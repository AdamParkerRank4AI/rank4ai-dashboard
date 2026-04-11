#!/usr/bin/env python3
"""
Fetch Google AI Mode/Overview data via DataForSEO API.
$0.004 per SERP (Live) or $0.0012 (Standard queue).

Sign up at dataforseo.com — $1 free credit on signup.
Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD env vars.

Usage:
  python3 fetch_dataforseo.py           # Run for all clients
  python3 fetch_dataforseo.py rank4ai   # Run for one client
"""
import json
import os
import sys
import time
import base64
from datetime import datetime

import requests

LIVE_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
OUTPUT = os.path.join(LIVE_DIR, "ai_overview_serp.json")

# DataForSEO credentials
LOGIN = os.environ.get("DATAFORSEO_LOGIN", "")
PASSWORD = os.environ.get("DATAFORSEO_PASSWORD", "")

CLIENTS = {
    "rank4ai": {
        "queries": [
            "AI search visibility agency UK",
            "best AI SEO agencies UK",
            "what is AI search visibility",
            "GEO agency UK",
            "how to get found in ChatGPT",
        ],
    },
    "market-invoice": {
        "queries": [
            "invoice finance UK",
            "best invoice factoring companies UK",
            "compare invoice finance providers",
            "how does invoice finance work",
            "invoice finance for small business UK",
        ],
    },
    "seocompare": {
        "queries": [
            "compare SEO agencies UK",
            "best SEO companies UK",
            "how to choose an SEO agency",
        ],
    },
}

API_URL = "https://api.dataforseo.com/v3/serp/google/organic/live/regular"
AI_MODE_URL = "https://api.dataforseo.com/v3/serp/google/ai_overview/live/regular"


def get_auth_header():
    if not LOGIN or not PASSWORD:
        return None
    creds = base64.b64encode(f"{LOGIN}:{PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}


def fetch_serp(query, check_ai_overview=True):
    """Fetch SERP data including AI Overview detection."""
    headers = get_auth_header()
    if not headers:
        return {"error": "No DataForSEO credentials. Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD."}

    # Standard SERP with AI Overview detection
    payload = [{
        "keyword": query,
        "location_code": 2826,  # UK
        "language_code": "en",
        "device": "desktop",
        "os": "windows",
    }]

    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}

        data = resp.json()
        tasks = data.get("tasks", [])
        if not tasks or tasks[0].get("status_code") != 20000:
            return {"error": tasks[0].get("status_message", "Unknown error") if tasks else "No tasks"}

        result = tasks[0].get("result", [{}])[0]
        items = result.get("items", [])

        # Extract organic results
        organic = []
        ai_overview = None

        for item in items:
            if item.get("type") == "organic":
                organic.append({
                    "position": item.get("rank_absolute"),
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "domain": item.get("domain"),
                    "snippet": item.get("description", "")[:200],
                })
            elif item.get("type") == "ai_overview":
                ai_overview = {
                    "text": item.get("text", "")[:500],
                    "references": [{"url": r.get("url"), "title": r.get("title")} for r in item.get("references", [])[:5]],
                }
            elif item.get("type") == "featured_snippet":
                if not ai_overview:
                    ai_overview = {
                        "text": item.get("description", "")[:500],
                        "type": "featured_snippet",
                        "url": item.get("url"),
                    }

        return {
            "query": query,
            "has_ai_overview": ai_overview is not None,
            "ai_overview": ai_overview,
            "organic": organic[:10],
            "total_results": result.get("se_results_count"),
        }

    except Exception as e:
        return {"query": query, "error": str(e)[:100]}


def main():
    if not LOGIN or not PASSWORD:
        print("DataForSEO credentials not set.")
        print("Sign up at dataforseo.com ($1 free credit)")
        print("Set: export DATAFORSEO_LOGIN=your@email.com")
        print("Set: export DATAFORSEO_PASSWORD=your_password")
        print()
        print("To test without credentials, the data structure is ready.")
        print("The dashboard will show 'Not connected' until credentials are set.")
        return

    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    clients = CLIENTS if target == "all" else {target: CLIENTS.get(target, {})}

    all_results = {}
    for client_id, config in clients.items():
        if not config.get("queries"):
            continue

        print(f"\n{client_id}:")
        results = []

        for query in config["queries"]:
            print(f"  {query}...")
            result = fetch_serp(query)
            results.append(result)

            if result.get("has_ai_overview"):
                print(f"    AI Overview DETECTED")
            elif result.get("error"):
                print(f"    Error: {result['error']}")
            else:
                print(f"    No AI Overview")

            time.sleep(1)

        aio_count = sum(1 for r in results if r.get("has_ai_overview"))
        all_results[client_id] = {
            "checked_at": datetime.now().isoformat(),
            "total_queries": len(results),
            "ai_overviews_detected": aio_count,
            "results": results,
        }
        print(f"  AI Overviews: {aio_count}/{len(results)}")

    with open(OUTPUT, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved → {OUTPUT}")


if __name__ == "__main__":
    main()
