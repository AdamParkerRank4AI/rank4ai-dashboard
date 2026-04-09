#!/usr/bin/env python3
"""
Fetch real Google SERP data via Serper.dev API.
Shows: organic rankings, AI Overviews, PAA, featured snippets, Knowledge Panels.
Free — 2,500 searches/month.
"""
import json
import os
import time
from datetime import datetime

import requests

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
SERPER_API_KEY = "28257708ebacca0e696d3cfaebda39de3496fa75"

CLIENTS = {
    "rank4ai": {
        "brand": "Rank4AI",
        "domain": "rank4ai.co.uk",
        "queries": [
            "AI search visibility agency UK",
            "best AI SEO agencies UK",
            "GEO agency UK",
            "what is AI search visibility",
            "how to get found in ChatGPT",
            "AI search audit UK",
            "generative engine optimization UK",
            "AI overviews optimization UK",
            "best GEO agencies UK 2026",
            "llms.txt what is it",
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
            "confidential invoice discounting UK",
            "invoice finance costs UK",
            "best construction invoice finance UK",
            "invoice finance vs business loan",
            "selective invoice finance UK",
        ],
    },
    "seocompare": {
        "brand": "SEO Compare",
        "domain": "seocompare.co.uk",
        "queries": [
            "compare SEO agencies UK",
            "best SEO companies UK 2026",
            "SEO agency comparison tool",
            "how to choose an SEO agency UK",
            "top rated SEO services UK",
        ],
    },
}

SERPER_URL = "https://google.serper.dev/search"


def search_query(query):
    """Search Google via Serper API."""
    try:
        resp = requests.post(SERPER_URL, json={
            "q": query,
            "gl": "gb",
            "hl": "en",
            "num": 10,
        }, headers={
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json",
        }, timeout=15)

        if resp.status_code != 200:
            return {"query": query, "error": f"HTTP {resp.status_code}: {resp.text[:100]}"}

        data = resp.json()

        # AI Overview
        ai_overview = None
        if "aiOverview" in data:
            ai_overview = {
                "text": data["aiOverview"].get("text", "")[:500],
                "sources": [{"title": s.get("title", ""), "link": s.get("link", "")} for s in data["aiOverview"].get("references", data["aiOverview"].get("sources", []))[:5]],
            }
        elif "answerBox" in data:
            ai_overview = {
                "text": data["answerBox"].get("snippet", data["answerBox"].get("answer", ""))[:500],
                "sources": [{"title": data["answerBox"].get("title", ""), "link": data["answerBox"].get("link", "")}] if data["answerBox"].get("link") else [],
                "type": "answer_box",
            }

        # Organic results
        organic = []
        for r in data.get("organic", []):
            organic.append({
                "position": r.get("position", 0),
                "title": r.get("title", ""),
                "link": r.get("link", ""),
                "domain": r.get("link", "").split("/")[2] if r.get("link") else "",
                "snippet": r.get("snippet", "")[:200],
            })

        # People Also Ask
        paa = [q.get("question", "") for q in data.get("peopleAlsoAsk", [])]

        # Knowledge Graph
        kg = None
        if "knowledgeGraph" in data:
            kg_data = data["knowledgeGraph"]
            kg = {
                "title": kg_data.get("title", ""),
                "type": kg_data.get("type", ""),
                "description": kg_data.get("description", ""),
            }

        # Related searches
        related = [r.get("query", "") for r in data.get("relatedSearches", [])]

        # SERP features present
        features = []
        if ai_overview:
            features.append("AI Overview" if ai_overview.get("type") != "answer_box" else "Answer Box")
        if paa:
            features.append("People Also Ask")
        if kg:
            features.append("Knowledge Graph")
        if data.get("images"):
            features.append("Images")
        if data.get("videos"):
            features.append("Videos")
        if data.get("topStories"):
            features.append("Top Stories")
        if data.get("places"):
            features.append("Local Pack")
        if data.get("shopping"):
            features.append("Shopping")

        return {
            "query": query,
            "ai_overview": ai_overview,
            "has_ai_overview": ai_overview is not None,
            "organic": organic[:10],
            "paa": paa[:5],
            "knowledge_graph": kg,
            "related_searches": related[:5],
            "serp_features": features,
            "total_results": data.get("searchInformation", {}).get("totalResults"),
        }

    except Exception as e:
        return {"query": query, "error": str(e)[:100]}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_results = {}
    for client_id, config in CLIENTS.items():
        print(f"\n{'='*50}")
        print(f"{config['brand']}")
        print(f"{'='*50}")

        results = []
        brand_in_organic = 0
        brand_in_ai_overview = 0
        queries_with_ai_overview = 0

        for query in config["queries"]:
            time.sleep(1)  # Rate limit
            result = search_query(query)
            results.append(result)

            if "error" in result:
                print(f"  ERROR: {query[:40]} — {result['error']}")
                continue

            # Check if brand appears in organic
            brand_organic_pos = None
            for r in result.get("organic", []):
                if config["domain"] in r.get("link", ""):
                    brand_organic_pos = r["position"]
                    brand_in_organic += 1
                    break

            # Check if brand appears in AI Overview
            brand_in_aio = False
            aio = result.get("ai_overview")
            if aio:
                queries_with_ai_overview += 1
                aio_text = (aio.get("text", "") + " ".join(s.get("link", "") for s in aio.get("sources", []))).lower()
                if config["domain"].lower() in aio_text or config["brand"].lower() in aio_text:
                    brand_in_aio = True
                    brand_in_ai_overview += 1

            result["brand_organic_position"] = brand_organic_pos
            result["brand_in_ai_overview"] = brand_in_aio

            # Display
            features = ", ".join(result.get("serp_features", []))
            pos_str = f"#{brand_organic_pos}" if brand_organic_pos else "Not ranked"
            aio_str = "IN AI Overview" if brand_in_aio else ("AI Overview (not cited)" if aio else "No AI Overview")
            print(f"  {pos_str} | {aio_str} | {query[:50]}")
            if features:
                print(f"    Features: {features}")

        total = len([r for r in results if "error" not in r])
        all_results[client_id] = {
            "brand": config["brand"],
            "domain": config["domain"],
            "checked_at": datetime.now().isoformat(),
            "total_queries": total,
            "brand_in_organic": brand_in_organic,
            "organic_rate": round(brand_in_organic / max(total, 1) * 100, 1),
            "queries_with_ai_overview": queries_with_ai_overview,
            "brand_in_ai_overview": brand_in_ai_overview,
            "ai_overview_rate": round(brand_in_ai_overview / max(queries_with_ai_overview, 1) * 100, 1) if queries_with_ai_overview else 0,
            "results": results,
        }

        print(f"\n  Organic: {brand_in_organic}/{total} ({round(brand_in_organic/max(total,1)*100,1)}%)")
        print(f"  AI Overviews: {queries_with_ai_overview}/{total} queries had one")
        print(f"  In AI Overview: {brand_in_ai_overview}/{queries_with_ai_overview}")

    output_file = os.path.join(OUTPUT_DIR, "serp_data.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
