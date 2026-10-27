import logging

from django.apps import AppConfig
from django.db.models.signals import post_save

logger = logging.getLogger(__name__)


class ToursConfig(AppConfig):
    name = 'tours'

    def ready(self):
        from tours.images import image_fields

        for model in self.get_models():
            if image_fields(model):
                post_save.connect(build_renditions_on_save, sender=model, dispatch_uid=f'renditions-{model.__name__}')


def build_renditions_on_save(sender, instance, **kwargs):
    """Process images when they're uploaded in the admin, so visitors never wait on it."""
    from tours import images

    for field in images.image_fields(sender):
        name = getattr(instance, field.name).name
        if not name:
            continue
        try:
            images.ensure(name)
        except Exception:
            # Never block a save; the template tag falls back to the original image.
            logger.exception('Could not build renditions for %s', name)
