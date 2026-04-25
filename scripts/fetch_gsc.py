#!/usr/bin/env python3
"""
Fetch Google Search Console data for dashboard.
"""
import json
import os
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_FILE = os.path.expanduser('~/rank4ai-dashboard/scripts/ga4_token.json')
OUTPUT_DIR = os.path.expanduser('~/rank4ai-dashboard/src/data/live')

SITES = {
    "rank4ai": "sc-domain:rank4ai.co.uk",
    "market-invoice": "sc-domain:marketinvoice.co.uk",
    "seocompare": "sc-domain:seocompare.co.uk",
}

# Fallback URL-prefix formats if domain property doesn't work
SITES_FALLBACK = {
    "rank4ai": "https://www.rank4ai.co.uk/",
    "market-invoice": "https://www.marketinvoice.co.uk/",
    "seocompare": "https://www.seocompare.co.uk/",
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


def fetch_site(service, site_url, site_id):
    end_date = datetime.now() - timedelta(days=3)  # GSC data has 3-day delay
    start_date = end_date - timedelta(days=28)

    # Top queries
    queries_resp = service.searchanalytics().query(
        siteUrl=site_url,
        body={
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "dimensions": ["query"],
            "rowLimit": 100,
            "type": "web",
        }
    ).execute()

    top_queries = []
    for row in queries_resp.get("rows", []):
        top_queries.append({
            "query": row["keys"][0],
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": round(row.get("ctr", 0) * 100, 2),
            "position": round(row.get("position", 0), 1),
        })

    # Top pages
    pages_resp = service.searchanalytics().query(
        siteUrl=site_url,
        body={
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "dimensions": ["page"],
            "rowLimit": 100,
            "type": "web",
        }
    ).execute()

    # GSC domain properties (sc-domain:) return both www + bare host variants.
    # Normalise by stripping "www." and merging stats so the same page isn't
    # double-counted in the top_pages list.
    def normalise_page(url):
        import re
        return re.sub(r"^(https?://)(www\.)", r"\1", url)

    page_agg = {}
    for row in pages_resp.get("rows", []):
        norm = normalise_page(row["keys"][0])
        if norm not in page_agg:
            page_agg[norm] = {
                "page": norm,
                "clicks": 0,
                "impressions": 0,
                "_ctr_num": 0.0,
                "_pos_num": 0.0,
            }
        clicks = row.get("clicks", 0)
        impressions = row.get("impressions", 0)
        page_agg[norm]["clicks"] += clicks
        page_agg[norm]["impressions"] += impressions
        page_agg[norm]["_pos_num"] += (row.get("position", 0) or 0) * impressions

    top_pages = []
    for p in page_agg.values():
        imp = p["impressions"]
        top_pages.append({
            "page": p["page"],
            "clicks": p["clicks"],
            "impressions": imp,
            "ctr": round((p["clicks"] / imp * 100) if imp else 0, 2),
            "position": round((p["_pos_num"] / imp) if imp else 0, 1),
        })
    top_pages.sort(key=lambda x: -x["impressions"])

    # Content gaps: high impressions, low clicks
    gaps = [q for q in top_queries if q["impressions"] >= 10 and q["ctr"] < 2.0]
    gaps.sort(key=lambda x: x["impressions"], reverse=True)

    # Totals
    totals_resp = service.searchanalytics().query(
        siteUrl=site_url,
        body={
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "type": "web",
        }
    ).execute()

    totals = {}
    for row in totals_resp.get("rows", []):
        totals = {
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": round(row.get("ctr", 0) * 100, 2),
            "position": round(row.get("position", 0), 1),
        }

    # AI Overview appearances (searchAppearance filter)
    ai_overview_data = {}
    try:
        aio_resp = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "dimensions": ["query"],
                "dimensionFilterGroups": [{
                    "filters": [{
                        "dimension": "searchAppearance",
                        "expression": "AI_OVERVIEW"
                    }]
                }],
                "rowLimit": 25,
                "type": "web",
            }
        ).execute()

        aio_queries = []
        for row in aio_resp.get("rows", []):
            aio_queries.append({
                "query": row["keys"][0],
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
            })

        ai_overview_data = {
            "total_impressions": sum(q["impressions"] for q in aio_queries),
            "total_clicks": sum(q["clicks"] for q in aio_queries),
            "queries": aio_queries,
        }
    except Exception as e:
        ai_overview_data = {"error": str(e)[:100], "queries": []}

    return {
        "site_id": site_id,
        "site_url": site_url,
        "fetched_at": datetime.now().isoformat(),
        "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "totals": totals,
        "top_queries": top_queries,
        "top_pages": top_pages,
        "content_gaps": gaps[:15],
        "ai_overviews": ai_overview_data,
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    creds = get_creds()
    service = build('searchconsole', 'v1', credentials=creds)

    all_data = {}
    for site_id, site_url in SITES.items():
        print(f"Fetching GSC data for {site_id} ({site_url})...")
        try:
            data = fetch_site(service, site_url, site_id)
            all_data[site_id] = data
            print(f"  Clicks: {data['totals'].get('clicks', 0)}")
            print(f"  Impressions: {data['totals'].get('impressions', 0)}")
            print(f"  Avg Position: {data['totals'].get('position', 0)}")
            print(f"  Content Gaps: {len(data['content_gaps'])}")
        except Exception as e:
            print(f"  Error with domain property: {e}")
            # Try URL-prefix fallback
            fallback = SITES_FALLBACK.get(site_id)
            if fallback:
                print(f"  Trying URL prefix: {fallback}")
                try:
                    data = fetch_site(service, fallback, site_id)
                    all_data[site_id] = data
                    print(f"  Clicks: {data['totals'].get('clicks', 0)}")
                    print(f"  Impressions: {data['totals'].get('impressions', 0)}")
                except Exception as e2:
                    print(f"  Fallback also failed: {e2}")

    output_file = os.path.join(OUTPUT_DIR, "gsc.json")
    with open(output_file, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
