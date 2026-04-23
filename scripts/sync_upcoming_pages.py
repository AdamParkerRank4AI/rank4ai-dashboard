#!/usr/bin/env python3
"""Auto-mark upcoming_pages.json items as 'published' when the slug exists
on the live site (detected via crawl data). Runs daily.

Input:  src/data/live/upcoming_pages.json
Output: same file, with status updated.
"""
import json
import os
from datetime import datetime

LIVE = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
UPCOMING = os.path.join(LIVE, "upcoming_pages.json")


def main():
    if not os.path.exists(UPCOMING):
        print("No upcoming_pages.json — skipping")
        return

    with open(UPCOMING) as f:
        upcoming = json.load(f)

    changed = 0
    for site_id, site_data in upcoming.items():
        if not isinstance(site_data, dict):
            continue
        crawl_path = os.path.join(LIVE, f"crawl_{site_id}.json")
        if not os.path.exists(crawl_path):
            continue
        with open(crawl_path) as f:
            crawl = json.load(f)
        live_paths = {
            (p.get("path", "") or "").strip("/")
            for p in crawl.get("pages", [])
            if p.get("status") == 200
        }

        for page in site_data.get("pages", []):
            slug = (page.get("slug") or "").strip("/")
            if slug and slug in live_paths and page.get("status") != "published":
                page["status"] = "published"
                page["published_at"] = datetime.now().strftime("%Y-%m-%d")
                changed += 1
                print(f"  {site_id}: {slug} → published")

    upcoming["_meta"] = {"last_synced_at": datetime.now().isoformat()}

    with open(UPCOMING, "w") as f:
        json.dump(upcoming, f, indent=2)

    print(f"Synced {changed} upcoming pages to published status")


if __name__ == "__main__":
    main()
