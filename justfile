# List available commands
default:
    @just --list

# Start local development server with watch mode
[group('Local Development')]
dev:
    @echo "Starting development server..."
    @bun run dev

# Build production bundles
[group('Build')]
build:
    @echo "Building production bundles..."
    @bun run build

# Serve the docs directory locally
[group('Local Development')]
serve PORT="8000":
    @echo "Serving docs on port {{PORT}}..."
    @PORT={{PORT}} bun run serve

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
