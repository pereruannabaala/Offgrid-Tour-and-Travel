"""Web-optimised, responsive renditions of uploaded images.

Originals in MEDIA_ROOT are never modified. For each one we write resized
copies to MEDIA_ROOT/renditions/<VERSION>/<original path>/ in WebP plus a
universally supported fallback (JPEG, or PNG for images with transparency),
and a manifest.json that templates read to build <picture> srcsets.

Renditions are stripped of metadata (camera EXIF, GPS), rotated per their
EXIF orientation, and cache-busted with a hash of the source file so they
can be served with a long-lived immutable Cache-Control header.
"""
import hashlib
import json
import logging
import os
import tempfile

from django.core.files.storage import default_storage
from django.db import models
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Bump when the encoding settings below change, so every image is regenerated
# under new URLs instead of browsers keeping stale cached copies.
VERSION = 'v1'
ROOT = f'renditions/{VERSION}'
WIDTHS = (320, 640, 960, 1280, 1920)
WEBP_QUALITY = 76
JPEG_QUALITY = 78

Image.MAX_IMAGE_PIXELS = 120_000_000  # drone/DSLR panoramas, still guards against decompression bombs


def image_fields(model):
    return [f for f in model._meta.get_fields() if isinstance(f, models.ImageField)]


def _dir(name):
    """'team/Gab.jpeg' -> 'renditions/v1/team/Gab.jpeg'."""
    return f'{ROOT}/{name}'


def _path(rel):
    return default_storage.path(rel)


def _source_stat(name):
    st = os.stat(_path(name))
    return st.st_size, int(st.st_mtime)


def _read_manifest(name):
    try:
        with open(_path(f'{_dir(name)}/manifest.json')) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _atomic_write(rel, write, mode='wb'):
    """Write via a temp file and rename, so concurrent workers never serve a half-written file."""
    dest = _path(rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(dest), suffix='.part')
    try:
        with os.fdopen(fd, mode) as fh:
            write(fh)
        os.chmod(tmp, 0o644)
        os.replace(tmp, dest)
    except BaseException:
        os.unlink(tmp)
        raise


def _save_image(image, rel, **params):
    _atomic_write(rel, lambda fh: image.save(fh, **params))


def _hash_file(path):
    digest = hashlib.sha1()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()[:10]


def generate(name):
    """Build every rendition of the stored file `name` and return its manifest."""
    source = _path(name)
    size, mtime = _source_stat(name)

    with Image.open(source) as im:
        # Keep the colour profile (wide-gamut camera shots), except for CMYK, which we convert to RGB.
        icc_profile = None if im.mode == 'CMYK' else im.info.get('icc_profile')
        has_alpha = im.mode in ('RGBA', 'LA', 'PA') or (im.mode == 'P' and 'transparency' in im.info)
        # Display size of the original, after EXIF rotation (orientations 5-8 swap the axes).
        orig_w, orig_h = im.size[::-1] if im.getexif().get(0x0112, 1) in (5, 6, 7, 8) else im.size

        # Let the JPEG decoder downscale by up to 8x while decoding: far faster
        # and lighter on memory than decoding a 24MP photo at full size.
        scale = WIDTHS[-1] / max(im.size)
        if scale < 1:
            im.draft('RGB', (int(im.width * scale) + 1, int(im.height * scale) + 1))

        im = ImageOps.exif_transpose(im)
        im = im.convert('RGBA' if has_alpha else 'RGB')

        widths = sorted({w for w in WIDTHS if w < orig_w} | {min(orig_w, WIDTHS[-1])})
        fallback = 'png' if has_alpha else 'jpg'

        for w in widths:
            h = max(1, round(orig_h * w / orig_w))
            resized = im if im.size == (w, h) else im.resize((w, h), Image.Resampling.LANCZOS, reducing_gap=3.0)
            _save_image(resized, f'{_dir(name)}/{w}.webp', format='WEBP',
                        quality=WEBP_QUALITY, method=6, icc_profile=icc_profile)
            if fallback == 'png':
                _save_image(resized, f'{_dir(name)}/{w}.png', format='PNG', optimize=True, icc_profile=icc_profile)
            else:
                _save_image(resized, f'{_dir(name)}/{w}.jpg', format='JPEG', quality=JPEG_QUALITY,
                            optimize=True, progressive=True, subsampling='4:2:0', icc_profile=icc_profile)

    manifest = {
        'width': min(orig_w, WIDTHS[-1]),
        'height': round(orig_h * min(orig_w, WIDTHS[-1]) / orig_w),
        'widths': widths,
        'fallback': fallback,
        'hash': _hash_file(source),
        'source_size': size,
        'source_mtime': mtime,
    }
    _atomic_write(f'{_dir(name)}/manifest.json', lambda fh: json.dump(manifest, fh), mode='w')
    return manifest


def is_stale(name):
    manifest = _read_manifest(name)
    if manifest is None:
        return True
    return (manifest['source_size'], manifest['source_mtime']) != _source_stat(name)


def ensure(name, force=False):
    """Generate renditions if they are missing or the source file changed. Returns True if work was done."""
    if force or is_stale(name):
        generate(name)
        return True
    return False


def renditions(name):
    """Srcsets and dimensions for templates, or None if the image can't be processed.

    Generates on first use as a fallback; normally the post_save signal or the
    build_renditions command has already done it.
    """
    if not name:
        return None
    manifest = _read_manifest(name)
    if manifest is None:
        try:
            manifest = generate(name)
        except FileNotFoundError:
            logger.warning('Image file missing: %s', name)
            return None
        except Exception:
            logger.exception('Could not build renditions for %s', name)
            return None

    def url(w, ext):
        return f"{default_storage.url(f'{_dir(name)}/{w}.{ext}')}?v={manifest['hash']}"

    widths, fallback = manifest['widths'], manifest['fallback']
    return {
        'webp_srcset': ', '.join(f'{url(w, "webp")} {w}w' for w in widths),
        'fallback_srcset': ', '.join(f'{url(w, fallback)} {w}w' for w in widths),
        'fallback_type': 'image/png' if fallback == 'png' else 'image/jpeg',
        # Plain src for browsers without srcset support: a mid-size rendition.
        'src': url(min(widths, key=lambda w: abs(w - 960)), fallback),
        'large': url(widths[-1], fallback),
        'width': manifest['width'],
        'height': manifest['height'],
    }
