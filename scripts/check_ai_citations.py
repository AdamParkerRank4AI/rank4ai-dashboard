#!/usr/bin/env python3
"""
Check AI citation visibility for client brands.
Uses Claude API to test if brands are mentioned in AI responses.
Outputs JSON for the dashboard.
"""

import json
import os
from datetime import datetime

import anthropic

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")

BRANDS = {
    "rank4ai": {
        "name": "Rank4AI",
        "domain": "rank4ai.co.uk",
        "queries": [
            "What are the best AI search visibility agencies in the UK?",
            "How can I optimise my website for ChatGPT and AI search?",
            "What is GEO generative engine optimization?",
            "Who offers AI SEO services in the UK?",
            "What tools help track AI search visibility?",
            "What is AI search optimization and who does it?",
            "Best agencies for getting found in AI Overviews UK",
            "How do I get my business mentioned by ChatGPT?",
        ],
    },
    "market-invoice": {
        "name": "Market Invoice",
        "domain": "marketinvoice.co.uk",
        "queries": [
            "What is invoice finance UK?",
            "Best invoice financing companies UK",
            "How does invoice factoring work?",
            "Compare invoice finance providers UK",
            "What is the difference between factoring and invoice discounting?",
        ],
    },
}


def check_citation(client, query, brand_name, domain):
    """Ask Claude a question and check if the brand is mentioned."""
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": query}
            ],
        )
        response_text = message.content[0].text

        # Check for mentions
        text_lower = response_text.lower()
        brand_lower = brand_name.lower()
        domain_lower = domain.lower()

        mentioned = brand_lower in text_lower or domain_lower in text_lower

        # Position (rough — where in the response)
        position = None
        if mentioned:
            idx = text_lower.find(brand_lower)
            if idx == -1:
                idx = text_lower.find(domain_lower)
            # Position as percentage through the response
            position = round(idx / max(len(text_lower), 1) * 100)

        # Count mentions
        mention_count = text_lower.count(brand_lower) + text_lower.count(domain_lower)

        return {
            "query": query,
            "model": "claude-sonnet-4-20250514",
            "mentioned": mentioned,
            "mention_count": mention_count,
            "position_pct": position,
            "response_length": len(response_text),
            "response_preview": response_text[:200],
            "checked_at": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "query": query,
            "model": "claude-sonnet-4-20250514",
            "mentioned": False,
            "error": str(e)[:100],
            "checked_at": datetime.now().isoformat(),
        }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not set")
        return

    client = anthropic.Anthropic(api_key=api_key)

    all_results = {}

    for site_id, config in BRANDS.items():
        print(f"\nChecking AI citations for {config['name']}...")
        results = []

        for query in config["queries"]:
            print(f"  Query: {query[:60]}...")
            result = check_citation(client, query, config["name"], config["domain"])
            results.append(result)
            print(f"    → {'CITED' if result.get('mentioned') else 'not cited'}")

        cited_count = sum(1 for r in results if r.get("mentioned"))
        total = len(results)

        all_results[site_id] = {
            "brand": config["name"],
            "domain": config["domain"],
            "checked_at": datetime.now().isoformat(),
            "total_queries": total,
            "cited_count": cited_count,
            "citation_rate": round(cited_count / max(total, 1) * 100, 1),
            "results": results,
        }

        print(f"  Citation rate: {cited_count}/{total} ({all_results[site_id]['citation_rate']}%)")

    output_file = os.path.join(OUTPUT_DIR, "ai_citations.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
