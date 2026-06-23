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
    "homesandhedge": "https://homesandhedge.co.uk",
    "hervitals": "https://hervitals.co.uk",
    "adhdhelper": "https://adhdhelper.co.uk",
    "company-rescue": "https://ltdturnaround.co.uk",
    "datesandtimes": "https://datesandtimes.co.uk",
    "fitcalcs": "https://fitcalcs.co.uk",
    "babydata": "https://babydata.co.uk",
    "vettedhome": "https://vettedhome.co.uk",
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
    "homesandhedge":     "4109de09679304557367b5b3e1b90c9b",
    "hervitals":         "4d36b67015e69fd2c5009095402cac74",
    "adhdhelper":        "a39ace08e7ac01f94c8fadff07824ebd",
    "company-rescue":    "1644a63379414ee2be55d249cffa2d7d",
    "datesandtimes":     "b77809bc20917b53ed29bef15cf3fb64",
    "fitcalcs":          "34efe4973ea9b6923b1bb736aad21f75",
    "babydata":          "723526312aa65870fda148e84ca0b79a",
    "vettedhome":        "e8ac7f2771ef3889025ba977c4ace41e",
}


STATE_FILE = os.path.join(OUTPUT_DIR, "indexnow_state.json")


def load_state():
    """url->lastmod map per client of what we've already submitted, so we only
    ping IndexNow for NEW or CHANGED urls instead of re-submitting the whole
    sitemap every run (Bing flags that as over-use)."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_urls_from_crawl(client_id):
    """Get all URLs from the latest crawl as {url: ""} (no lastmod available)."""
    crawl_file = os.path.join(OUTPUT_DIR, f"crawl_{client_id}.json")
    if not os.path.exists(crawl_file):
        return {}
    with open(crawl_file) as f:
        data = json.load(f)
    return {p["url"]: "" for p in data.get("pages", []) if p.get("url")}


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

    def parse_urlset(xml):
        # Map each <loc> to its <lastmod> (empty string if absent), so callers
        # can detect changed pages, not just new ones.
        out = {}
        for block in re.findall(r"<url>(.*?)</url>", xml, re.S):
            loc = re.search(r"<loc>([^<]+)</loc>", block)
            if not loc:
                continue
            lm = re.search(r"<lastmod>([^<]+)</lastmod>", block)
            out[loc.group(1).strip()] = (lm.group(1).strip() if lm else "")
        # Fallback for sitemaps without <url> wrappers
        if not out:
            for loc in re.findall(r"<loc>([^<]+)</loc>", xml):
                out[loc.strip()] = ""
        return out

    for path in ("sitemap-index.xml", "sitemap.xml", "sitemap-0.xml"):
        try:
            r = requests.get(f"{base}/{path}", timeout=20, allow_redirects=True, headers=headers)
            if r.status_code != 200:
                continue
            xml = r.text
            if "<sitemapindex" in xml:
                urls = {}
                for child in re.findall(r"<loc>([^<]+)</loc>", xml):
                    try:
                        cr = requests.get(child, timeout=20, allow_redirects=True, headers=headers)
                        if cr.status_code == 200:
                            urls.update(parse_urlset(cr.text))
                    except Exception:
                        pass
                if urls:
                    return urls
            else:
                urls = parse_urlset(xml)
                if urls:
                    return urls
        except Exception:
            pass
    return {}


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

    # --force / --all-urls re-submits everything (first run, or a manual reset).
    # Default behaviour now only submits NEW or CHANGED urls vs indexnow_state.json.
    force = "--force" in sys.argv or "--all-urls" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    target = args[0] if args else "all"
    clients = list(SITES.keys()) if target == "all" else [target]

    results = {}
    state = load_state()
    import sys as _sys2, os as _os2; _sys2.path.insert(0, _os2.path.dirname(_os2.path.abspath(__file__)))
    from site_status import skip as _skip
    for client_id in clients:
        if client_id not in SITES:
            print(f"Unknown client: {client_id}")
            continue
        if _skip(client_id):
            print(f"  skip {client_id} (paused/pre-launch)"); continue

        # Prefer the live sitemap (always current, includes new pages); fall
        # back to crawl data only if the sitemap is unreachable.
        url_map = get_urls_from_sitemap(SITES[client_id])
        source = "sitemap"
        if not url_map:
            url_map = get_urls_from_crawl(client_id)
            source = "crawl"

        # Only submit NEW or CHANGED urls — never re-ping the whole sitemap
        # (that's what triggered Bing's IndexNow over-use warning).
        prev = state.get(client_id, {})
        if force:
            to_submit = list(url_map.keys())
        else:
            to_submit = [u for u, lm in url_map.items() if prev.get(u) != lm]
        print(f"\n{client_id}: {len(to_submit)} new/changed of {len(url_map)} URLs (from {source})")

        if to_submit:
            submitted = submit_urls(client_id, to_submit)
            # Record current lastmod for everything we just submitted.
            merged = dict(prev)
            for u in to_submit:
                merged[u] = url_map.get(u, "")
            state[client_id] = merged
            results[client_id] = {
                "submitted": submitted,
                "new_or_changed": len(to_submit),
                "total_urls": len(url_map),
                "source": source,
                "submitted_at": datetime.now().isoformat(),
            }
            print(f"  Done: {submitted}/{len(to_submit)} submitted ({len(url_map)} total, rest unchanged)")
        elif url_map:
            print(f"  Nothing new or changed since last run — skipped (no re-submit)")
        else:
            print(f"  No URLs found (sitemap unreachable and no crawl data)")

    save_state(state)

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
