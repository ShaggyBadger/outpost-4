# Grannycoded Color Palette

Palette based on `grannycoded_logo.jpg`. The logo's main colors are near-black,
muted olive, and antique gold. Warm linen is a complementary site background
color chosen to keep the shop light and product photography prominent.

| Name | Hex | Recommended use |
| --- | --- | --- |
| Ink | `#0B0B09` | Text, footer, and dark details |
| Granny olive | `#464E29` | Primary brand color, buttons, and links |
| Moss | `#68683A` | Secondary accents and borders |
| Antique gold | `#C0A070` | Small highlights and decorative details |
| Warm linen | `#F4EBDD` | Default page background and light surfaces |

## Usage notes

- Use warm linen as the main background and ink for readable text.
- Use granny olive for primary actions and links.
- Use antique gold sparingly as an accent; do not rely on it alone for text or
  important controls.
- Check contrast and keyboard focus states when implementing the palette.
- Treat these as design tokens so they can be adjusted consistently later.

## In Django and Tailwind

The shared Tailwind theme in `backend/static-src/css/input.css` exposes these
tokens as classes such as `bg-brand-linen`, `text-brand-olive`, and
`border-brand-moss`. The base page already uses linen and ink. The logo is
available to Django templates at `{% static 'images/grannycoded_logo.avif' %}`;
it is AVIF data, despite the `.jpg` extension on the supplied original file.
