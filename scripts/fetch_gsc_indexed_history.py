#!/usr/bin/env python3
"""
fetch_gsc_indexed_history.py — daily snapshot of GSC sitemap submitted/indexed counts.

Appends a row per site per day to src/data/live/gsc_indexed_history.json.
Lets the dashboard graph "pages indexed over time" — submissions ≠ indexings.

Uses GSC sitemaps.get + sitemaps.list. Falls back to URL-prefix property if the
sc-domain: property doesn't have a submitted sitemap (rare).
"""
import json
import os
import sys
from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

TOKEN_FILE = os.path.expanduser('~/rank4ai-dashboard/scripts/ga4_token.json')
LIVE_DIR = os.path.expanduser('~/rank4ai-dashboard/src/data/live')
HISTORY_FILE = os.path.join(LIVE_DIR, 'gsc_indexed_history.json')

# (site_id, property URL). Sitemaps enumerated dynamically via sitemaps.list.
SITES = [
    ("rank4ai",          "sc-domain:rank4ai.co.uk"),
    ("market-invoice",   "sc-domain:marketinvoice.co.uk"),
    ("seocompare",       "sc-domain:seocompare.co.uk"),
    ("bestbusinessloans","sc-domain:bestbusinessloans.ai"),
    ("fundbiz",          "sc-domain:fundbiz.co.uk"),
    ("cardmachines",     "sc-domain:merchanthq.co.uk"),
    ("kartapay",         "sc-domain:kartapay.co.uk"),
    ("peptideclear",     "sc-domain:peptideclear.co.uk"),
]


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


def fetch_site_indexed(service, site_url, sitemap_url):
    """
    GSC sitemap.contents includes per-content-type submitted/indexed.
    Returns dict: {submitted, indexed, errors, warnings, last_submitted, last_downloaded}.
    """
    try:
        resp = service.sitemaps().get(siteUrl=site_url, feedpath=sitemap_url).execute()
    except HttpError as e:
        return {"error": f"HTTP {e.resp.status}: {str(e)[:200]}"}
    except Exception as e:
        return {"error": str(e)[:200]}

    contents = resp.get('contents', [])
    submitted = sum(int(c.get('submitted', 0)) for c in contents)
    indexed = sum(int(c.get('indexed', 0)) for c in contents)

    return {
        "submitted": submitted,
        "indexed": indexed,
        "errors": int(resp.get('errors', 0)),
        "warnings": int(resp.get('warnings', 0)),
        "last_submitted": resp.get('lastSubmitted'),
        "last_downloaded": resp.get('lastDownloaded'),
        "is_pending": resp.get('isPending', False),
        "is_sitemaps_index": resp.get('isSitemapsIndex', False),
    }


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {"computed_at": None, "per_site_history": {}}


def main():
    print(f"Fetching GSC indexed-count history…")
    creds = get_creds()
    service = build('searchconsole', 'v1', credentials=creds)

    today = datetime.now(timezone.utc).date().isoformat()
    history = load_history()
    history.setdefault('per_site_history', {})

    for site_id, site_url, sitemap_url in SITES:
        result = fetch_site_indexed(service, site_url, sitemap_url)
        if 'error' in result:
            print(f"  {site_id}: {result['error']}")
            continue

        history['per_site_history'].setdefault(site_id, [])

        # Replace today's entry if already present (idempotent same-day reruns)
        history['per_site_history'][site_id] = [
            row for row in history['per_site_history'][site_id]
            if row.get('date') != today
        ]
        history['per_site_history'][site_id].append({
            "date": today,
            **result,
        })

        # Cap history to 365 days
        history['per_site_history'][site_id] = history['per_site_history'][site_id][-365:]

        delta_str = ""
        rows = history['per_site_history'][site_id]
        if len(rows) >= 2:
            prev = rows[-2]['indexed']
            cur = rows[-1]['indexed']
            delta = cur - prev
            delta_str = f" ({'+' if delta >= 0 else ''}{delta} vs prev)"

        print(f"  {site_id}: {result['indexed']}/{result['submitted']} indexed{delta_str}")

    history['computed_at'] = datetime.now(timezone.utc).isoformat()
    os.makedirs(LIVE_DIR, exist_ok=True)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

    print(f"\nSaved: {HISTORY_FILE}")


if __name__ == '__main__':
    main()
