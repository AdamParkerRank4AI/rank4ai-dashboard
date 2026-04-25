#!/usr/bin/env python3
"""
Run baseline citation tests — top 5 per category across Claude + ChatGPT + Gemini + Perplexity.
Single system, one output file, all 4 models.
"""
import json
import os
import re
import time
from collections import Counter
from datetime import datetime

import anthropic
import requests

LIVE_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
OUTPUT = os.path.join(LIVE_DIR, "citation_results.json")

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
PERPLEXITY_KEY = os.environ.get("PERPLEXITY_API_KEY", "")

CATEGORIES = ["brand", "industry", "best_of", "how_to", "what_is", "comparison", "cost", "local", "question", "review", "problem", "recommendation"]
TOP_N = 5

# Regex patterns for extracting domains from AI response text
_URL_PATTERN = re.compile(r'https?://([^\s<>"\')\]]+)', re.IGNORECASE)
_DOMAIN_PATTERN = re.compile(r'(?<![/@\w])(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+(?:co\.uk|org\.uk|ac\.uk|com|org|net|io|ai|dev|info|biz|edu|gov)\b', re.IGNORECASE)
# Domains to ignore (generic platforms, not meaningful competitors)
_IGNORE_DOMAINS = {
    "example.com", "example.org", "example.net",
    "google.com", "youtube.com", "wikipedia.org", "en.wikipedia.org",
    "github.com", "linkedin.com", "twitter.com", "x.com",
    "facebook.com", "instagram.com", "reddit.com",
    "api.openai.com", "openai.com", "anthropic.com", "perplexity.ai",
    "generativelanguage.googleapis.com",
}


def extract_domains(text):
    """Extract all unique domains cited in AI response text."""
    if not text:
        return []
    domains = set()

    # Extract domains from full URLs (https://foo.com/bar -> foo.com)
    for match in _URL_PATTERN.findall(text):
        domain = match.split("/")[0].split(":")[0].lower().strip(".")
        if domain and domain not in _IGNORE_DOMAINS:
            domains.add(domain)

    # Extract bare domain mentions (e.g. "semrush.com" without http)
    for match in _DOMAIN_PATTERN.findall(text):
        domain = match.lower().strip(".")
        if domain and domain not in _IGNORE_DOMAINS:
            domains.add(domain)

    return sorted(domains)


def load_prompts():
    with open(os.path.join(LIVE_DIR, "citation_prompts.json")) as f:
        return json.load(f)


def test_claude(query):
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1024,
            messages=[{"role": "user", "content": query}],
        )
        return msg.content[0].text
    except Exception as e:
        return None


def test_chatgpt(query):
    try:
        resp = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "max_tokens": 1024, "messages": [{"role": "user", "content": query}]},
            timeout=30)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
    except:
        pass
    return None


def test_gemini(query):
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": query}]}], "generationConfig": {"maxOutputTokens": 1024}},
            timeout=30)
        if resp.status_code == 200:
            return resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    except:
        pass
    return None


def test_perplexity(query):
    try:
        resp = requests.post("https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {PERPLEXITY_KEY}", "Content-Type": "application/json"},
            json={"model": "sonar-pro", "max_tokens": 1024, "messages": [{"role": "user", "content": query}]},
            timeout=30)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
    except:
        pass
    return None


def check_cited(text, brand, domain):
    if not text:
        return {"cited": False, "error": True, "competitors_cited": []}
    text_lower = text.lower()
    cited = brand.lower() in text_lower or domain.lower() in text_lower

    # Extract all domains mentioned in the response (excluding the client's own domain)
    all_domains = extract_domains(text)
    competitors = [d for d in all_domains if d != domain.lower()]

    return {"cited": cited, "preview": text[:300], "competitors_cited": competitors}


