#!/bin/sh
# Container entrypoint: prepare the app, then hand off to the CMD (gunicorn by default).
set -e

if [ "${DJANGO_MIGRATE:-1}" = "1" ]; then
    echo "→ Applying database migrations"
    python manage.py migrate --noinput
fi

if [ "${DJANGO_COLLECTSTATIC:-1}" = "1" ]; then
    echo "→ Collecting static files"
    python manage.py collectstatic --noinput --clear -v 0
fi

# Optionally bootstrap an admin account (idempotent).
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
u = os.environ['DJANGO_SUPERUSER_USERNAME']
if not User.objects.filter(username=u).exists():
    User.objects.create_superuser(u, os.environ.get('DJANGO_SUPERUSER_EMAIL', ''), os.environ['DJANGO_SUPERUSER_PASSWORD'])
    print(f'→ Created superuser {u}')
"
fi

exec "$@"
