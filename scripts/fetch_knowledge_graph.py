#!/usr/bin/env python3
"""
Check Google Knowledge Graph for client entities.
Free — 500 requests/day, no auth needed (just API key).
"""
import json
import os
from datetime import datetime

import requests

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
API_KEY = "AIzaSyDLOMKvg2KHpV8mw6gC-wazY49y4tCyu5s"

CLIENTS = {
    "rank4ai": {
        "queries": ["Rank4AI", "Rank4AI Ltd", "Adam Parker Rank4AI"],
    },
    "market-invoice": {
        "queries": ["Market Invoice", "marketinvoice.co.uk", "Best Business Loans Ltd"],
    },
    "seocompare": {
        "queries": ["SEO Compare", "seocompare.co.uk"],
    },
}

KG_URL = "https://kgsearch.googleapis.com/v1/entities:search"


def search_entity(query):
    """Search Knowledge Graph for an entity."""
    try:
        resp = requests.get(KG_URL, params={
            "query": query,
            "key": API_KEY,
            "limit": 5,
            "languages": "en",
        }, timeout=15)

        if resp.status_code != 200:
            return {"query": query, "error": f"HTTP {resp.status_code}"}

        data = resp.json()
        items = data.get("itemListElement", [])

        results = []
        for item in items:
            entity = item.get("result", {})
            results.append({
                "name": entity.get("name", ""),
                "type": entity.get("@type", []),
                "description": entity.get("description", ""),
                "detailed_description": entity.get("detailedDescription", {}).get("articleBody", "")[:300],
                "url": entity.get("detailedDescription", {}).get("url", ""),
                "image": entity.get("image", {}).get("contentUrl", ""),
                "score": item.get("resultScore", 0),
            })

        return {
            "query": query,
            "found": len(results) > 0,
            "count": len(results),
            "results": results,
        }

    except Exception as e:
        return {"query": query, "error": str(e)[:100]}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_results = {}
    for client_id, config in CLIENTS.items():
        print(f"\n{client_id}:")
        client_results = []

        for query in config["queries"]:
            result = search_entity(query)
            client_results.append(result)

            if result.get("found"):
                top = result["results"][0]
                print(f"  '{query}' → FOUND: {top['name']} ({', '.join(top['type'])}) — score {top['score']}")
            else:
                print(f"  '{query}' → NOT FOUND in Knowledge Graph")

        # Is the brand a known entity?
        brand_found = any(r.get("found") for r in client_results)
        best_match = None
        if brand_found:
            for r in client_results:
                if r.get("found"):
                    for entity in r["results"]:
                        if not best_match or entity["score"] > best_match["score"]:
                            best_match = entity

        all_results[client_id] = {
            "checked_at": datetime.now().isoformat(),
            "is_known_entity": brand_found,
            "best_match": best_match,
            "queries": client_results,
        }

        status = "KNOWN ENTITY" if brand_found else "NOT a known entity"
        print(f"  Status: {status}")

    output_file = os.path.join(OUTPUT_DIR, "knowledge_graph.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