def run_client(client_id, config):
    brand = {"rank4ai": "Rank4AI", "market-invoice": "Market Invoice", "seocompare": "SEO Compare"}.get(client_id, client_id)
    domain = {"rank4ai": "rank4ai.co.uk", "market-invoice": "marketinvoice.co.uk", "seocompare": "seocompare.co.uk"}.get(client_id, "")

    # Collect all prompts by category
    all_prompts = []
    for group in ["high_intent", "discovery", "faq"]:
        for p in config.get(group, []):
            all_prompts.append(p)

    # Group by type
    by_category = {}
    for p in all_prompts:
        cat = p.get("type", "other")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(p)

    # Take top N per category
    baseline_prompts = []
    for cat in CATEGORIES:
        prompts = by_category.get(cat, [])
        baseline_prompts.extend(prompts[:TOP_N])

    # Also always include brand prompts
    brand_prompts = by_category.get("brand", [])
    for p in brand_prompts:
        if p not in baseline_prompts:
            baseline_prompts.append(p)

    print(f"\n{brand}: testing {len(baseline_prompts)} baseline prompts across 4 models")

    category_results = {}
    all_results = []

    for p in baseline_prompts:
        query = p["query"]
        cat = p.get("type", "other")
        print(f"  [{cat}] {query[:50]}...")

        # Test all 4 models
        claude_text = test_claude(query)
        chatgpt_text = test_chatgpt(query)
        gemini_text = test_gemini(query)
        perplexity_text = test_perplexity(query)

        result = {
            "id": p.get("id", ""),
            "query": query,
            "type": cat,
            "source": p.get("source", ""),
            "page_url": p.get("page_url", ""),
            "claude": check_cited(claude_text, brand, domain),
            "chatgpt": check_cited(chatgpt_text, brand, domain),
            "gemini": check_cited(gemini_text, brand, domain),
            "perplexity": check_cited(perplexity_text, brand, domain),
            "tested_at": datetime.now().isoformat(),
        }

        # Print result
        c = "Y" if result["claude"]["cited"] else "N"
        g = "Y" if result["chatgpt"]["cited"] else "N"
        gm = "Y" if result["gemini"]["cited"] else "N"
        px = "Y" if result["perplexity"]["cited"] else "N"
        print(f"    C:{c} G:{g} Gm:{gm} Px:{px}")

        all_results.append(result)

        # Aggregate by category
        if cat not in category_results:
            category_results[cat] = {"total": 0, "claude": 0, "chatgpt": 0, "gemini": 0, "perplexity": 0}
        category_results[cat]["total"] += 1
        if result["claude"]["cited"]:
            category_results[cat]["claude"] += 1
        if result["chatgpt"]["cited"]:
            category_results[cat]["chatgpt"] += 1
        if result["gemini"]["cited"]:
            category_results[cat]["gemini"] += 1
        if result["perplexity"]["cited"]:
            category_results[cat]["perplexity"] += 1

        time.sleep(0.5)

    # Calculate rates
    for cat, data in category_results.items():
        t = max(data["total"], 1)
        data["claude_rate"] = round(data["claude"] / t * 100, 1)
        data["chatgpt_rate"] = round(data["chatgpt"] / t * 100, 1)
        data["gemini_rate"] = round(data["gemini"] / t * 100, 1)
        data["perplexity_rate"] = round(data["perplexity"] / t * 100, 1)

    # Overall
    total = len(all_results)
    claude_cited = sum(1 for r in all_results if r["claude"]["cited"])
    chatgpt_cited = sum(1 for r in all_results if r["chatgpt"]["cited"])
    gemini_cited = sum(1 for r in all_results if r["gemini"]["cited"])
    perplexity_cited = sum(1 for r in all_results if r["perplexity"]["cited"])

    # Aggregate competitor citations across all prompts and models
    competitor_counter = Counter()
    for r in all_results:
        for model in ["claude", "chatgpt", "gemini", "perplexity"]:
            for d in r.get(model, {}).get("competitors_cited", []):
                competitor_counter[d] += 1
    # Sort by frequency descending
    competitor_citations = dict(competitor_counter.most_common())

    return {
        "brand": brand,
        "domain": domain,
        "tested_at": datetime.now().isoformat(),
        "total_prompts": total,
        "competitor_citations": competitor_citations,
        "summary": {
            "claude": {"cited": claude_cited, "total": total, "rate": round(claude_cited / max(total, 1) * 100, 1)},
            "chatgpt": {"cited": chatgpt_cited, "total": total, "rate": round(chatgpt_cited / max(total, 1) * 100, 1)},
            "gemini": {"cited": gemini_cited, "total": total, "rate": round(gemini_cited / max(total, 1) * 100, 1)},
            "perplexity": {"cited": perplexity_cited, "total": total, "rate": round(perplexity_cited / max(total, 1) * 100, 1)},
        },
        "by_category": category_results,
        "results": all_results,
    }


def main():
    prompts = load_prompts()
    all_data = {}

    # Load existing results to preserve history
    if os.path.exists(OUTPUT):
        with open(OUTPUT) as f:
            try:
                existing = json.load(f)
                # Keep previous runs as history
                for cid in existing:
                    if "history" not in existing[cid]:
                        existing[cid]["history"] = []
                    existing[cid]["history"].append({
                        "tested_at": existing[cid].get("tested_at"),
                        "summary": existing[cid].get("summary"),
                    })
                    existing[cid]["history"] = existing[cid]["history"][-30:]  # Keep 30 runs
            except:
                existing = {}
    else:
        existing = {}

    for client_id in ["rank4ai", "market-invoice", "seocompare"]:
        config = prompts.get(client_id, {})
        if not config:
            continue

        result = run_client(client_id, config)

        # Preserve history
        if client_id in existing and "history" in existing[client_id]:
            result["history"] = existing[client_id]["history"]

        all_data[client_id] = result

        print(f"\n  Summary:")
        print(f"    Claude: {result['summary']['claude']['rate']}%")
        print(f"    ChatGPT: {result['summary']['chatgpt']['rate']}%")
        print(f"    Gemini: {result['summary']['gemini']['rate']}%")
        print(f"    Perplexity: {result['summary']['perplexity']['rate']}%")

    with open(OUTPUT, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"\nSaved → {OUTPUT}")


if __name__ == "__main__":
    main()
