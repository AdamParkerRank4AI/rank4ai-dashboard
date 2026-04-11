#!/usr/bin/env python3
"""
Contextual Knowledge Graph Analysis
Based on Dan Hinckley's approach:
1. Get top 10 ranking pages for a query (via Serper)
2. Scrape each page
3. Extract entities and classify by type
4. Build a contextual knowledge graph
5. Compare client page to the graph
6. Identify missing entity CLASSES, not just entities

Usage:
  python3 knowledge_graph_analysis.py "invoice finance UK" marketinvoice.co.uk
"""
import json
import os
import sys
import time
import re
from datetime import datetime
from collections import Counter, defaultdict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import anthropic

LIVE_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
SERPER_KEY = "28257708ebacca0e696d3cfaebda39de3496fa75"
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def get_serp_results(query, num=10):
    """Get top organic results from Serper."""
    try:
        resp = requests.post("https://google.serper.dev/search", json={
            "q": query, "gl": "gb", "num": num,
        }, headers={
            "X-API-KEY": SERPER_KEY,
            "Content-Type": "application/json",
        }, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("organic", [])
    except:
        pass
    return []


def scrape_page(url):
    """Scrape visible text from a page."""
    try:
        resp = requests.get(url, headers={"User-Agent": "Rank4AI-KG/1.0"}, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:5000]  # Cap for API cost
    except:
        return None


def extract_and_classify_entities(text, query):
    """Use Claude to extract entities and classify them by semantic type."""
    if not ANTHROPIC_KEY:
        return None

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

    prompt = f"""Analyse this text from a page ranking for "{query}". Extract all named entities and classify each into one of these semantic categories:

CATEGORIES:
- COMPANY: Business names, brands, organisations
- PERSON: Named individuals, job titles with names
- PRODUCT: Specific products, services, tools
- LOCATION: Cities, regions, countries
- REGULATION: Laws, regulations, compliance requirements, standards
- PROCESS: Methods, procedures, workflows, how things work
- FINANCIAL: Monetary amounts, rates, percentages, costs
- OUTCOME: Results, benefits, metrics, KPIs
- RISK: Risks, problems, warnings, downsides
- COMPARISON: Alternatives, competitors, "vs" relationships
- TIMEFRAME: Dates, durations, timelines
- CREDENTIAL: Qualifications, certifications, accreditations, awards
- INDUSTRY: Sector names, market segments, verticals

Output as JSON array. Each item: {{"entity": "name", "category": "CATEGORY", "context": "brief context"}}
Only output the JSON array, nothing else.

TEXT:
{text[:3000]}"""

    try:
        msg = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        response = msg.content[0].text
        # Extract JSON
        match = re.search(r'\[[\s\S]*\]', response)
        if match:
            return json.loads(match.group())
    except:
        pass
    return []


def build_knowledge_graph(query, client_domain=None):
    """Build contextual knowledge graph for a query."""
    print(f"\nQuery: {query}")

    # 1. Get top ranking pages
    print("  Getting SERP results...")
    serp = get_serp_results(query)
    if not serp:
        return {"error": "No SERP results"}

    # 2. Scrape and extract entities from each page
    all_entities = []
    page_entities = {}
    client_page = None

    for i, result in enumerate(serp[:8]):  # Top 8
        url = result.get("link", "")
        domain = urlparse(url).netloc.replace("www.", "")
        print(f"  [{i+1}] {domain}...")

        text = scrape_page(url)
        if not text:
            print(f"    Could not scrape")
            continue

        entities = extract_and_classify_entities(text, query)
        if entities:
            page_entities[domain] = entities
            all_entities.extend(entities)
            print(f"    {len(entities)} entities extracted")

            # Check if this is the client's page
            if client_domain and client_domain in domain:
                client_page = {"url": url, "domain": domain, "entities": entities}
        else:
            print(f"    No entities found")

        time.sleep(0.5)

    if not all_entities:
        return {"error": "No entities extracted"}

    # 3. Aggregate entity classes across ranking set
    class_counts = Counter()
    class_entities = defaultdict(list)
    for e in all_entities:
        cat = e.get("category", "OTHER")
        class_counts[cat] += 1
        entity_name = e.get("entity", "")
        if entity_name not in class_entities[cat]:
            class_entities[cat].append(entity_name)

    # 4. Compare client page to ranking set
    gap_analysis = None
    if client_page:
        client_classes = Counter()
        for e in client_page["entities"]:
            client_classes[e.get("category", "OTHER")] += 1

        # Find missing classes
        missing_classes = []
        weak_classes = []
        for cat, count in class_counts.most_common():
            avg_per_page = count / len(page_entities)
            client_count = client_classes.get(cat, 0)
            if client_count == 0 and avg_per_page >= 2:
                missing_classes.append({
                    "category": cat,
                    "avg_in_ranking_set": round(avg_per_page, 1),
                    "examples": class_entities[cat][:5],
                })
            elif client_count < avg_per_page * 0.5 and avg_per_page >= 2:
                weak_classes.append({
                    "category": cat,
                    "client_count": client_count,
                    "avg_in_ranking_set": round(avg_per_page, 1),
                    "examples": class_entities[cat][:5],
                })

        gap_analysis = {
            "client_domain": client_domain,
            "client_entity_count": len(client_page["entities"]),
            "avg_entity_count": round(sum(len(e) for e in page_entities.values()) / len(page_entities), 1),
            "missing_classes": missing_classes,
            "weak_classes": weak_classes,
        }

    return {
        "query": query,
        "analysed_at": datetime.now().isoformat(),
        "pages_analysed": len(page_entities),
        "total_entities": len(all_entities),
        "entity_classes": {cat: {"count": count, "examples": class_entities[cat][:5]} for cat, count in class_counts.most_common()},
        "dominant_classes": [cat for cat, _ in class_counts.most_common(5)],
        "gap_analysis": gap_analysis,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 knowledge_graph_analysis.py <query> [client_domain]")
        print("Example: python3 knowledge_graph_analysis.py 'invoice finance UK' marketinvoice.co.uk")
        return

    query = sys.argv[1]
    client_domain = sys.argv[2] if len(sys.argv) > 2 else None

    result = build_knowledge_graph(query, client_domain)

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print(f"\n{'='*50}")
    print(f"Knowledge Graph for: {query}")
    print(f"{'='*50}")
    print(f"Pages analysed: {result['pages_analysed']}")
    print(f"Total entities: {result['total_entities']}")
    print(f"Dominant entity classes:")
    for cat, data in result["entity_classes"].items():
        print(f"  {cat}: {data['count']} ({', '.join(data['examples'][:3])})")

    if result.get("gap_analysis"):
        ga = result["gap_analysis"]
        print(f"\nGap Analysis for {ga['client_domain']}:")
        print(f"  Client entities: {ga['client_entity_count']} vs avg {ga['avg_entity_count']}")
        if ga["missing_classes"]:
            print(f"  MISSING classes:")
            for mc in ga["missing_classes"]:
                print(f"    {mc['category']}: avg {mc['avg_in_ranking_set']} in ranking set, you have 0")
                print(f"      Examples: {', '.join(mc['examples'][:3])}")
        if ga["weak_classes"]:
            print(f"  WEAK classes:")
            for wc in ga["weak_classes"]:
                print(f"    {wc['category']}: you have {wc['client_count']}, avg is {wc['avg_in_ranking_set']}")

    # Save result
    output = os.path.join(LIVE_DIR, "knowledge_graph_analysis.json")
    if os.path.exists(output):
        with open(output) as f:
            existing = json.load(f)
    else:
        existing = {}

    key = query.replace(" ", "_")[:50]
    existing[key] = result
    with open(output, "w") as f:
        json.dump(existing, f, indent=2)
    print(f"\nSaved → {output}")


if __name__ == "__main__":
    main()
