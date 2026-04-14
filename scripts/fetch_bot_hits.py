#!/usr/bin/env python3
"""
Fetch bot hit data from Cloudflare Worker API for each tracked site.
Saves to src/data/live/bot_hits.json
"""
import json
import os
from datetime import datetime, timezone

import requests

SITES = {
    "rank4ai": "https://rank4ai-tracker.dawn-field-3d16.workers.dev/api/bot-hits",
    "market-invoice": "https://rank4ai-tracker.dawn-field-3d16.workers.dev/api/bot-hits",
    "seocompare": "https://www.seocompare.co.uk/_bot-api/hits",
}
DAYS = 30

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(PROJECT_DIR, "src", "data", "live", "bot_hits.json")


def fetch_site(site, api_url):
    """Fetch bot hit data for a single site."""
    url = f"{api_url}?site={site}&days={DAYS}"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else data.get("data", [])
    except Exception as e:
        print(f"  Error fetching {site}: {e}")
        return []


def main():
    print("Fetching bot hit data...")
    now = datetime.now(timezone.utc).isoformat()
    result = {}

    for site, api_url in SITES.items():
        print(f"  {site}...")
        days = fetch_site(site, api_url)
        result[site] = {
            "fetched_at": now,
            "days": days,
        }
        print(f"    {len(days)} days of data")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
