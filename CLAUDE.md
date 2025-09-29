# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a static website template built with a modern frontend toolchain. Sites are deployed to GitHub Pages and use a simple HTML/CSS/JS structure with build tools for optimization.

## Development Commands

- `bun run dev` - Start development with parallel watching of CSS/JS and local server on port 8000
- `bun run build` - Full production build (CSS, JS, and static versioning)
- `bun run serve` - Serve the docs directory on localhost:8000

### Individual Build Commands

- `bun run build:css` - Build and minify CSS with Tailwind
- `bun run build:js` - Bundle and minify JavaScript with esbuild
- `bun run watch:css` - Watch CSS changes during development
- `bun run watch:js` - Watch JS changes during development

### Deployment

- `bun run version-statics` - Add content-based cache-busting versions to static files
- `bun run purge-cf` - Purge Cloudflare cache after deployment

## Architecture

The project follows a simple static site structure:

- **docs/**: Final output directory (served by GitHub Pages)
  - `index.html`: Main landing page
  - `statics/`: Contains versioned CSS and JS bundles
- **config/**: Build configuration and utilities
  - `esbuild.config.js`: JavaScript bundling with Lucide icons
  - `tailwind.config.css`: Tailwind CSS configuration
  - `version-statics.py`: Python script for cache-busting static assets
  - `purge-cf.py`: Cloudflare cache purging utility

### Asset Management

The build system automatically:

1. Bundles JS with esbuild (config/esbuild.config.js)
2. Compiles CSS with Tailwind CSS
3. Adds content-based version hashes to static files for cache busting
4. Updates HTML references to include version parameters

### Icon System

Uses Lucide icons via esbuild. To add icons:

1. Import needed icons in `config/esbuild.config.js`
2. Add them to the `createIcons()` configuration
3. Reference in HTML with `data-lucide="icon-name"`

Note: @lucide/lab icons require lowercase import names but uppercase variable names.

### Environment

- Uses `mise` for Python environment management
- Python dependencies installed via `uv` with auto-venv
- Node.js dependencies managed with Bun
