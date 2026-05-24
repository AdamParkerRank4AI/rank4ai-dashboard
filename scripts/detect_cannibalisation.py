#!/usr/bin/env python3
"""
detect_cannibalisation.py — fetch GSC with (query, page) dimensions and flag
queries where 2+ pages from the same site both rank in the top 20.

Cannibalisation = two pages competing for the same query. Splits link equity
and confuses Google about which is canonical. Fixes:
  - Consolidate (301 redirect the weaker page to the stronger)
  - Differentiate (rewrite one page to target a sibling intent)
  - Internal-link from weaker to stronger (concentrates signal)

Output → src/data/live/cannibalisation.json (per-site).

Runs daily via refresh_all.py.
"""
import json
import os
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_FILE = Path(os.path.expanduser("~/rank4ai-dashboard/scripts/ga4_token.json"))
LIVE = Path(os.path.expanduser("~/rank4ai-dashboard/src/data/live"))

# Match fetch_gsc.py SITES
SITES = {
    "rank4ai":           "sc-domain:rank4ai.co.uk",
    "market-invoice":    "sc-domain:marketinvoice.co.uk",
    "seocompare":        "sc-domain:seocompare.co.uk",
    "resiliencebuilder": "sc-domain:resiliencebuilder.co.uk",
    "bestbusinessloans": "https://bestbusinessloans.ai/",
    "fundbiz":           "https://fundbiz.co.uk/",
    "cardmachines":      "https://merchanthq.co.uk/",
    "kartapay":          "https://kartapay.co.uk/",
    "peptideclear":      "https://peptideclear.co.uk/",
}


def get_creds():
    with open(TOKEN_FILE) as f:
        t = json.load(f)
    creds = Credentials(token=t['token'], refresh_token=t['refresh_token'],
                        token_uri=t['token_uri'], client_id=t['client_id'],
                        client_secret=t['client_secret'], scopes=t.get('scopes', []))
    if creds.expired or not creds.valid:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
    return creds


def fetch_query_page(service, site_url):
    """Pull GSC query+page dim, last 28 days, top 1000 rows."""
    end_date = datetime.now() - timedelta(days=3)
    start_date = end_date - timedelta(days=28)
    try:
        resp = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "dimensions": ["query", "page"],
                "rowLimit": 1000,
                "type": "web",
            }
        ).execute()
        return resp.get("rows", [])
    except Exception as e:
        return {"error": str(e)[:200]}


def detect_for_site(rows):
    """Group by query, find cases with 2+ pages in top 20."""
    if isinstance(rows, dict): return {"error": rows.get("error")}
    by_query = defaultdict(list)
    for r in rows:
        if len(r.get("keys", [])) < 2: continue
        q, p = r["keys"][0], r["keys"][1]
        pos = round(r.get("position", 0), 1)
        imp = r.get("impressions", 0)
        clicks = r.get("clicks", 0)
        if pos > 20: continue
        by_query[q].append({"page": p, "position": pos, "impressions": imp, "clicks": clicks})

    cannibals = []
    for q, pages in by_query.items():
        if len(pages) < 2: continue
        # Sort: leader first
        pages.sort(key=lambda x: x["position"])
        # Total impressions across all competing pages
        total_imp = sum(p["impressions"] for p in pages)
        if total_imp < 10: continue  # noise floor
        cannibals.append({
            "query": q,
            "competing_pages": len(pages),
            "total_impressions": total_imp,
            "total_clicks": sum(p["clicks"] for p in pages),
            "pages": pages[:5],  # top 5 competing
        })
    cannibals.sort(key=lambda x: -x["total_impressions"])
    return cannibals


def main():
    out = {"checked_at": datetime.now(timezone.utc).isoformat(), "sites": {}}
    try:
        creds = get_creds()
    except Exception as e:
        print(f"creds error: {e}")
        out["error"] = str(e)[:200]
        with open(LIVE / "cannibalisation.json", "w") as f:
            json.dump(out, f, indent=2)
        return

    service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    for site_id, url in SITES.items():
        print(f"Cannibalisation pull → {site_id}...")
        rows = fetch_query_page(service, url)
        cannibals = detect_for_site(rows)
        if isinstance(cannibals, dict) and "error" in cannibals:
            out["sites"][site_id] = {"error": cannibals["error"]}
            continue
        out["sites"][site_id] = {
            "count": len(cannibals),
            "top": cannibals[:25],
        }
        print(f"  {len(cannibals)} cannibalised queries")

    with open(LIVE / "cannibalisation.json", "w") as f:
        json.dump(out, f, indent=2)
    print("Saved → cannibalisation.json")


if __name__ == "__main__":
    main()
