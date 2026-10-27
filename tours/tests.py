import io
import json
import os
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from tours import images
from tours.models import ExpeditionPhoto, Order, Product, TeamMember


def make_image(size=(4000, 3000), mode='RGB', fmt='JPEG', orientation=None):
    im = Image.new(mode, size, (200, 120, 40, 128) if mode == 'RGBA' else (200, 120, 40))
    exif = Image.Exif()
    if orientation:
        exif[0x0112] = orientation
    exif[0x8825] = {2: (1.0, 2.0, 3.0)}  # GPS info that must not leak into renditions
    buf = io.BytesIO()
    im.save(buf, fmt, exif=exif.tobytes())
    return buf.getvalue()


class MediaTestCase(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media)
        override = override_settings(MEDIA_ROOT=self.media, MEDIA_URL='/media/')
        override.enable()
        self.addCleanup(override.disable)

    def put(self, name, data):
        path = os.path.join(self.media, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as fh:
            fh.write(data)
        return name

    def rendition(self, name, filename):
        return os.path.join(self.media, images.ROOT, name, filename)


class GenerateTests(MediaTestCase):
    def test_large_photo_gets_every_width_in_webp_and_jpeg(self):
        name = self.put('hero_slides/a.jpg', make_image())
        manifest = images.generate(name)

        self.assertEqual(manifest['widths'], list(images.WIDTHS))
        self.assertEqual((manifest['width'], manifest['height']), (1920, 1440))
        for w in images.WIDTHS:
            for ext in ('webp', 'jpg'):
                with Image.open(self.rendition(name, f'{w}.{ext}')) as im:
                    self.assertEqual(im.width, w)
                    self.assertNotIn('exif', im.info)

    def test_exif_rotation_is_applied(self):
        name = self.put('team/portrait.jpg', make_image(size=(3000, 2000), orientation=6))
        manifest = images.generate(name)

        self.assertEqual((manifest['width'], manifest['height']), (1920, 2880))
        with Image.open(self.rendition(name, '1920.jpg')) as im:
            self.assertEqual(im.size, (1920, 2880))

    def test_small_images_are_not_upscaled(self):
        name = self.put('variants/small.jpg', make_image(size=(500, 400)))
        self.assertEqual(images.generate(name)['widths'], [320, 500])

    def test_transparent_png_falls_back_to_png(self):
        name = self.put('team/logo.png', make_image(size=(800, 800), mode='RGBA', fmt='PNG'))
        manifest = images.generate(name)

        self.assertEqual(manifest['fallback'], 'png')
        with Image.open(self.rendition(name, '800.webp')) as im:
            self.assertEqual(im.mode, 'RGBA')

    def test_ensure_rebuilds_only_when_the_source_changes(self):
        name = self.put('team/a.jpg', make_image(size=(1000, 800)))
        self.assertTrue(images.ensure(name))
        self.assertFalse(images.ensure(name))

        self.put(name, make_image(size=(1200, 800)))
        os.utime(os.path.join(self.media, name), (1, 1))
        self.assertTrue(images.ensure(name))
        with open(self.rendition(name, 'manifest.json')) as fh:
            self.assertEqual(json.load(fh)['width'], 1200)


class TemplateTagTests(MediaTestCase):
    def render(self, field, extra=''):
        template = Template('{% load responsive_images %}{% responsive_image field sizes="50vw" alt="A lion" ' + extra + ' %}')
        return template.render(Context({'field': field}))

    def test_renders_picture_with_srcsets_and_dimensions(self):
        member = TeamMember.objects.create(
            name='Gab', role='Guide', bio='-',
            image=SimpleUploadedFile('gab.jpg', make_image(size=(2400, 1600)), content_type='image/jpeg'),
        )
        html = self.render(member.image, 'class="w-100" fetchpriority="high"')

        self.assertIn('<picture class="ri"><source type="image/webp"', html)
        self.assertIn('640.webp?v=', html)
        self.assertIn('1920.jpg?v=', html)
        self.assertIn('sizes="50vw"', html)
        self.assertIn('width="1920"', html)
        self.assertIn('height="1280"', html)
        self.assertIn('fetchpriority="high"', html)
        self.assertIn('alt="A lion"', html)

    def test_unreadable_file_falls_back_to_original(self):
        member = TeamMember(name='X', role='-', bio='-', image='team/missing.jpg')
        html = self.render(member.image)
        self.assertIn('src="/media/team/missing.jpg"', html)
        self.assertNotIn('<picture', html)

    def test_empty_field_renders_nothing(self):
        self.assertEqual(self.render(TeamMember().image).strip(), '')


class IntegrationTests(MediaTestCase):
    def test_upload_builds_renditions_on_save(self):
        member = TeamMember.objects.create(
            name='Gab', role='Guide', bio='-',
            image=SimpleUploadedFile('gab.jpg', make_image(size=(1000, 1000)), content_type='image/jpeg'),
        )
        self.assertTrue(os.path.exists(self.rendition(member.image.name, 'manifest.json')))

    def test_build_renditions_command(self):
        name = self.put('expeditions/p.jpg', make_image(size=(1000, 700)))
        ExpeditionPhoto.objects.bulk_create([ExpeditionPhoto(image=name, thumb=name)])  # bypasses the signal
        out = io.StringIO()
        call_command('build_renditions', stdout=out)
        self.assertIn('1 built', out.getvalue())

    def test_gallery_serves_renditions_and_lightbox_sources(self):
        name = self.put('expeditions/p.jpg', make_image(size=(3000, 2000)))
        ExpeditionPhoto.objects.create(image=name)
        response = self.client.get(reverse('expedition_gallery'))

        self.assertContains(response, 'data-full-webp=')
        self.assertContains(response, '1920.jpg?v=')
        self.assertNotContains(response, 'src="/media/expeditions/p.jpg"')


class NavigationTests(TestCase):
    def test_home_section_links_work_from_any_page(self):
        response = self.client.get(reverse('expedition_gallery'))
        self.assertContains(response, 'href="/#our-story"')
        self.assertContains(response, 'href="/#our-experiences"')
        self.assertNotContains(response, 'href="#our-')

    def test_contact_scrolls_on_pages_that_have_the_form(self):
        response = self.client.get(reverse('expedition_gallery'))
        self.assertContains(response, 'href="#contact"')
        self.assertContains(response, '<section id="contact"')

    def test_contact_points_home_on_pages_without_the_form(self):
        response = self.client.get('/no-such-page/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'href="/#contact"', status_code=404)
        self.assertNotContains(response, 'href="#contact"', status_code=404)

    def test_home_page_has_no_dead_links_and_spies_on_sections(self):
        response = self.client.get(reverse('index'))
        self.assertNotContains(response, 'href="#"')
        self.assertContains(response, 'data-bs-spy="scroll"')
        for section in ('our-story', 'our-experiences', 'contact'):
            self.assertContains(response, f'id="{section}"')


SHOP_URLS = [
    ('shop_list', []), ('product_detail', [1]), ('cart_detail', []), ('cart_add', [1]),
    ('cart_remove', [1]), ('cart_update', [1]), ('guest_checkout', []),
]


@override_settings(SHOP_ENABLED=False)
class ShopDisabledTests(TestCase):
    def test_shop_pages_return_404(self):
        for name, args in SHOP_URLS:
            with self.subTest(name):
                self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 404)
                self.assertEqual(self.client.post(reverse(name, args=args)).status_code, 404)

    def test_shop_and_cart_hidden_from_navigation(self):
        response = self.client.get(reverse('index'))
        self.assertNotContains(response, f'href="{reverse("shop_list")}"')
        self.assertNotContains(response, f'href="{reverse("cart_detail")}"')

    def test_existing_orders_can_still_be_tracked(self):
        order = Order.objects.create(email='a@b.co', phone='0700000000', full_name='A', total_amount=5)
        response = self.client.get(reverse('guest_order_tracking', args=[order.tracking_token]))
        self.assertContains(response, 'Back to Home')
        self.assertNotContains(response, f'href="{reverse("shop_list")}"')


@override_settings(SHOP_ENABLED=True)
class ShopEnabledTests(TestCase):
    def test_shop_is_listed_and_reachable(self):
        product = Product.objects.create(name='Zebra', price_usd=5, price_kes=650)
        self.assertContains(self.client.get(reverse('index')), f'href="{reverse("shop_list")}"')
        self.assertContains(self.client.get(reverse('shop_list')), 'Zebra')
        self.assertEqual(self.client.get(reverse('product_detail', args=[product.id])).status_code, 200)
