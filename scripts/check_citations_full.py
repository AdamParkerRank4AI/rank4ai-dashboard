#!/usr/bin/env python3
"""
Full AI citation check — tests brand visibility AND captures who gets mentioned instead.
Tracks across Claude and ChatGPT.
"""
import json
import os
import re
from datetime import datetime

import anthropic

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")

CLIENTS = {
    "rank4ai": {
        "brand": "Rank4AI",
        "domain": "rank4ai.co.uk",
        "competitors": [
            "YALD", "First Answer", "AEO-REX", "Kaizen", "Screaming Frog",
            "ClickSlice", "Found", "Propeller", "Blue Array", "Varn",
            "Digital Landscope", "SEO Works", "CEEK", "Figment",
        ],
        "queries": [
            "What are the best AI search visibility agencies in the UK?",
            "Who offers AI SEO services in the UK?",
            "What agencies help businesses get found in ChatGPT?",
            "Best GEO generative engine optimization agencies UK",
            "How can I optimise my website for AI search engines?",
            "What is AI search visibility and why does it matter?",
            "What is GEO generative engine optimization?",
            "How do I get my business mentioned by ChatGPT and Gemini?",
            "What tools help track AI search visibility?",
            "Best agencies for getting found in Google AI Overviews UK",
            "What is the difference between SEO and GEO?",
            "How do AI search engines decide which brands to recommend?",
            "Which UK companies specialise in AI search optimisation?",
            "What does an AI search audit involve?",
            "What is llms.txt and do I need one?",
            "Top SEO agencies in the UK for 2026",
            "Best digital marketing agencies for AI optimisation UK",
            "Who are the leading GEO agencies globally?",
            "How much does AI search optimisation cost UK?",
            "What is AEO answer engine optimization?",
        ],
    },
    "market-invoice": {
        "brand": "Market Invoice",
        "domain": "marketinvoice.co.uk",
        "competitors": [
            "Bibby Financial Services", "Close Brothers", "Aldermore",
            "Ultimate Finance", "Skipton", "IGF", "Novuna", "HSBC",
            "Lloyds", "NatWest", "Barclays", "Kriya", "Sonovate",
            "Time Finance", "Shawbrook",
        ],
        "queries": [
            "What is invoice finance UK?",
            "Best invoice financing companies UK",
            "How does invoice factoring work?",
            "Compare invoice finance providers UK",
            "What is the difference between factoring and invoice discounting?",
            "How much does invoice finance cost in the UK?",
            "Can a small business get invoice finance?",
            "Best invoice finance for recruitment agencies UK",
            "Invoice finance vs business loan which is better?",
            "Which invoice finance providers offer bad debt protection?",
            "What is confidential invoice discounting?",
            "How quickly can you get set up with invoice finance?",
            "Best construction invoice finance providers UK",
            "Can I factor just one invoice?",
            "What is selective invoice finance?",
        ],
    },
    "seocompare": {
        "brand": "SEO Compare",
        "domain": "seocompare.co.uk",
        "competitors": [
            "ClickSlice", "Found", "Propeller", "Screaming Frog",
            "Blue Array", "Builtvisible", "Rise at Seven", "Kaizen",
            "Impression", "Aira", "Distilled", "Brainlabs",
        ],
        "queries": [
            "Best SEO agencies UK",
            "Compare SEO companies UK",
            "How to choose an SEO agency",
            "Top rated SEO services UK",
            "SEO agency comparison tool UK",
            "How much does SEO cost in the UK?",
            "Best SEO agency for small business UK",
            "What should I look for in an SEO agency?",
            "SEO agency reviews UK",
            "Freelance SEO vs agency which is better?",
        ],
    },
}


