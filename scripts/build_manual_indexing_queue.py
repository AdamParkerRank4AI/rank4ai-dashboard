#!/usr/bin/env python3
"""Build the daily Manual GSC Indexing Queue.

The Indexing API submits 200 URLs/day automatically. But Google's
"Request indexing" button in GSC URL Inspection is the only thing
that pushes a URL to the priority crawl queue. 20-30/day practical
limit per property.

This script picks the top 10 per site that Adam should paste into
URL Inspection, prioritised by:
  1. Never submitted before (highest priority)
  2. High-value paths (root, money pages, recent blog)
  3. Deprioritise tag/archive/pagination URLs

Writes src/data/live/manual_indexing_queue.json for the dashboard tile.
"""
import json
import os
import re
from datetime import datetime
from urllib.request import urlopen, Request

LIVE = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
INDEXING_PROGRESS = os.path.expanduser("~/indexing_progress.json")
OUTPUT = os.path.join(LIVE, "manual_indexing_queue.json")

SITES = {
    "rank4ai": {
        "sitemap": "https://www.rank4ai.co.uk/sitemap-0.xml",
        "gsc_property": "sc-domain:rank4ai.co.uk",
        "money_paths": ["/", "/services", "/about", "/contact", "/free-audit", "/ai-search-visibility", "/how-we-work"],
    },
    "market-invoice": {
        "sitemap": "https://www.marketinvoice.co.uk/sitemap-0.xml",
        "gsc_property": "sc-domain:marketinvoice.co.uk",
        "money_paths": ["/", "/compare", "/providers", "/guides", "/locations", "/contact"],
    },
    "seocompare": {
        "sitemap": "https://www.seocompare.co.uk/sitemap-0.xml",
        "gsc_property": "sc-domain:seocompare.co.uk",
        "money_paths": ["/", "/tools", "/agencies", "/guides", "/about", "/contact"],
    },
}

TOP_N = 10


def fetch_sitemap(url):
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 Rank4AI-Queue-Builder"})
        xml = urlopen(req, timeout=15).read().decode("utf-8", errors="ignore")
        return re.findall(r"<loc>(.*?)</loc>", xml)
    except Exception as e:
        print(f"  Sitemap fetch failed: {e}")
        return []


def score_url(url, money_paths):
    """Higher score = higher priority for manual submission."""
    path = re.sub(r"^https?://[^/]+", "", url).rstrip("/") or "/"
    score = 0

    # Money pages
    for mp in money_paths:
        if path == mp or path.startswith(mp + "/") or path == mp.rstrip("/"):
            score += 50
            break

    # Shallow pages beat deep pages
    depth = path.count("/")
    score += max(0, 20 - depth * 4)

    # Penalise pagination, archives, tag pages
    if re.search(r"/page/\d+", path) or re.search(r"/tag/", path) or re.search(r"/category/", path):
        score -= 30
    if re.search(r"\?.*(page|p)=\d+", url):
        score -= 30

    # Small bonus for /blog/ and /guides/ (fresh content)
    if "/blog/" in path or "/guides/" in path:
        score += 5

    return score


def normalise(url):
    return url.rstrip("/")


def load_seen():
    if not os.path.exists(INDEXING_PROGRESS):
        return set()
    try:
        with open(INDEXING_PROGRESS) as f:
            seen_map = json.load(f).get("seen", {})
        return {normalise(u) for u in seen_map}
    except Exception:
        return set()


def main():
    seen = load_seen()
    print(f"Loaded {len(seen)} previously-submitted URLs from indexing_progress.json")

    queue = {
        "generated_at": datetime.now().isoformat(),
        "instructions": "Paste each URL into Google Search Console URL Inspection and click 'Request Indexing'. 20-30/day practical limit per property.",
        "per_site": {},
    }

    for site_id, cfg in SITES.items():
        print(f"\n{site_id}:")
        urls = fetch_sitemap(cfg["sitemap"])
        if not urls:
            queue["per_site"][site_id] = {"error": "sitemap_unavailable", "top": []}
            continue

        # Prioritise: never submitted via API > submitted via API
        # (manual submission is especially useful for never-submitted pages)
        never_submitted = [u for u in urls if normalise(u) not in seen]
        scored = sorted(
            never_submitted,
            key=lambda u: -score_url(u, cfg["money_paths"])
        )

        # If we don't have 10 never-submitted, fill from already-submitted sorted by score
        top = scored[:TOP_N]
        if len(top) < TOP_N:
            also_submitted = sorted(
                [u for u in urls if normalise(u) in seen],
                key=lambda u: -score_url(u, cfg["money_paths"])
            )
            top = top + also_submitted[: TOP_N - len(top)]

        queue["per_site"][site_id] = {
            "sitemap_url_count": len(urls),
            "never_api_submitted": len(never_submitted),
            "gsc_property": cfg["gsc_property"],
            "gsc_inspect_url": f"https://search.google.com/search-console/inspect?resource_id={cfg['gsc_property'].replace(':', '%3A')}",
            "top": [
                {
                    "url": u,
                    "score": score_url(u, cfg["money_paths"]),
                    "api_submitted": normalise(u) in seen,
                }
                for u in top
            ],
        }
        print(f"  {len(urls)} URLs in sitemap, {len(never_submitted)} never API-submitted")
        for i, u in enumerate(top[:3], 1):
            print(f"    {i}. {u}")

    with open(OUTPUT, "w") as f:
        json.dump(queue, f, indent=2)
    print(f"\nWrote {OUTPUT}")


if __name__ == "__main__":
    main()
