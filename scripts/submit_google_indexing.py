#!/usr/bin/env python3
"""
Submit URLs to Google via the Indexing API for fast indexing.
Uses OAuth credentials (same as GA4/GSC).

Usage:
  python3 submit_google_indexing.py rank4ai              # Submit all crawled pages
  python3 submit_google_indexing.py market-invoice 10    # Submit first 10
  python3 submit_google_indexing.py seocompare /path/    # Submit specific URL path
"""
import json
import os
import sys
import time
from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_FILE = os.path.expanduser('~/rank4ai-dashboard/scripts/ga4_token.json')
LIVE_DIR = os.path.expanduser('~/rank4ai-dashboard/src/data/live')
LOG_FILE = os.path.join(LIVE_DIR, 'google_indexing_log.json')

SITES = {
    "rank4ai": "https://www.rank4ai.co.uk",
    "market-invoice": "https://www.marketinvoice.co.uk",
    "seocompare": "https://www.seocompare.co.uk",
    "rank4ai-staging": "https://rank4ai-staging.pages.dev",
    "rank4ai-online": "https://www.rank4ai.online",
}


def get_creds():
    with open(TOKEN_FILE) as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data['token'],
        refresh_token=token_data['refresh_token'],
        token_uri=token_data['token_uri'],
        client_id=token_data['client_id'],
        client_secret=token_data['client_secret'],
        scopes=token_data.get('scopes', []),
    )
    if creds.expired or not creds.valid:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        token_data['token'] = creds.token
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)
    return creds


def submit_url(service, url, action="URL_UPDATED"):
    """Submit a single URL. action: URL_UPDATED or URL_DELETED"""
    try:
        body = {
            "url": url,
            "type": action,
        }
        resp = service.urlNotifications().publish(body=body).execute()
        return {"url": url, "status": "ok", "response": resp.get("urlNotificationMetadata", {})}
    except Exception as e:
        return {"url": url, "status": "error", "error": str(e)[:200]}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 submit_google_indexing.py <client_id> [limit|path]")
        return

    client_id = sys.argv[1]
    limit_or_path = sys.argv[2] if len(sys.argv) > 2 else None

    base_url = SITES.get(client_id)
    if not base_url:
        print(f"Unknown client: {client_id}")
        return

    creds = get_creds()
    service = build('indexing', 'v3', credentials=creds)

    # Get URLs to submit
    urls = []
    if limit_or_path and limit_or_path.startswith("/"):
        # Specific path
        urls = [base_url + limit_or_path]
    else:
        # From crawl data
        crawl_file = os.path.join(LIVE_DIR, f"crawl_{client_id}.json")
        if os.path.exists(crawl_file):
            with open(crawl_file) as f:
                crawl = json.load(f)
            urls = [p["url"] for p in crawl.get("pages", []) if p.get("word_count", 0) > 20]
        else:
            print(f"No crawl data for {client_id}")
            return

        if limit_or_path and limit_or_path.isdigit():
            urls = urls[:int(limit_or_path)]

    print(f"Submitting {len(urls)} URLs for {client_id}...")

    # Load existing log
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            log = json.load(f)
    else:
        log = {}

    if client_id not in log:
        log[client_id] = {"submissions": []}

    submitted = 0
    errors = 0
    for url in urls:
        result = submit_url(service, url)
        if result["status"] == "ok":
            submitted += 1
            print(f"  OK: {url[-50:]}")
        else:
            errors += 1
            print(f"  ERROR: {url[-50:]} — {result['error'][:80]}")

        log[client_id]["submissions"].append({
            "url": url,
            "submitted_at": datetime.now().isoformat(),
            "status": result["status"],
        })

        # Google Indexing API limit: 200/day
        if submitted >= 200:
            print(f"\nHit daily limit (200). Remaining URLs will need to be submitted tomorrow.")
            break

        time.sleep(0.5)

    # Keep last 500 entries
    log[client_id]["submissions"] = log[client_id]["submissions"][-500:]

    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

    print(f"\nDone: {submitted} submitted, {errors} errors")
    print(f"Log: {LOG_FILE}")


if __name__ == "__main__":
    main()
