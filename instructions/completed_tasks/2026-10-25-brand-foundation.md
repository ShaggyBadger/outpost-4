# Brand Foundation — Completed 2026-10-25

## Completion summary

Added reusable Tailwind brand tokens, applied linen/ink/olive to the site shell
and home template, and stored an AVIF-named copy of the supplied logo under
Django static assets. The original source image remains unchanged.

- Key files: `BRAND_COLORS.md`, `backend/static-src/css/input.css`,
  `backend/static/images/grannycoded_logo.avif`, and shared/home templates.
- Checks: Django system check, Tailwind production CSS build, static asset lookup,
  and source/copy SHA-256 comparison all passed.
- Follow-up: use the static logo URL and tokens as the storefront is designed;
  upload the logo to the site's Linode bucket when that bucket is ready.

---

## Goal

Preserve Grannycoded's supplied palette and logo in reusable, Django-served
locations without replacing the original source files.

## Relevant files

- `BRAND_COLORS.md` and `grannycoded_logo.jpg`: supplied source assets.
- `backend/static-src/css/input.css`: shared Tailwind design tokens.
- `backend/static/images/grannycoded_logo.avif`: accurately named static logo.
- `backend/templates/base.html` and the home template: initial token usage.

## Steps

1. Add the palette as Tailwind theme tokens and use it for site defaults.
2. Copy the logo into Django static assets with its actual AVIF extension.
3. Document token names and the static logo path.

## Verification performed

- Confirmed the source logo remains unchanged and the static copy is valid AVIF.
- Built Tailwind CSS and ran Django's system check inside Compose.
- Confirmed Django discovers the static logo and source/copy hashes match.