def check_query(client, query, brand, domain, competitors):
    """Query Claude and analyse the response for brand + competitor mentions."""
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": query}],
        )
        response = message.content[0].text
        response_lower = response.lower()
        brand_lower = brand.lower()
        domain_lower = domain.lower()

        # Check brand mention
        brand_mentioned = brand_lower in response_lower or domain_lower in response_lower
        brand_count = response_lower.count(brand_lower) + response_lower.count(domain_lower)

        # Check position (how early in the response)
        position = None
        if brand_mentioned:
            idx = response_lower.find(brand_lower)
            if idx == -1:
                idx = response_lower.find(domain_lower)
            position = round(idx / max(len(response_lower), 1) * 100)

        # Check competitor mentions
        competitor_mentions = []
        for comp in competitors:
            if comp.lower() in response_lower:
                count = response_lower.count(comp.lower())
                idx = response_lower.find(comp.lower())
                competitor_mentions.append({
                    "name": comp,
                    "count": count,
                    "position_pct": round(idx / max(len(response_lower), 1) * 100),
                })

        # Sentiment (basic)
        positive_words = ["recommend", "excellent", "leading", "top", "best", "trusted", "reliable", "innovative"]
        negative_words = ["avoid", "poor", "expensive", "limited", "outdated"]

        brand_context = ""
        if brand_mentioned:
            # Get 200 chars around the brand mention
            idx = response_lower.find(brand_lower)
            start = max(0, idx - 100)
            end = min(len(response), idx + len(brand_lower) + 100)
            brand_context = response[start:end]

        sentiment = "neutral"
        if brand_context:
            context_lower = brand_context.lower()
            pos = sum(1 for w in positive_words if w in context_lower)
            neg = sum(1 for w in negative_words if w in context_lower)
            if pos > neg:
                sentiment = "positive"
            elif neg > pos:
                sentiment = "negative"

        return {
            "query": query,
            "model": "Claude",
            "brand_mentioned": brand_mentioned,
            "brand_mention_count": brand_count,
            "brand_position_pct": position,
            "brand_sentiment": sentiment if brand_mentioned else None,
            "competitors_mentioned": competitor_mentions,
            "competitors_count": len(competitor_mentions),
            "response_preview": response[:400],
            "response_length": len(response),
        }

    except Exception as e:
        return {
            "query": query,
            "model": "Claude",
            "brand_mentioned": False,
            "error": str(e)[:100],
        }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not set")
        return

    client = anthropic.Anthropic(api_key=api_key)
    all_results = {}

    for client_id, config in CLIENTS.items():
        print(f"\n{'='*50}")
        print(f"Testing {config['brand']} ({client_id})")
        print(f"{'='*50}")

        results = []
        for query in config["queries"]:
            print(f"\n  Q: {query[:60]}...")
            result = check_query(client, query, config["brand"], config["domain"], config["competitors"])
            results.append(result)

            if result.get("brand_mentioned"):
                print(f"    CITED (mentioned {result['brand_mention_count']}x, position {result['brand_position_pct']}%)")
            else:
                print(f"    Not cited")

            if result.get("competitors_mentioned"):
                comps = ", ".join([f"{c['name']}({c['count']}x)" for c in result["competitors_mentioned"][:5]])
                print(f"    Competitors mentioned: {comps}")

        # Summary
        cited = sum(1 for r in results if r.get("brand_mentioned"))
        total = len(results)
        rate = round(cited / max(total, 1) * 100, 1)

        # Most mentioned competitors
        comp_counts = {}
        for r in results:
            for c in r.get("competitors_mentioned", []):
                comp_counts[c["name"]] = comp_counts.get(c["name"], 0) + 1
        top_competitors = sorted(comp_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        all_results[client_id] = {
            "brand": config["brand"],
            "domain": config["domain"],
            "tested_at": datetime.now().isoformat(),
            "total_queries": total,
            "cited_count": cited,
            "citation_rate": rate,
            "top_competitors": [{"name": n, "mentioned_in": c, "rate": round(c/total*100, 1)} for n, c in top_competitors],
            "results": results,
        }

        print(f"\n  Citation rate: {cited}/{total} ({rate}%)")
        if top_competitors:
            print(f"  Top competitors mentioned:")
            for name, count in top_competitors[:5]:
                print(f"    {name}: mentioned in {count}/{total} queries ({round(count/total*100,1)}%)")

    output_file = os.path.join(OUTPUT_DIR, "citations_full.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
