import time

from django.apps import apps
from django.core.management.base import BaseCommand

from tours import images


class Command(BaseCommand):
    help = 'Generate web-optimised renditions for every image referenced by the tours models.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Rebuild even if renditions are up to date.')

    def handle(self, *args, force=False, **options):
        names = set()
        for model in apps.get_app_config('tours').get_models():
            fields = images.image_fields(model)
            if not fields:
                continue
            for row in model.objects.values_list(*(f.name for f in fields)):
                names.update(name for name in row if name)

        built = skipped = failed = 0
        started = time.monotonic()
        for name in sorted(names):
            try:
                if images.ensure(name, force=force):
                    built += 1
                    self.stdout.write(f'  built   {name}')
                else:
                    skipped += 1
            except FileNotFoundError:
                failed += 1
                self.stderr.write(f'  missing {name}')
            except Exception as exc:
                failed += 1
                self.stderr.write(f'  failed  {name}: {exc}')

        self.stdout.write(self.style.SUCCESS(
            f'{built} built, {skipped} up to date, {failed} failed in {time.monotonic() - started:.1f}s'
        ))
