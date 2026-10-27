# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Django 6.1 site for a Maasai safari/tour operator (Kaelo Expeditions / "Offgrid Tour and Travel"). One project package (`maasai_adventures/`) and one app (`tours/`). The site is a CMS-like marketing site with content managed in Django admin, plus a souvenir shop: session cart, guest checkout, and M-Pesa STK Push payments.

## Commands

### Docker (primary)

```bash
cp .env.example .env                 # then set SECRET_KEY, POSTGRES_PASSWORD, etc.
docker compose up -d --build         # db (Postgres 17) + web (gunicorn) + nginx on http://localhost:${APP_PORT:-8080}
docker compose logs -f web
docker compose exec web python manage.py <command>   # e.g. createsuperuser, makemigrations
docker compose exec db psql -U offgrid -d offgrid
docker compose down                  # add -v to also wipe the database and media volumes
```

`docker/entrypoint.sh` runs `migrate`, `collectstatic` and `build_renditions` on every container start (turn them off with `DJANGO_MIGRATE=0` / `DJANGO_COLLECTSTATIC=0` / `DJANGO_BUILD_RENDITIONS=0`). It also creates a superuser if `DJANGO_SUPERUSER_*` is set. nginx serves `/static/` and `/media/` from shared volumes and proxies everything else to gunicorn. Postgres sits on an internal-only network and isn't published to the host. Compose builds `DATABASE_URL` from the `POSTGRES_*` variables.

### Local (without Docker)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
python manage.py makemigrations tours
python manage.py test tours
python manage.py test tours.tests.GenerateTests.test_exif_rotation_is_applied   # single test
python manage.py build_renditions    # resize any new/changed images (--force rebuilds all)
```

`SECRET_KEY` is required. Settings read it from `.env` at the repo root (gitignored) via `django-environ`. Other keys: `DEBUG`, `ALLOWED_HOSTS`, `SHOP_ENABLED`, `EMAIL_HOST_USER_PASSWORD`, `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_SHORTCODE`, `MPESA_PASSKEY`, `MPESA_CALLBACK_URL`, `MPESA_ENV`.

Database config comes from `DATABASE_URL` (via `env.db()`); when it's unset, it falls back to SQLite (`db.sqlite3`; listed in `.gitignore` but committed to the repo since the Oct 2026 data import, along with `media/`). `db.sqlite3.broken` and `db.sqlite3.corrupted` are committed leftovers and are not used.

### Production server (`ssh kaelo`, 169.58.189.181)

Live at http://169.58.189.181:8080. Docker isn't installed there yet (the `kaelo` user has no passwordless sudo), so it runs without root:

- `~/offgrid` holds the code, a `uv`-built Python 3.13 `venv`, SQLite `db.sqlite3`, `staticfiles/`, `media/`, and `.env` (production secrets, mode 600).
- systemd **user** units (lingering is on, so they start at boot): `offgrid-web` (gunicorn on 127.0.0.1:8000) and `offgrid-caddy` (`~/.local/bin/caddy` with `~/offgrid/Caddyfile` on :8080, serving `/static/` and `/media/` and proxying the rest, like the nginx config).

Deploy a change from the repo root:

```bash
rsync -az --exclude .git --exclude venv --exclude .env --exclude 'db.sqlite3*' --exclude __pycache__ \
  --exclude media/ --exclude staticfiles/ --exclude .DS_Store ./ kaelo:offgrid/
ssh kaelo 'cd offgrid && ~/.local/bin/uv pip install -q --python venv/bin/python -r requirements.txt \
  && venv/bin/python manage.py migrate --noinput && venv/bin/python manage.py collectstatic --noinput --clear -v 0 \
  && venv/bin/python manage.py build_renditions && systemctl --user restart offgrid-web'
rsync -az --exclude .DS_Store --exclude renditions/ media/ kaelo:offgrid/media/   # only when media/ changed in git; then rerun build_renditions
ssh kaelo 'journalctl --user -u offgrid-web -f'   # logs
```

To move to the Docker stack once Docker is installed: dump data with `manage.py dumpdata --natural-foreign --exclude contenttypes --exclude auth.permission`, stop and disable both user units, set `APP_PORT=80` and `CSRF_TRUSTED_ORIGINS=http://169.58.189.181` in `.env`, remove the `STATIC_ROOT`/`MEDIA_ROOT` lines, run `docker compose up -d --build`, then `loaddata` and copy `media/` into the `media_files` volume.

