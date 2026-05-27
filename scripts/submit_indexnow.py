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
    "market-invoice": "https://marketinvoice.co.uk",
    "seocompare": "https://www.seocompare.co.uk",
    "bestbusinessloans": "https://bestbusinessloans.ai",
    "fundbiz": "https://fundbiz.co.uk",
    "cardmachines": "https://merchanthq.co.uk",
    "peptideclear": "https://peptideclear.co.uk",
    "kartapay": "https://kartapay.co.uk",
}

INDEXNOW_URL = "https://api.indexnow.org/indexnow"

# Per-site IndexNow keys — each registered in its own repo's public/<key>.txt.
# Falling back to BING_API_KEY (above) for sites not in this map.
# The single shared key 403'd as "UserForbiddedToAccessSite" because Bing
# associates each IndexNow key with the BWT account that originally claimed it.
SITE_KEYS = {
    "rank4ai":           "4c1cc17752ab451887a14b719906f527",
    "market-invoice":    "a2dbf411f85049958a10a31d0eea8ab9",
    "seocompare":        "4c1cc17752ab451887a14b719906f527",
    "bestbusinessloans": "6c8693c2af63422098320cf1a132e7d2",
    "fundbiz":           "4d8cee5b9f8249d8848a5305264ca1cc",
    "cardmachines":      "0090cd828ef442e38aa2c00baca23c6d",
    "peptideclear":      "9b4e84786bf3482db8081609777b3811",
    "kartapay":          "e7ac3dd5700130fb675be39a3a0effc5",
}


def get_urls_from_crawl(client_id):
    """Get all URLs from the latest crawl."""
    crawl_file = os.path.join(OUTPUT_DIR, f"crawl_{client_id}.json")
    if not os.path.exists(crawl_file):
        return []
    with open(crawl_file) as f:
        data = json.load(f)
    return [p["url"] for p in data.get("pages", [])]


def get_urls_from_sitemap(base_url):
    """Get all URLs from the live sitemap (source of truth, always current).

    Expands a sitemap index into its child sitemaps and follows redirects
    (e.g. www -> non-www), so the URLs returned are the canonical ones. This
    is preferred over crawl data because it always includes newly published
    pages and never silently returns nothing for a site that lacks crawl data.
    """
    import re
    base = base_url.rstrip("/")
    headers = {"User-Agent": "Mozilla/5.0"}
    for path in ("sitemap-index.xml", "sitemap.xml", "sitemap-0.xml"):
        try:
            r = requests.get(f"{base}/{path}", timeout=20, allow_redirects=True, headers=headers)
            if r.status_code != 200:
                continue
            xml = r.text
            if "<sitemapindex" in xml:
                urls = []
                for child in re.findall(r"<loc>([^<]+)</loc>", xml):
                    try:
                        cr = requests.get(child, timeout=20, allow_redirects=True, headers=headers)
                        if cr.status_code == 200:
                            urls += re.findall(r"<loc>([^<]+)</loc>", cr.text)
                    except Exception:
                        pass
                if urls:
                    return sorted(set(urls))
            else:
                urls = re.findall(r"<loc>([^<]+)</loc>", xml)
                if urls:
                    return sorted(set(urls))
        except Exception:
            pass
    return []


def submit_urls(client_id, urls):
    """Submit URLs via IndexNow API.

    The host (and key location) are derived from the actual URLs, grouped by
    hostname, so submissions always match the canonical host and never fail on
    a www/non-www mismatch with the configured base URL.
    """
    from urllib.parse import urlparse

    if not urls:
        return 0

    # Per-site key (each registered with its own BWT account), fallback to shared.
    key = SITE_KEYS.get(client_id, BING_API_KEY)

    by_host = {}
    for u in urls:
        host = urlparse(u).netloc
        if host:
            by_host.setdefault(host, []).append(u)

    batch_size = 100
    total_submitted = 0

    for host, host_urls in by_host.items():
        key_location = f"https://{host}/{key}.txt"
        for i in range(0, len(host_urls), batch_size):
            batch = host_urls[i:i + batch_size]
            payload = {
                "host": host,
                "key": key,
                "keyLocation": key_location,
                "urlList": batch,
            }
            try:
                resp = requests.post(INDEXNOW_URL, json=payload, timeout=15)
                if resp.status_code in [200, 202]:
                    total_submitted += len(batch)
                    print(f"  Submitted {len(batch)} URLs to {host} (batch {i // batch_size + 1})")
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

        # Prefer the live sitemap (always current, includes new pages); fall
        # back to crawl data only if the sitemap is unreachable.
        urls = get_urls_from_sitemap(SITES[client_id])
        source = "sitemap"
        if not urls:
            urls = get_urls_from_crawl(client_id)
            source = "crawl"
        print(f"\n{client_id}: {len(urls)} URLs to submit (from {source})")

        if urls:
            submitted = submit_urls(client_id, urls)
            results[client_id] = {
                "submitted": submitted,
                "total_urls": len(urls),
                "source": source,
                "submitted_at": datetime.now().isoformat(),
            }
            print(f"  Done: {submitted}/{len(urls)} submitted")
        else:
            print(f"  No URLs found (sitemap unreachable and no crawl data)")

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
