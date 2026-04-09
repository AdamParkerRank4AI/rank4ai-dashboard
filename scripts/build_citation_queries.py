#!/usr/bin/env python3
"""
Build citation test queries from real data sources:
- GSC queries (what people actually search)
- Bing queries
- Site question pages (H1s that are questions)
- SERP PAA questions

Outputs query configs for check_citations_by_type.py
"""
import json
import os

LIVE_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
OUTPUT = os.path.expanduser("~/rank4ai-dashboard/src/data/live/citation_queries.json")

COMPETITOR_MAP = {
    "rank4ai": [
        "YALD", "AEO-REX", "First Answer", "Kaizen", "ClickSlice",
        "Screaming Frog", "Found", "Propeller", "CEEK", "Varn",
    ],
    "market-invoice": [
        "Close Brothers", "Bibby", "Aldermore", "HSBC", "Kriya",
        "Sonovate", "Ultimate Finance", "Skipton", "Time Finance",
        "Novuna", "Capitalise", "FundInvoice",
    ],
    "seocompare": [
        "ClickSlice", "Found", "Propeller", "Impression", "Aira",
        "Rise at Seven", "Kaizen", "Brainlabs",
    ],
}


def load(filename):
    path = os.path.join(LIVE_DIR, filename)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def build_queries(client_id):
    """Build queries from all available data sources."""
    queries = {
        "brand": [],
        "best_of": [],
        "how_to": [],
        "what_is": [],
        "comparison": [],
        "questions": [],  # From actual site question pages
        "gsc_queries": [],  # From real GSC data
    }

    # 1. Brand queries (always include)
    brand_map = {
        "rank4ai": "Rank4AI",
        "market-invoice": "Market Invoice",
        "seocompare": "SEO Compare",
    }
    brand = brand_map.get(client_id, client_id)
    queries["brand"] = [
        f"What is {brand}?",
        f"Tell me about {brand}",
    ]

    # 2. GSC queries (real search data)
    gsc = load("gsc.json").get(client_id, {})
    for q in gsc.get("top_queries", []):
        query = q.get("query", "")
        if query and len(query) > 5 and query.lower() != brand.lower():
            queries["gsc_queries"].append(query)

    # 3. Site question pages (real questions from the site content)
    crawl = load(f"crawl_{client_id}.json")
    if crawl:
        for page in crawl.get("pages", []):
            h1 = page.get("h1", "")
            if "?" in h1 and len(h1) > 15:
                # Categorise
                h1_lower = h1.lower()
                if h1_lower.startswith("how") or "how do" in h1_lower or "how to" in h1_lower:
                    queries["how_to"].append(h1)
                elif h1_lower.startswith("what") or "what is" in h1_lower:
                    queries["what_is"].append(h1)
                elif "vs" in h1_lower or "versus" in h1_lower or "compare" in h1_lower or "difference" in h1_lower:
                    queries["comparison"].append(h1)
                else:
                    queries["questions"].append(h1)

    # 4. SERP PAA (People Also Ask from Google)
    serp = load("serp_data.json").get(client_id, {})
    for result in serp.get("results", []):
        for paa in result.get("paa", []):
            if paa not in queries["questions"]:
                queries["questions"].append(paa)

    # 5. Industry best-of queries (from SERP data — what are people searching)
    serp_queries = [r.get("query", "") for r in serp.get("results", []) if r.get("query")]
    for q in serp_queries:
        q_lower = q.lower()
        if "best" in q_lower or "top" in q_lower:
            if q not in queries["best_of"]:
                queries["best_of"].append(q)
        elif "compare" in q_lower or "vs" in q_lower:
            if q not in queries["comparison"]:
                queries["comparison"].append(q)

    # Limit each category
    for cat in queries:
        queries[cat] = queries[cat][:10]

    # Remove empty categories
    queries = {k: v for k, v in queries.items() if v}

    total = sum(len(v) for v in queries.values())

    return {
        "brand": brand,
        "domain": {"rank4ai": "rank4ai.co.uk", "market-invoice": "marketinvoice.co.uk", "seocompare": "seocompare.co.uk"}.get(client_id, ""),
        "competitors": COMPETITOR_MAP.get(client_id, []),
        "query_types": queries,
        "total_queries": total,
    }


def main():
    all_configs = {}
    for client_id in ["rank4ai", "market-invoice", "seocompare"]:
        config = build_queries(client_id)
        all_configs[client_id] = config
        print(f"\n{config['brand']}:")
        print(f"  Total queries: {config['total_queries']}")
        for cat, queries in config["query_types"].items():
            print(f"  {cat}: {len(queries)}")
            for q in queries[:3]:
                print(f"    - {q[:70]}")
            if len(queries) > 3:
                print(f"    ...and {len(queries) - 3} more")

    with open(OUTPUT, "w") as f:
        json.dump(all_configs, f, indent=2)
    print(f"\nSaved → {OUTPUT}")


if __name__ == "__main__":
    main()
