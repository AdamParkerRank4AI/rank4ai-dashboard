#!/usr/bin/env python3
"""
Check what Google returns for key queries using Custom Search API.
Shows if AI Overviews appear, what sites rank, featured snippets.
Free — 100 queries/day.

Note: Requires a Custom Search Engine ID (cx).
Create one at programmablesearchengine.google.com — set to search the whole web.
"""
import json
import os
from datetime import datetime

import requests

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
API_KEY = "AIzaSyBVkLChwxuGJWkWE1ywpiT_pmcUxyjeh0s"

# You need to create a Custom Search Engine at programmablesearchengine.google.com
# Set it to "Search the entire web" and get the cx ID
# For now, this is a placeholder — replace with your cx ID
CSE_ID = ""  # TODO: Create at programmablesearchengine.google.com

CLIENTS = {
    "rank4ai": {
        "brand": "Rank4AI",
        "domain": "rank4ai.co.uk",
        "queries": [
            "AI search visibility agency UK",
            "best AI SEO agencies UK",
            "GEO agency UK",
            "how to get found in ChatGPT",
            "AI search audit UK",
        ],
    },
    "market-invoice": {
        "brand": "Market Invoice",
        "domain": "marketinvoice.co.uk",
        "queries": [
            "invoice finance UK",
            "best invoice factoring companies UK",
            "compare invoice finance providers",
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
            "SEO agency comparison",
        ],
    },
}

SEARCH_URL = "https://www.googleapis.com/customsearch/v1"


def search_google(query):
    """Search Google via Custom Search API."""
    if not CSE_ID:
        return {"query": query, "error": "No Custom Search Engine ID configured. Create one at programmablesearchengine.google.com"}

    try:
        resp = requests.get(SEARCH_URL, params={
            "key": API_KEY,
            "cx": CSE_ID,
            "q": query,
            "num": 10,
        }, timeout=15)

        if resp.status_code != 200:
            return {"query": query, "error": f"HTTP {resp.status_code}"}

        data = resp.json()
        results = []
        brand_position = None

        for i, item in enumerate(data.get("items", []), 1):
            result = {
                "position": i,
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "domain": item.get("displayLink", ""),
            }
            results.append(result)

        total_results = int(data.get("searchInformation", {}).get("totalResults", 0))

        return {
            "query": query,
            "total_results": total_results,
            "results": results,
        }

    except Exception as e:
        return {"query": query, "error": str(e)[:100]}


def main():
    if not CSE_ID:
        print("Custom Search Engine ID not configured.")
        print("To set up:")
        print("1. Go to programmablesearchengine.google.com")
        print("2. Click 'Add' to create a new search engine")
        print("3. Set 'Search the entire web' to ON")
        print("4. Copy the Search Engine ID (cx)")
        print("5. Paste it into this script as CSE_ID")
        print("\nThis is free — 100 queries/day.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_results = {}

    for client_id, config in CLIENTS.items():
        print(f"\n{client_id}:")
        results = []

        for query in config["queries"]:
            result = search_google(query)
            results.append(result)

            if "results" in result:
                # Check if brand appears in top 10
                for r in result["results"]:
                    if config["domain"] in r.get("link", ""):
                        print(f"  #{r['position']}: {query}")
                        break
                else:
                    print(f"  Not in top 10: {query}")

        all_results[client_id] = {
            "brand": config["brand"],
            "checked_at": datetime.now().isoformat(),
            "results": results,
        }

    output_file = os.path.join(OUTPUT_DIR, "google_search.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
