# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a static website template built with a modern frontend toolchain. Sites are deployed to GitHub Pages via automated GitHub Actions and use a simple HTML/CSS/JS structure with build tools for optimization.

## Development Commands

- `just dev` or `bun run dev` - Start development with parallel watching of CSS/JS and local server on port 8000
- `just build` or `bun run build` - Full production build (CSS, JS, and static versioning)
- `just serve` or `bun run serve` - Serve the docs directory on localhost:8000

### Individual Build Commands

- `bun run build:css` - Build and minify CSS with Tailwind, then hash the filename
- `bun run build:js` - Bundle and minify JavaScript with Bun's bundler (with content hash in filename)
- `bun run dev:css` - Watch CSS changes during development (fixed filename)
- `bun run dev:js` - Watch JS changes during development (fixed filename with sourcemap)

### Deployment

- **Automated**: Push to `main` branch triggers GitHub Actions workflow that builds and deploys
- `just purge-cf` or `bun run purge-cf` - Purge Cloudflare cache after deployment (optional, for HTML caching)
- `just update-scaffolding` - Update project from copier template

## Architecture

The project follows a simple static site structure:

- **docs/**: Final output directory (served by GitHub Pages)
  - `index.html`: Main landing page
  - `statics/`: Contains versioned CSS and JS bundles
- **config/**: Build configuration and utilities
  - `config.js`: JavaScript bundling entry that registers Lucide icons
  - `config.css`: Tailwind CSS configuration
  - `hash-css.ts`: Bun script to hash CSS filename after Tailwind build
  - `version-statics.ts`: Bun script to update HTML references to hashed bundle files
  - `purge-cf.py`: Cloudflare cache purging utility (optional)
  - `serve.py`: Development server with livereload and cache-control headers

### Asset Management & Cache Busting

The build system uses different strategies for development and production:

**Development Mode:**
- Fixed filenames: `bundle.js`, `bundle.css`
- Cache-Control headers prevent browser caching (`no-cache, no-store, must-revalidate`)
- Livereload triggers browser refresh on file changes
- Sourcemaps enabled for debugging

**Production Mode:**
- Content-hashed filenames: `bundle.{hash}.js`, `bundle.{hash}.css`
- Bun automatically hashes JS files during build
- `hash-css.ts` computes SHA-256 hash and renames CSS file after Tailwind build
- `version-statics.ts` updates HTML to reference correct hashed filenames
- GitHub Actions builds and deploys automatically on push to `main`

### Build Process

1. **CSS Build**: Tailwind compiles → `bundle.css` → `hash-css.ts` renames to `bundle.{hash}.css`
2. **JS Build**: Bun bundles with `--entry-naming='bundle.[hash].[ext]'` → `bundle.{hash}.js`
3. **Versioning**: `version-statics.ts` scans for hashed bundles and updates HTML `<script>` and `<link>` tags
4. **Result**: HTML references exact hashed filenames, perfect cache busting

### Icon System

Uses Lucide icons via Bun's bundler. To add icons:

1. Import needed icons in `config/config.js`
2. Add them to the `createIcons()` configuration
3. Reference in HTML with `data-lucide="icon-name"`

Note: @lucide/lab icons require lowercase import names but uppercase variable names.

### Environment

- Uses `mise` for Python environment management (only for dev server)
- Python dependencies installed via `uv` with auto-venv
- Node.js dependencies managed with Bun
- Build process is Bun-only (no Python required for production builds)

### GitHub Actions Deployment

The `.github/workflows/deploy.yml` workflow:
- Triggers on push to `main` or manual dispatch
- Installs Bun and dependencies
- Runs `bun run build` (CSS + JS + versioning)
- Uploads `docs/` folder as Pages artifact
- Deploys to GitHub Pages

No Python/UV needed in CI/CD - pure Bun workflow!
