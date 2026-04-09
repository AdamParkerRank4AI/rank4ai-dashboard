#!/usr/bin/env python3
"""
Test Perplexity AI citations for client brands.
Perplexity searches the live web — so it SHOULD find established sites.
Uses OpenAI-compatible API with Perplexity endpoint.

Note: Needs PERPLEXITY_API_KEY or uses OpenAI key with Perplexity base URL.
If no Perplexity key, falls back to testing via the Anthropic API with
web search simulation prompts.
"""
import json
import os
from datetime import datetime

import requests

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")

# Check for Perplexity API key
PERPLEXITY_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

CLIENTS = {
    "rank4ai": {
        "brand": "Rank4AI",
        "domain": "rank4ai.co.uk",
        "queries": [
            "What are the best AI search visibility agencies in the UK?",
            "What is GEO generative engine optimization?",
            "How do I get my business found in ChatGPT?",
            "Best AI SEO agencies UK 2026",
        ],
    },
    "market-invoice": {
        "brand": "Market Invoice",
        "domain": "marketinvoice.co.uk",
        "queries": [
            "Best invoice finance companies UK",
            "Compare invoice finance providers UK",
            "How does invoice factoring work UK?",
        ],
    },
    "seocompare": {
        "brand": "SEO Compare",
        "domain": "seocompare.co.uk",
        "queries": [
            "Compare SEO agencies UK",
            "Best SEO companies UK 2026",
        ],
    },
}


def query_perplexity(query):
    """Query Perplexity API."""
    if not PERPLEXITY_KEY:
        return None

    try:
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {PERPLEXITY_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [{"role": "user", "content": query}],
                "max_tokens": 1024,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = data.get("citations", [])
            return {"text": text, "citations": citations}
        return None
    except:
        return None


def query_chatgpt_browse(query):
    """Query ChatGPT with browsing context (uses OpenAI API)."""
    if not OPENAI_KEY:
        return None

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant. When answering, include specific company names, websites, and URLs where relevant."},
                    {"role": "user", "content": query},
                ],
                "max_tokens": 1024,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"text": text, "citations": []}
        return None
    except:
        return None


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_results = {}
    models_tested = []

    if PERPLEXITY_KEY:
        models_tested.append("Perplexity")
    if OPENAI_KEY:
        models_tested.append("ChatGPT")

    if not models_tested:
        print("No API keys found. Set PERPLEXITY_API_KEY or OPENAI_API_KEY")
        return

    print(f"Testing with: {', '.join(models_tested)}")

    for client_id, config in CLIENTS.items():
        print(f"\n{config['brand']}:")
        results = []

        for query in config["queries"]:
            query_result = {"query": query, "models": {}}

            # Test Perplexity
            if PERPLEXITY_KEY:
                plex = query_perplexity(query)
                if plex:
                    text_lower = plex["text"].lower()
                    mentioned = config["brand"].lower() in text_lower or config["domain"].lower() in text_lower
                    cited_in_sources = any(config["domain"] in str(c) for c in plex.get("citations", []))
                    query_result["models"]["Perplexity"] = {
                        "mentioned": mentioned,
                        "cited_in_sources": cited_in_sources,
                        "preview": plex["text"][:300],
                        "citations": plex.get("citations", [])[:5],
                    }
                    status = "CITED" if mentioned or cited_in_sources else "not cited"
                    print(f"  Perplexity {status}: {query[:50]}")

            # Test ChatGPT
            if OPENAI_KEY:
                gpt = query_chatgpt_browse(query)
                if gpt:
                    text_lower = gpt["text"].lower()
                    mentioned = config["brand"].lower() in text_lower or config["domain"].lower() in text_lower
                    query_result["models"]["ChatGPT"] = {
                        "mentioned": mentioned,
                        "preview": gpt["text"][:300],
                    }
                    status = "CITED" if mentioned else "not cited"
                    print(f"  ChatGPT {status}: {query[:50]}")

            results.append(query_result)

        # Summarise
        summary = {}
        for model in models_tested:
            cited = sum(1 for r in results if r["models"].get(model, {}).get("mentioned") or r["models"].get(model, {}).get("cited_in_sources"))
            total = sum(1 for r in results if model in r["models"])
            summary[model] = {
                "cited": cited,
                "total": total,
                "rate": round(cited / max(total, 1) * 100, 1),
            }
            print(f"  {model}: {cited}/{total} ({summary[model]['rate']}%)")

        all_results[client_id] = {
            "brand": config["brand"],
            "tested_at": datetime.now().isoformat(),
            "models_tested": models_tested,
            "summary": summary,
            "results": results,
        }

    output_file = os.path.join(OUTPUT_DIR, "multi_model_citations.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
