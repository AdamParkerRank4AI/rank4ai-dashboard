#!/usr/bin/env python3
"""
Submit URLs to Bing/Yandex via IndexNow API.
Free, unlimited, instant indexing.

Usage:
  python3 submit_indexnow.py rank4ai          # Submit all pages from crawl
  python3 submit_indexnow.py market-invoice   # Submit all pages from crawl
  python3 submit_indexnow.py all              # Submit all clients
"""
import json
import os
import sys
from datetime import datetime

import requests

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
BING_API_KEY = "c129b8c91294404d96cca29e1cf613fe"

SITES = {
    "rank4ai": "https://www.rank4ai.co.uk",
    "market-invoice": "https://www.marketinvoice.co.uk",
    "seocompare": "https://www.seocompare.co.uk",
}

INDEXNOW_URL = "https://api.indexnow.org/indexnow"


def get_urls_from_crawl(client_id):
    """Get all URLs from the latest crawl."""
    crawl_file = os.path.join(OUTPUT_DIR, f"crawl_{client_id}.json")
    if not os.path.exists(crawl_file):
        return []
    with open(crawl_file) as f:
        data = json.load(f)
    return [p["url"] for p in data.get("pages", [])]


def submit_urls(client_id, urls):
    """Submit URLs via IndexNow API."""
    host = SITES.get(client_id, "").replace("https://", "").replace("http://", "")
    if not host:
        print(f"  Unknown client: {client_id}")
        return

    # IndexNow accepts batch submissions
    batch_size = 100
    total_submitted = 0

    for i in range(0, len(urls), batch_size):
        batch = urls[i:i + batch_size]

        payload = {
            "host": host,
            "key": BING_API_KEY,
            "urlList": batch,
        }

        try:
            resp = requests.post(INDEXNOW_URL, json=payload, timeout=15)
            if resp.status_code in [200, 202]:
                total_submitted += len(batch)
                print(f"  Submitted {len(batch)} URLs (batch {i // batch_size + 1})")
            else:
                print(f"  Batch {i // batch_size + 1} failed: HTTP {resp.status_code} — {resp.text[:100]}")
        except Exception as e:
            print(f"  Batch error: {e}")

    return total_submitted


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 submit_indexnow.py <client_id|all>")
        return

    target = sys.argv[1]
    clients = list(SITES.keys()) if target == "all" else [target]

    results = {}
    for client_id in clients:
        if client_id not in SITES:
            print(f"Unknown client: {client_id}")
            continue

        urls = get_urls_from_crawl(client_id)
        print(f"\n{client_id}: {len(urls)} URLs to submit")

        if urls:
            submitted = submit_urls(client_id, urls)
            results[client_id] = {
                "submitted": submitted,
                "total_urls": len(urls),
                "submitted_at": datetime.now().isoformat(),
            }
            print(f"  Done: {submitted}/{len(urls)} submitted")
        else:
            print(f"  No crawl data — run crawl_sites.py first")

    # Save submission log
    log_file = os.path.join(OUTPUT_DIR, "indexnow_log.json")
    if os.path.exists(log_file):
        with open(log_file) as f:
            log = json.load(f)
    else:
        log = []

    log.append({
        "date": datetime.now().isoformat(),
        "results": results,
    })

    with open(log_file, "w") as f:
        json.dump(log[-50:], f, indent=2)  # Keep last 50 submissions

    print(f"\nLog saved → {log_file}")


if __name__ == "__main__":
    main()
