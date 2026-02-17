# List available commands
default:
    @just --list

# Start local development server with watch mode
[group('Local Development')]
dev:
    @echo "Starting development server..."
    @bun run dev

# Build production site
[group('Build')]
build:
    @echo "Building production site..."
    @bun run build

# Clean build output
[group('Build')]
clean:
    @echo "Cleaning build output..."
    @bun run clean

# Serve the site locally with Hugo
[group('Local Development')]
serve:
    @echo "Serving site..."
    @bun run serve

# Purge Cloudflare cache (requires CLOUDFLARE_ZONE_ID and CLOUDFLARE_API_TOKEN)
[group('Deploy')]
purge-cf:
    @echo "Purging Cloudflare cache..."
    @bun run purge-cf

# Update to the latest version of the project scaffolding
[group('scaffolding')]
update-scaffolding:
    @echo "Updating project scaffolding..."
    @copier update -A --trust
    @bun install
    @echo "Project scaffolding updated."
    @echo "Please review the changes and commit."
