#!/usr/bin/env python3
"""
fetch_url_inspection.py — query GSC URL Inspection API for every URL in each
site's crawl, classify indexing status, and surface what's actually broken.

This is the missing piece. Our crawler only follows the sitemap, so it can't
see URLs that 404 or that Google has dropped. The URL Inspection API gives us
Google's view: indexed / not-indexed / 404 / redirect / robots-blocked.

Output: indexing_status.json with per_site classification + broken-link list.
Quota: 2,000 calls/property/day. Each call = 1 quota. Sleeping 0.4s between
calls to stay under 600/min burst.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

PROJECT_DIR = Path(__file__).resolve().parent.parent
LIVE = PROJECT_DIR / "src" / "data" / "live"
TOKEN_FILE = PROJECT_DIR / "scripts" / "ga4_token.json"

SITES = {
    "rank4ai":        ("sc-domain:rank4ai.co.uk",        "rank4ai.co.uk"),
    "market-invoice": ("sc-domain:marketinvoice.co.uk", "marketinvoice.co.uk"),
    "seocompare":     ("sc-domain:seocompare.co.uk",    "seocompare.co.uk"),
}

# Per-site cap to stay under 2000/day quota with margin
DAILY_CAP = 1500
SLEEP_BETWEEN = 0.4


def get_creds():
    with open(TOKEN_FILE) as f:
        td = json.load(f)
    creds = Credentials(
        token=td["token"],
        refresh_token=td["refresh_token"],
        token_uri=td["token_uri"],
        client_id=td["client_id"],
        client_secret=td["client_secret"],
        scopes=td.get("scopes", []),
    )
    if creds.expired or not creds.valid:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        td["token"] = creds.token
        with open(TOKEN_FILE, "w") as f:
            json.dump(td, f, indent=2)
    return creds


def inspect_url(service, site_property, url):
    """Returns dict with verdict + coverageState + lastCrawlTime."""
    try:
        body = {"inspectionUrl": url, "siteUrl": site_property, "languageCode": "en-GB"}
        resp = service.urlInspection().index().inspect(body=body).execute()
        idx = resp.get("inspectionResult", {}).get("indexStatusResult", {})
        return {
            "url": url,
            "verdict": idx.get("verdict"),  # PASS / PARTIAL / FAIL / NEUTRAL
            "coverage_state": idx.get("coverageState"),  # "Indexed", "Not found (404)", etc.
            "last_crawl_time": idx.get("lastCrawlTime"),
            "page_fetch_state": idx.get("pageFetchState"),
            "indexing_state": idx.get("indexingState"),
            "robots_txt_state": idx.get("robotsTxtState"),
            "google_canonical": idx.get("googleCanonical"),
            "user_canonical": idx.get("userCanonical"),
            "referring_urls": idx.get("referringUrls", [])[:5],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    except HttpError as e:
        return {"url": url, "error": f"HTTP {e.resp.status}", "checked_at": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        return {"url": url, "error": str(e)[:200], "checked_at": datetime.now(timezone.utc).isoformat()}


def site_urls(site_id):
    """Get all crawled URLs for a site (sitemap-derived) + any prior 'broken'
    URLs we've seen so re-checks happen automatically."""
    crawl_path = LIVE / f"crawl_{site_id}.json"
    if not crawl_path.exists():
        return []
    with open(crawl_path) as f:
        crawl = json.load(f)
    urls = set()
    for p in crawl.get("pages", []):
        u = p.get("url")
        if u:
            urls.add(u)
    return sorted(urls)


