#!/usr/bin/env python3
"""
Check Brave Search for client visibility.
Brave has its own independent index — different from Google/Bing.
2,000 queries/month on free tier.
"""
import json
import os
import time
from datetime import datetime

import requests

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
BRAVE_API_KEY = "BSAcxOjWstVg4HFyqKF9ZXXx-Nc0IvW"

CLIENTS = {
    "rank4ai": {
        "brand": "Rank4AI",
        "domain": "rank4ai.co.uk",
        "queries": [
            "AI search visibility agency UK",
            "best AI SEO agencies UK",
            "what is AI search visibility",
            "GEO agency UK",
            "how to get found in ChatGPT",
        ],
    },
    "market-invoice": {
        "brand": "Market Invoice",
        "domain": "marketinvoice.co.uk",
        "queries": [
            "invoice finance UK",
            "best invoice factoring companies UK",
            "compare invoice finance providers UK",
            "how does invoice finance work",
            "invoice finance for small business UK",
        ],
    },
    "seocompare": {
        "brand": "SEO Compare",
        "domain": "seocompare.co.uk",
        "queries": [
            "compare SEO agencies UK",
            "best SEO companies UK",
            "how to choose an SEO agency",
        ],
    },
}

BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"


def search_brave(query):
    """Search Brave."""
    try:
        resp = requests.get(BRAVE_URL, params={
            "q": query,
            "count": 10,
            "country": "gb",
        }, headers={
            "X-Subscription-Token": BRAVE_API_KEY,
            "Accept": "application/json",
        }, timeout=15)

        if resp.status_code != 200:
            return {"query": query, "error": f"HTTP {resp.status_code}: {resp.text[:100]}"}

        data = resp.json()
        results = []
        for r in data.get("web", {}).get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "domain": r.get("url", "").split("/")[2] if r.get("url") else "",
                "description": r.get("description", "")[:200],
            })

        return {
            "query": query,
            "results": results[:10],
            "total": data.get("web", {}).get("totalResults", 0),
        }

    except Exception as e:
        return {"query": query, "error": str(e)[:100]}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_results = {}

    for client_id, config in CLIENTS.items():
        print(f"\n{config['brand']}:")
        results = []
        found_count = 0

        for query in config["queries"]:
            time.sleep(1)
            result = search_brave(query)
            results.append(result)

            if "error" in result:
                print(f"  ERROR: {query[:40]} — {result['error']}")
                continue

            # Check if client appears
            position = None
            for i, r in enumerate(result.get("results", []), 1):
                if config["domain"] in r.get("url", ""):
                    position = i
                    found_count += 1
                    break

            pos_str = f"#{position}" if position else "Not ranked"
            top3 = [r["domain"].replace("www.", "") for r in result.get("results", [])[:3]]
            print(f"  {pos_str} | {query[:40]} | Top: {', '.join(top3)}")

        total = len([r for r in results if "error" not in r])
        all_results[client_id] = {
            "brand": config["brand"],
            "domain": config["domain"],
            "checked_at": datetime.now().isoformat(),
            "total_queries": total,
            "found_count": found_count,
            "visibility_pct": round(found_count / max(total, 1) * 100, 1),
            "results": results,
        }

        print(f"  Brave visibility: {found_count}/{total} ({round(found_count/max(total,1)*100,1)}%)")

    output_file = os.path.join(OUTPUT_DIR, "brave_search.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
