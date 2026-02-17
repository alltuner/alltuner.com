# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Hugo-based static website with multilingual support (English, Catalan, Spanish). It is deployed to GitHub Pages via automated GitHub Actions. The theme lives in-repo at `themes/alltuner-theme/`.

## Development Commands

- `just dev` or `bun run dev` - Start Hugo dev server with parallel CSS/JS watching
- `just build` or `bun run build` - Full production build (assets + Hugo)
- `just clean` or `bun run clean` - Remove `public/` build output
- `just serve` or `bun run serve` - Run Hugo dev server only

### Individual Build Commands

- `bun run css:build` - Build and minify CSS with Tailwind CLI
- `bun run css:watch` - Watch CSS changes during development
- `bun run js:build` - Bundle and minify JavaScript with Bun
- `bun run js:watch` - Watch JS changes during development
- `bun run fonts` - Copy font files from node_modules to `static/fonts/`
- `bun run assets` - Build all assets in parallel (fonts + CSS + JS)

### Deployment

- **Automated**: Push to `main` branch triggers GitHub Actions workflow that builds and deploys
- `just purge-cf` or `bun run purge-cf` - Purge Cloudflare cache after deployment (optional)
- `just update-scaffolding` - Update project from copier template

## Architecture

### Hugo Structure

- **`hugo.toml`**: Main configuration with i18n settings and site params
- **`content/`**: Markdown content files
  - `_index.md`: English homepage (default language, served at `/`)
  - `ca/_index.md`: Catalan homepage (served at `/ca/`)
  - `es/_index.md`: Spanish homepage (served at `/es/`)
- **`themes/alltuner-theme/`**: In-repo Hugo theme
  - `layouts/_default/baseof.html`: Base template with head, body chrome, footer
  - `layouts/index.html`: Homepage template
  - `layouts/partials/icons/`: Inline SVG icon partials
  - `layouts/robots.txt`: Dynamic robots.txt template
  - `i18n/`: Translation files (en, ca, es)
  - `css/theme.css`: Font-face declarations and custom utilities
  - `js/main.js`: Minimal JS (instant.page prefetching)
- **`css/input.css`**: Tailwind CSS entry point with theme imports
- **`static/`**: Static assets copied directly to output
  - `CNAME`: GitHub Pages custom domain
  - `statics/img/`: Logo, favicon, OG image, product logos
  - `fonts/`: Woff2 font files (copied from node_modules during build)
- **`assets/`**: Built CSS/JS consumed by Hugo's `resources.Get`
- **`public/`**: Hugo build output (deployed to GitHub Pages)

### Build Process

1. **Fonts**: Copy woff2 files from `node_modules/` to `static/fonts/`
2. **CSS Build**: Tailwind CLI compiles `css/input.css` → `assets/css/style.css`
3. **JS Build**: Bun bundles `themes/alltuner-theme/js/main.js` → `assets/js/main.js`
4. **Hugo Build**: Hugo reads assets via `resources.Get`, appends MD5 query string for cache busting
5. **Result**: `public/` contains the complete site ready for deployment

### Icon System

Uses inline SVG partials instead of a JS icon library. Icons live in `themes/alltuner-theme/layouts/partials/icons/`. To add a new icon:

1. Create `themes/alltuner-theme/layouts/partials/icons/{name}.html` with inline SVG
2. Add a case to `themes/alltuner-theme/layouts/partials/icons/social-icon.html`

### i18n / Multilingual

- Default language: English (served at root `/`)
- Catalan: served at `/ca/`
- Spanish: served at `/es/`
- UI strings: `themes/alltuner-theme/i18n/{lang}.toml`
- Content strings: frontmatter in `content/{lang}/_index.md`
- hreflang alternates configured in `hugo.toml` `[params.alternates]`

### GitHub Actions Deployment

The `.github/workflows/deploy.yml` workflow:
- Triggers on push to `main` or manual dispatch
- Sets up Bun and Hugo
- Runs `bun run assets` (fonts + CSS + JS) then `hugo`
- Uploads `public/` folder as Pages artifact
- Deploys to GitHub Pages