def classify(results):
    """Group results by GSC coverage state."""
    by_state = {}
    broken = []
    not_indexed_serveable = []  # discovered/crawled-not-indexed
    indexed = []
    redirects = []
    blocked = []
    errors = []
    for r in results:
        if r.get("error"):
            errors.append(r)
            continue
        cov = r.get("coverage_state") or "Unknown"
        by_state.setdefault(cov, []).append(r["url"])
        cov_lower = cov.lower()
        if "404" in cov or "not found" in cov_lower:
            broken.append(r)
        elif "indexed" in cov_lower and "not indexed" not in cov_lower:
            indexed.append(r)
        elif "not indexed" in cov_lower or "discovered" in cov_lower or "crawled" in cov_lower:
            not_indexed_serveable.append(r)
        elif "redirect" in cov_lower:
            redirects.append(r)
        elif "blocked" in cov_lower or "robots" in cov_lower:
            blocked.append(r)
    return {
        "by_coverage_state": {k: len(v) for k, v in by_state.items()},
        "indexed_count": len(indexed),
        "not_indexed_count": len(not_indexed_serveable),
        "broken_404_count": len(broken),
        "redirects_count": len(redirects),
        "blocked_count": len(blocked),
        "errors_count": len(errors),
        "broken_404_urls": [r["url"] for r in broken],
        "not_indexed_urls": [{"url": r["url"], "state": r["coverage_state"], "last_crawl": r.get("last_crawl_time")} for r in not_indexed_serveable[:50]],
        "broken_detail": [{"url": r["url"], "state": r["coverage_state"], "referring": r.get("referring_urls", [])} for r in broken[:50]],
    }


def fetch_site(service, site_id):
    site_property, domain = SITES[site_id]
    urls = site_urls(site_id)
    if not urls:
        print(f"  {site_id}: no crawled URLs to inspect")
        return None
    sample = urls[:DAILY_CAP]
    print(f"  {site_id}: inspecting {len(sample)}/{len(urls)} URLs (cap {DAILY_CAP})")
    results = []
    for i, url in enumerate(sample, 1):
        r = inspect_url(service, site_property, url)
        results.append(r)
        if i % 100 == 0:
            cov = r.get("coverage_state") or r.get("error", "?")
            print(f"    [{i}/{len(sample)}] last: {cov}")
        time.sleep(SLEEP_BETWEEN)
    classified = classify(results)
    classified["total_inspected"] = len(results)
    classified["total_in_sitemap"] = len(urls)
    classified["sample_capped"] = len(urls) > DAILY_CAP
    classified["fetched_at"] = datetime.now(timezone.utc).isoformat()
    classified["domain"] = domain
    return classified


def main():
    creds = get_creds()
    service = build("searchconsole", "v1", credentials=creds)
    out = {"computed_at": datetime.now(timezone.utc).isoformat(), "per_site": {}}

    target_sites = sys.argv[1:] or list(SITES.keys())
    for site_id in target_sites:
        if site_id not in SITES:
            print(f"  skipping unknown {site_id}")
            continue
        print(f"\n=== {site_id} ===")
        try:
            data = fetch_site(service, site_id)
            if data:
                out["per_site"][site_id] = data
        except Exception as e:
            print(f"  ERROR: {e}")
            out["per_site"][site_id] = {"error": str(e)[:300]}

    out_path = LIVE / "indexing_status.json"
    # Merge with prior data so a partial run doesn't wipe other sites' data
    if out_path.exists():
        try:
            with open(out_path) as f:
                prior = json.load(f)
            merged_per_site = prior.get("per_site", {}) or {}
            merged_per_site.update(out["per_site"])
            out["per_site"] = merged_per_site
        except Exception:
            pass

    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\n=== summary ===")
    for site_id, d in out["per_site"].items():
        if d.get("error"):
            print(f"  {site_id}: ERROR — {d['error']}")
            continue
        print(f"  {site_id}: indexed={d.get('indexed_count')} not_indexed={d.get('not_indexed_count')} broken_404={d.get('broken_404_count')} redirects={d.get('redirects_count')} blocked={d.get('blocked_count')} errors={d.get('errors_count')}")
    print(f"\nwritten: {out_path}")


if __name__ == "__main__":
    main()
