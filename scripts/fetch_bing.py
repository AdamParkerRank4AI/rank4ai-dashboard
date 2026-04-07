#!/usr/bin/env python3
"""
Fetch Bing Webmaster Tools data for dashboard.
"""
import json
import os
from datetime import datetime, timedelta

import requests

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
API_KEY = "c129b8c91294404d96cca29e1cf613fe"
BASE_URL = "https://ssl.bing.com/webmaster/api.svc/json"

SITES = {
    "rank4ai": "https://www.rank4ai.co.uk/",
    "market-invoice": "https://www.marketinvoice.co.uk/",
}


def fetch_site(site_url, site_id):
    headers = {"Content-Type": "application/json"}
    params = {"apikey": API_KEY, "siteUrl": site_url}

    result = {
        "site_id": site_id,
        "site_url": site_url,
        "fetched_at": datetime.now().isoformat(),
    }

    # Get traffic stats
    try:
        resp = requests.get(
            f"{BASE_URL}/GetRankAndTrafficStats",
            params=params,
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            stats = data.get("d", [])
            if stats:
                latest = stats[-1] if isinstance(stats, list) else stats
                result["traffic_stats"] = stats[-7:] if isinstance(stats, list) else [stats]
        else:
            result["traffic_error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        result["traffic_error"] = str(e)[:100]

    # Get query stats (top keywords)
    try:
        resp = requests.get(
            f"{BASE_URL}/GetQueryStats",
            params=params,
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            queries = data.get("d", [])
            if queries and isinstance(queries, list):
                result["top_queries"] = queries[:25]
                result["total_queries"] = len(queries)
        else:
            result["query_error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        result["query_error"] = str(e)[:100]

    # Get page stats
    try:
        resp = requests.get(
            f"{BASE_URL}/GetPageStats",
            params=params,
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            pages = data.get("d", [])
            if pages and isinstance(pages, list):
                result["top_pages"] = pages[:25]
        else:
            result["page_error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        result["page_error"] = str(e)[:100]

    # Get crawl stats
    try:
        resp = requests.get(
            f"{BASE_URL}/GetCrawlStats",
            params=params,
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            crawl = data.get("d", [])
            if crawl:
                result["crawl_stats"] = crawl[-7:] if isinstance(crawl, list) else [crawl]
        else:
            result["crawl_error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        result["crawl_error"] = str(e)[:100]

    return result


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_data = {}
    for site_id, site_url in SITES.items():
        print(f"Fetching Bing data for {site_id}...")
        data = fetch_site(site_url, site_id)
        all_data[site_id] = data

        if "top_queries" in data:
            print(f"  Queries: {data.get('total_queries', 0)}")
        if "traffic_error" in data:
            print(f"  Traffic: {data['traffic_error']}")
        if "query_error" in data:
            print(f"  Queries: {data['query_error']}")

    output_file = os.path.join(OUTPUT_DIR, "bing.json")
    with open(output_file, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
