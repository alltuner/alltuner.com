# All Tuner Labs

Hugo static site with Tailwind CSS v4. Supports 3 languages: en, ca, es.

## Logo Carousel

The homepage has a CSS-only scrolling logo carousel. To add a new logo:

1. Drop the SVG file into `static/statics/img/logos/`
2. Add an entry to `data/logos.yaml`:
   ```yaml
   - name: Company Name
     logo: filename.svg
     url: "https://example.com"
   ```

- `name`: used for the `alt` text on the image
- `logo`: filename inside `static/statics/img/logos/`
- `logoDark` (optional): dark mode variant filename. When provided, logos swap via `dark:hidden`/`hidden dark:block`. When absent, the light logo is shown in both modes with reduced opacity.
- `url`: where the logo links to

### Image guidelines

- **SVGs preferred** — scale perfectly, smallest file size.
- **PNGs**: export at 3x the rendered height for retina clarity. Logos render at `h-16` (64px CSS), so PNGs should be **192px tall** (width proportional to aspect ratio).
- **Trim whitespace** — ensure no extra padding around the logo so visual heights stay consistent across logos.
- **Single-color SVGs**: in Inkscape, set all fills to black (`#000000`), save as Plain SVG, then replace `fill="#000000"` (and any `style="fill:#000000"`) with `fill="currentColor"` in a text editor. The logo will automatically inherit the theme color (`raisin`/`raisin-dark`).

The carousel partial (`themes/alltuner-theme/layouts/partials/logo-carousel.html`) picks up the data automatically. The logo list is duplicated in HTML for seamless infinite scrolling — this is expected.
