import os

import cloudflare


def purge_cache(zone_id, api_token):
    cf = cloudflare.Cloudflare(api_token=api_token)
    try:
        cf.cache.purge(zone_id=zone_id, purge_everything=True)
        print(f"Cache purged for zone {zone_id}")
    except cloudflare._exceptions.CloudflareError as e:
        print(f"Failed to purge cache: {e}")


if __name__ == "__main__":
    ZONE_ID = os.environ.get("CLOUDFLARE_ZONE_ID")
    API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")
    if ZONE_ID and API_TOKEN:
        purge_cache(ZONE_ID, API_TOKEN)
    else:
        print(
            "Please provide CLOUDFLARE_ZONE_ID and CLOUDFLARE_API_TOKEN environment variables"
        )
