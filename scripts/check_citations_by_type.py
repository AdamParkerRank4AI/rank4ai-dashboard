#!/usr/bin/env python3
"""
Check AI citations broken down by query type — matched to page categories.
Tests which types of queries trigger citations for the brand.
"""
import json
import os
from datetime import datetime

import anthropic

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")

CLIENTS = {
    "rank4ai": {
        "brand": "Rank4AI",
        "domain": "rank4ai.co.uk",
        "competitors": ["YALD", "AEO-REX", "First Answer", "Kaizen", "ClickSlice", "Screaming Frog"],
        "query_types": {
            "brand": [
                "What is Rank4AI?",
                "Tell me about Rank4AI",
            ],
            "best_of": [
                "Best AI search visibility agencies UK",
                "Top AI SEO agencies in the UK 2026",
                "Best GEO agencies UK",
            ],
            "how_to": [
                "How do I get my business found in ChatGPT?",
                "How to optimise for AI search engines",
                "How to get cited by Perplexity AI",
                "How to create an llms.txt file",
            ],
            "what_is": [
                "What is AI search visibility?",
                "What is GEO generative engine optimization?",
                "What is AEO answer engine optimization?",
                "What is the difference between SEO and GEO?",
            ],
            "comparison": [
                "SEO vs GEO which is more important?",
                "Traditional SEO vs AI search optimization",
                "Compare AI search agencies UK",
            ],
            "cost": [
                "How much does AI search optimisation cost UK?",
                "AI SEO agency pricing UK",
            ],
            "local": [
                "AI search agencies London",
                "AI SEO services near me UK",
            ],
        },
    },
    "market-invoice": {
        "brand": "Market Invoice",
        "domain": "marketinvoice.co.uk",
        "competitors": ["Close Brothers", "Bibby", "Aldermore", "HSBC", "Kriya", "Sonovate"],
        "query_types": {
            "brand": [
                "What is Market Invoice?",
                "Tell me about marketinvoice.co.uk",
            ],
            "best_of": [
                "Best invoice finance companies UK",
                "Top invoice factoring providers UK",
                "Best invoice finance for small business UK",
            ],
            "how_to": [
                "How does invoice finance work UK?",
                "How to get set up with invoice factoring",
                "How to choose an invoice finance provider",
            ],
            "what_is": [
                "What is invoice factoring?",
                "What is confidential invoice discounting?",
                "What is selective invoice finance?",
            ],
            "comparison": [
                "Compare invoice finance providers UK",
                "Invoice finance vs business loan",
                "Factoring vs invoice discounting difference",
                "Close Brothers vs Bibby invoice finance",
            ],
            "cost": [
                "How much does invoice finance cost UK?",
                "Invoice finance rates and fees UK",
            ],
            "industry": [
                "Invoice finance for recruitment agencies UK",
                "Construction invoice finance UK",
                "Invoice finance for NHS suppliers",
            ],
            "location": [
                "Invoice finance Manchester",
                "Invoice factoring London",
                "Invoice finance Birmingham",
            ],
        },
    },
    "seocompare": {
        "brand": "SEO Compare",
        "domain": "seocompare.co.uk",
        "competitors": ["ClickSlice", "Found", "Propeller", "Aira", "Rise at Seven", "Impression"],
        "query_types": {
            "brand": [
                "What is SEO Compare?",
            ],
            "best_of": [
                "Best SEO agencies UK 2026",
                "Top rated SEO companies UK",
            ],
            "how_to": [
                "How to choose an SEO agency UK",
                "How to compare SEO companies",
            ],
            "what_is": [
                "What should I look for in an SEO agency?",
                "What is technical SEO?",
            ],
            "comparison": [
                "Compare SEO agencies UK",
                "Freelance SEO vs agency which is better?",
            ],
        },
    },
}


def check_query(api_client, query, brand, domain, competitors):
    """Query Claude and check for brand + competitor mentions."""
    try:
        message = api_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": query}],
        )
        response = message.content[0].text
        response_lower = response.lower()
        brand_lower = brand.lower()
        domain_lower = domain.lower()

        brand_mentioned = brand_lower in response_lower or domain_lower in response_lower

        competitor_mentions = []
        for comp in competitors:
            if comp.lower() in response_lower:
                competitor_mentions.append(comp)

        return {
            "query": query,
            "brand_mentioned": brand_mentioned,
            "competitors_mentioned": competitor_mentions,
            "response_preview": response[:300],
        }
    except Exception as e:
        return {"query": query, "brand_mentioned": False, "error": str(e)[:100]}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not set")
        return

    api_client = anthropic.Anthropic(api_key=api_key)
    all_results = {}

    for client_id, config in CLIENTS.items():
        print(f"\n{'='*50}")
        print(f"{config['brand']}")
        print(f"{'='*50}")

        type_results = {}
        total_cited = 0
        total_queries = 0

        for query_type, queries in config["query_types"].items():
            print(f"\n  [{query_type.upper()}]")
            results = []

            for query in queries:
                result = check_query(api_client, query, config["brand"], config["domain"], config["competitors"])
                results.append(result)
                total_queries += 1

                status = "CITED" if result.get("brand_mentioned") else "not cited"
                comps = ", ".join(result.get("competitors_mentioned", [])[:3])
                comp_str = f" | Competitors: {comps}" if comps else ""
                print(f"    {status}: {query[:50]}...{comp_str}")

                if result.get("brand_mentioned"):
                    total_cited += 1

            cited_in_type = sum(1 for r in results if r.get("brand_mentioned"))
            type_results[query_type] = {
                "queries": len(queries),
                "cited": cited_in_type,
                "rate": round(cited_in_type / max(len(queries), 1) * 100, 1),
                "results": results,
            }

        overall_rate = round(total_cited / max(total_queries, 1) * 100, 1)

        # Aggregate competitor data
        all_comps = {}
        for qt in type_results.values():
            for r in qt["results"]:
                for c in r.get("competitors_mentioned", []):
                    all_comps[c] = all_comps.get(c, 0) + 1
        top_comps = sorted(all_comps.items(), key=lambda x: -x[1])

        all_results[client_id] = {
            "brand": config["brand"],
            "tested_at": datetime.now().isoformat(),
            "total_queries": total_queries,
            "total_cited": total_cited,
            "overall_rate": overall_rate,
            "by_type": type_results,
            "top_competitors": [{"name": n, "mentions": c} for n, c in top_comps[:10]],
        }

        print(f"\n  Overall: {total_cited}/{total_queries} ({overall_rate}%)")
        print(f"  By type:")
        for qt, data in type_results.items():
            print(f"    {qt}: {data['cited']}/{data['queries']} ({data['rate']}%)")

    output_file = os.path.join(OUTPUT_DIR, "citations_by_type.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
