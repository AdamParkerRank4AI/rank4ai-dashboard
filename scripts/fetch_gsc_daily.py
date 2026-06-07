#!/usr/bin/env python3
"""
Fetch TRUE per-day Google Search Console metrics (dimension=date) for the fleet.

Unlike gsc_history.json (which snapshots the rolling 28-day total each day for
trend lines), this stores one row PER CALENDAR DAY so the dashboard can sum real
day / week / month windows for the Fleet Quick View period toggle.

Output: src/data/live/gsc_daily.json
  { "<site_id>": { "fetched_at": iso, "days": [ {date, clicks, impressions, position}... ] } }
"""
import json
import os
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_FILE = os.path.expanduser('~/rank4ai-dashboard/scripts/ga4_token.json')
OUTPUT_DIR = os.path.expanduser('~/rank4ai-dashboard/src/data/live')
DAYS = 90

SITES = {
    "rank4ai": "sc-domain:rank4ai.co.uk",
    "market-invoice": "sc-domain:marketinvoice.co.uk",
    "seocompare": "sc-domain:seocompare.co.uk",
    "resiliencebuilder": "sc-domain:resiliencebuilder.co.uk",
    "bestbusinessloans": "https://bestbusinessloans.ai/",
    "fundbiz": "https://fundbiz.co.uk/",
    "cardmachines": "https://merchanthq.co.uk/",
    "kartapay": "https://kartapay.co.uk/",
    "peptideclear": "https://peptideclear.co.uk/",
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


def fetch_site(service, site_url):
    end_date = datetime.now() - timedelta(days=3)  # GSC has ~3-day delay
    start_date = end_date - timedelta(days=DAYS)
    resp = service.searchanalytics().query(
        siteUrl=site_url,
        body={
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "dimensions": ["date"],
            "rowLimit": 500,
        },
    ).execute()
    days = []
    for row in resp.get("rows", []):
        days.append({
            "date": row["keys"][0],
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "position": round(row.get("position", 0), 1),
        })
    days.sort(key=lambda d: d["date"])
    return days


def main():
    creds = get_creds()
    service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    out = {}
    for site_id, site_url in SITES.items():
        try:
            days = fetch_site(service, site_url)
            out[site_id] = {"fetched_at": datetime.now().isoformat(), "days": days}
            tot = sum(d["impressions"] for d in days)
            print(f"  {site_id:18} {len(days)} days, {tot} impr (90d)")
        except Exception as e:
            print(f"  {site_id:18} ERROR {repr(e)[:120]}")
            out[site_id] = {"fetched_at": datetime.now().isoformat(), "days": [], "error": str(e)[:200]}
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "gsc_daily.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {os.path.join(OUTPUT_DIR, 'gsc_daily.json')}")


if __name__ == "__main__":
    main()
