# ABOUTME: Task runner for the site. `just site` builds it into public/;
# ABOUTME: `just dev` serves it locally with live reload.

site:
    bun install --frozen-lockfile
    bun run assets
    bunx hugo

dev:
    bun install
    bun run dev
