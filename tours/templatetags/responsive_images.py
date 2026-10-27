from django import template
from django.utils.html import format_html, format_html_join

from tours import images

register = template.Library()


@register.simple_tag
def responsive_image(field, sizes='100vw', alt='', loading='lazy', **attrs):
    """Render an ImageField as a <picture> with WebP and JPEG/PNG srcsets.

    `sizes` should describe how wide the image is displayed, so phones download
    a small file. Extra keyword arguments become <img> attributes (underscores
    become hyphens, e.g. fetchpriority="high", data_full="...").

        {% responsive_image member.image sizes="(min-width: 768px) 40vw, 100vw" alt=member.name class="img-fluid" %}
    """
    if not field:
        return ''
    attrs = {key.replace('_', '-'): value for key, value in attrs.items() if value is not None}
    attrs.update(alt=alt, loading=loading, decoding='async')
    r = images.renditions(field.name)
    if r is None:
        attrs['src'] = field.url
        return format_html('<img {}>', _attrs(attrs))

    attrs.update(src=r['src'], srcset=r['fallback_srcset'], sizes=sizes, width=r['width'], height=r['height'])
    return format_html(
        '<picture class="ri"><source type="image/webp" srcset="{}" sizes="{}"><img {}></picture>',
        r['webp_srcset'], sizes, _attrs(attrs),
    )


@register.simple_tag
def image_renditions(field):
    """Srcsets for hand-written markup, e.g. lightboxes: {% image_renditions photo.image as r %}."""
    if not field:
        return None
    return images.renditions(field.name) or {
        'webp_srcset': '', 'fallback_srcset': '', 'fallback_type': '',
        'src': field.url, 'large': field.url, 'width': '', 'height': '',
    }


def _attrs(attrs):
    return format_html_join(' ', '{}="{}"', sorted(attrs.items()))
