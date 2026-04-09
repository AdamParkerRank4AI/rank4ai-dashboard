#!/usr/bin/env python3
"""
Extract entities and topics from client sites using Google NLP API.
Shows what Google thinks each site is about.
Free — 5,000 documents/month.
"""
import json
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
API_KEY = "AIzaSyDLOMKvg2KHpV8mw6gC-wazY49y4tCyu5s"

NLP_URL = f"https://language.googleapis.com/v1/documents:analyzeEntities?key={API_KEY}"
CLASSIFY_URL = f"https://language.googleapis.com/v1/documents:classifyText?key={API_KEY}"

SITES = {
    "rank4ai": [
        "https://www.rank4ai.co.uk/",
        "https://www.rank4ai.co.uk/ai-services",
        "https://www.rank4ai.co.uk/ai-search/framework",
    ],
    "market-invoice": [
        "https://www.marketinvoice.co.uk/",
        "https://www.marketinvoice.co.uk/guides/how-invoice-finance-works/",
        "https://www.marketinvoice.co.uk/providers/",
    ],
    "seocompare": [
        "https://www.seocompare.co.uk/",
    ],
}

HEADERS = {"User-Agent": "Rank4AI-NLP/1.0"}


def get_page_text(url):
    """Fetch page and extract visible text."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        # Limit to ~5000 chars for API
        return text[:5000]
    except:
        return None


def analyze_entities(text):
    """Extract entities using Google NLP API."""
    try:
        resp = requests.post(NLP_URL, json={
            "document": {
                "type": "PLAIN_TEXT",
                "content": text,
            },
            "encodingType": "UTF8",
        }, timeout=30)

        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

        data = resp.json()
        entities = []
        for e in data.get("entities", []):
            entities.append({
                "name": e.get("name", ""),
                "type": e.get("type", ""),
                "salience": round(e.get("salience", 0), 4),
                "mentions": len(e.get("mentions", [])),
                "wikipedia_url": e.get("metadata", {}).get("wikipedia_url", ""),
                "mid": e.get("metadata", {}).get("mid", ""),
            })

        # Sort by salience (importance)
        entities.sort(key=lambda x: x["salience"], reverse=True)
        return {"entities": entities[:30]}

    except Exception as e:
        return {"error": str(e)[:100]}


def classify_content(text):
    """Classify content into categories using Google NLP API."""
    try:
        resp = requests.post(CLASSIFY_URL, json={
            "document": {
                "type": "PLAIN_TEXT",
                "content": text,
            },
        }, timeout=30)

        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}

        data = resp.json()
        categories = []
        for c in data.get("categories", []):
            categories.append({
                "name": c.get("name", ""),
                "confidence": round(c.get("confidence", 0), 3),
            })
        return {"categories": categories}

    except Exception as e:
        return {"error": str(e)[:100]}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_results = {}
    for client_id, urls in SITES.items():
        print(f"\n{client_id}:")
        pages = []
        all_entities = {}
        all_categories = {}

        for url in urls:
            print(f"  {url}...")
            text = get_page_text(url)
            if not text:
                print(f"    Could not fetch page")
                continue

            # Extract entities
            entity_result = analyze_entities(text)
            if "entities" in entity_result:
                print(f"    Entities: {len(entity_result['entities'])}")
                for e in entity_result["entities"][:5]:
                    print(f"      {e['name']} ({e['type']}) — salience {e['salience']}")
                    # Aggregate across pages
                    key = e["name"].lower()
                    if key not in all_entities:
                        all_entities[key] = {"name": e["name"], "type": e["type"], "total_salience": 0, "pages": 0, "wikipedia": e.get("wikipedia_url", "")}
                    all_entities[key]["total_salience"] += e["salience"]
                    all_entities[key]["pages"] += 1
            else:
                print(f"    Entity error: {entity_result.get('error', 'unknown')}")

            # Classify content
            cat_result = classify_content(text)
            if "categories" in cat_result:
                print(f"    Categories: {[c['name'] for c in cat_result['categories'][:3]]}")
                for c in cat_result["categories"]:
                    if c["name"] not in all_categories:
                        all_categories[c["name"]] = {"confidence": 0, "pages": 0}
                    all_categories[c["name"]]["confidence"] += c["confidence"]
                    all_categories[c["name"]]["pages"] += 1
            else:
                print(f"    Category error: {cat_result.get('error', 'unknown')}")

            pages.append({
                "url": url,
                "entities": entity_result.get("entities", [])[:15],
                "categories": cat_result.get("categories", []),
            })

        # Top entities across all pages
        top_entities = sorted(all_entities.values(), key=lambda x: x["total_salience"], reverse=True)[:20]

        # Top categories
        top_categories = sorted(all_categories.items(), key=lambda x: x[1]["confidence"], reverse=True)

        all_results[client_id] = {
            "analyzed_at": datetime.now().isoformat(),
            "pages_analyzed": len(pages),
            "top_entities": top_entities,
            "top_categories": [{"name": n, "confidence": round(d["confidence"], 3), "pages": d["pages"]} for n, d in top_categories[:10]],
            "pages": pages,
        }

        print(f"\n  Top entities: {[e['name'] for e in top_entities[:5]]}")
        print(f"  Categories: {[c[0] for c in top_categories[:3]]}")

    output_file = os.path.join(OUTPUT_DIR, "nlp_entities.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