## Architecture

- **Content models** (`HeroSlide`, `WhatWeDoContent`, `Experience`, `PageHeader`, `TeamMember`, `ExpeditionPhoto`, `BlogHeader`, `BlogPost`) are edited through `tours/admin.py` and rendered by function-based views in `tours/views.py`. Blog content uses `django_ckeditor_5` (config is in `CKEDITOR_5_CONFIGS` in settings). Uploaded media goes to `MEDIA_ROOT`. Django serves it only when `DEBUG` is on; in Docker, nginx serves it.
- **Images** (`tours/images.py`): uploaded originals are never served directly. Each one gets resized WebP + JPEG copies (PNG if it has transparency) at 320–1920px in `media/renditions/v1/` (gitignored), with EXIF/GPS stripped and a `manifest.json`. A `post_save` signal (`tours/apps.py`) builds them on upload; `manage.py build_renditions` backfills. Templates render images with `{% load responsive_images %}{% responsive_image field sizes="..." alt=... %}`, which outputs a `<picture>` with srcsets and width/height (it falls back to the original if processing fails). Give `sizes` the image's real display width so phones download small files. Rendition URLs carry `?v=<hash>`, so Caddy/nginx cache `/media/renditions/` for a year. Bump `VERSION` in `images.py` when changing encoder settings.
- **Templates** are in `tours/templates/tours/`. They all extend `base.html` and use `django_bootstrap5`. The `tours.context_processors.cart_context` processor puts `cart` and `cart_item_count` into every template.
- **Shop switch**: `SHOP_ENABLED` (env, default `False`) gates the shop. When off, the `@shop_view` views (shop, product, cart, checkout) return 404, the navbar hides Shop/Cart (`shop_enabled` comes from the context processor), and order tracking, payment status, retry and the M-Pesa callback keep working for existing orders.
- **Navigation**: home-page sections (`#our-story`, `#our-experiences`) must be linked as `{% url 'index' %}#...`, never a bare `#...`, or they break on other pages. Contact is `#contact` because most pages include `tours/contact.html`; a page that doesn't must override `{% block contact_href %}{% url 'index' %}#contact{% endblock %}`. A script at the end of `base.html` redirects stale fragments (e.g. `/expedition-gallery/#our-experience`) to the home section; add old aliases to `HOME_SECTIONS` there. The home page uses Bootstrap ScrollSpy (`body_attrs` block) for the active nav state.
- **Cart** (`tours/cart.py`): stored in the session under `settings.CART_SESSION_ID`. Keys are `"{product_id}_{variant_id or 'None'}"`. Prices are saved as strings when an item is added (a variant's `get_price_usd()`, otherwise `product.price_usd`). Iterating the cart reloads products from the database and silently removes any that were deleted.
- **Checkout** (`guest_checkout` in views): creates an `Order` with `payment_status='pending'`, creates `OrderItem`s, decrements variant stock (or product stock if there's no variant), and emails a tracking link. When M-Pesa is chosen, it converts USD to KES at a hardcoded rate of 130 and calls `trigger_stk_push`. Customers track orders by `Order.tracking_token` (a UUID), since there are no customer accounts.
- **M-Pesa** (`tours/mpesa.py`): uses the Safaricom Daraja OAuth and STK Push APIs. The `mpesa_callback` view (csrf-exempt) marks an order as paid or failed using `CheckoutRequestID`. The frontend polls `check_payment_status` for updates, and `retry_mpesa_payment` sends a new STK push.
- **Safari inquiries** (`safari_inquiry_view`): saves a `SafariInquiry` and emails kaeloexpeditions@gmail.com over Gmail SMTP.
- `super-admin/upload/` is a superuser-only custom upload page (`admin_upload_image`).

## Known inconsistencies (check before relying on behavior)

- Settings define `MPESA_ENV`, but `mpesa.py` reads `MPESA_ENVIRONMENT` (and checks for `'live'`), so it always uses the sandbox endpoints. `MPESA_TRANSACTION_TYPE` and `MPESA_TILL_NUMBER` are read but never defined in settings.
- `tours/models.py` defines `class Order` twice. The second definition is the real one.
- `format_phone_number` is duplicated in `views.py` and `mpesa.py`.
- The order confirmation email is sent from the placeholder `shop@yourdomain.com`.
