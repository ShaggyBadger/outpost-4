# Backend

The Django/Wagtail site, Oscar shop, and Tailwind pipeline for the server-rendered
UI live here.

- `config/` contains project settings, URL routing, and ASGI/WSGI entry points.
- Wagtail manages editorial pages and blog content; Oscar manages products,
  stock, baskets, and orders.
- Oscar's dashboard is at `/dashboard/`; Wagtail admin is at `/admin/`; Jazzmin
  themes Django admin at `/django-admin/`.
- Oscar's catalogue is at `/shop/` and basket at `/basket/`. Checkout remains
  disabled until the later Stripe integration and launch gates are complete.
- Custom-order requests are saved from `/custom-order/`; staff can review them
  and record fair sales through Oscar-linked tools at `/dashboard/custom-orders/`
  and `/dashboard/record-sale/`.
- Each Django app owns its models, migrations, and app-specific templates.
- `templates/` contains shared Django templates; `static-src/` contains Tailwind
  input, and `static/` receives generated assets.
- `requirements.txt` and the npm manifests pin the backend and Tailwind tools.

Run project commands from the repository root through Compose, for example:

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py test
docker compose exec tailwind npm run build:css
```
