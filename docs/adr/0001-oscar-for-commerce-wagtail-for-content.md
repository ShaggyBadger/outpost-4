# Oscar for Commerce, Wagtail for Content

**Status:** Accepted

Use Oscar 4.2 as the source of truth for products, variants, stock, and orders;
keep Wagtail as the source of truth for public pages and editorial content. This
fits the need to manage batch quantities, one-off stock, guest orders, custom
work, and in-person sales without maintaining duplicate product prices or stock
in two systems.

## Considered options

- Keep growing the custom Wagtail-based commerce models and checkout.
- Use Oscar for commerce and Wagtail for editorial pages.

## Consequences

- The project has a split shop/content administration experience.
- Oscar 4.2's standard dashboard has no manual order-creation route. In-person
  sales and accepted custom orders therefore need a focused custom Oscar
  workflow.
- Creating and sending Stripe invoices from Oscar also requires custom
  integration; Stripe's invoice API supports the invoice lifecycle, but Oscar's
  payment app documents payment records and no payment views.
- Build the storefront with payments disabled. Add Stripe-hosted Checkout,
  invoice handling, and verified webhooks in a later phase; embedded Checkout
  can follow without changing the commerce source of truth.
- Oscar 4.2 release metadata supports Django 6 and Python 3.14. The exact
  Django 6.0.9/Wagtail 8.0.1 stack passes the local Docker system check and test
  suite; repeat this validation on dependency upgrades.
- Imported Etsy listings remain unpublished with zero available stock until
  Leah confirms each product's current details and inventory.

## Evidence

- [Oscar 4.2 release notes](https://github.com/django-oscar/django-oscar/releases/tag/4.2)
- [Oscar catalog modeling](https://django-oscar.readthedocs.io/en/latest/topics/modelling_your_catalogue.html)
- [Oscar dashboard overview](https://django-oscar.readthedocs.io/en/latest/ref/apps/dashboard.html)
- [Oscar 4.2 order-dashboard routes](https://github.com/django-oscar/django-oscar/blob/4.2/src/oscar/apps/dashboard/orders/apps.py)
- [Oscar payment app](https://django-oscar.readthedocs.io/en/latest/ref/apps/payment.html)
- [Stripe-hosted Checkout](https://docs.stripe.com/checkout/quickstart)
- [Stripe invoice creation](https://docs.stripe.com/api/invoices/create)
- [Stripe Checkout fulfillment and webhooks](https://docs.stripe.com/checkout/fulfillment)
