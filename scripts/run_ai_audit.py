#!/usr/bin/env python3
"""
AI SEO Audit — checks AI readiness of client sites.
Checks: llms.txt, robots.txt AI crawler rules, schema quality,
content structure, E-E-A-T signals, citation potential.
Outputs JSON for the dashboard.
"""

import json
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")

SITES = {
    "rank4ai": "https://www.rank4ai.co.uk",
    "market-invoice": "https://www.marketinvoice.co.uk",
    "seocompare": "https://www.seocompare.co.uk",
}

AI_CRAWLERS = [
    "GPTBot", "ChatGPT-User", "Google-Extended", "GoogleOther",
    "ClaudeBot", "Claude-Web", "PerplexityBot", "Bytespider",
    "CCBot", "cohere-ai", "Amazonbot", "anthropic-ai",
    "FacebookBot", "Applebot-Extended",
]

HEADERS = {"User-Agent": "Rank4AI-Auditor/1.0 (+https://rank4ai.co.uk)"}


def check_llms_txt(base_url):
    """Check for llms.txt file."""
    try:
        resp = requests.get(f"{base_url}/llms.txt", headers=HEADERS, timeout=10)
        if resp.status_code == 200 and len(resp.text) > 10:
            return {"exists": True, "content_length": len(resp.text), "preview": resp.text[:300]}
        return {"exists": False}
    except:
        return {"exists": False}


def check_robots_txt(base_url):
    """Check robots.txt for AI crawler rules."""
    try:
        resp = requests.get(f"{base_url}/robots.txt", headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return {"exists": False, "ai_crawlers": {}}

        text = resp.text
        crawler_status = {}
        for crawler in AI_CRAWLERS:
            if crawler.lower() in text.lower():
                # Check if allowed or disallowed
                pattern = rf'User-agent:\s*{re.escape(crawler)}.*?(?=User-agent:|\Z)'
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    block = match.group()
                    if "Disallow: /" in block:
                        crawler_status[crawler] = "blocked"
                    else:
                        crawler_status[crawler] = "allowed"
                else:
                    crawler_status[crawler] = "mentioned"
            else:
                crawler_status[crawler] = "not_mentioned"

        blocked = sum(1 for v in crawler_status.values() if v == "blocked")
        allowed = sum(1 for v in crawler_status.values() if v == "allowed")

        return {
            "exists": True,
            "ai_crawlers": crawler_status,
            "blocked_count": blocked,
            "allowed_count": allowed,
            "not_mentioned_count": len(AI_CRAWLERS) - blocked - allowed,
        }
    except:
        return {"exists": False, "ai_crawlers": {}}


def analyze_page_ai_readiness(url, html):
    """Score a page for AI citation readiness."""
    soup = BeautifulSoup(html, "html.parser")
    scores = {}

    # 1. Schema markup
    schemas = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and "@type" in item:
                    t = item["@type"]
                    schemas.extend(t if isinstance(t, list) else [str(t)])
        except:
            pass

    priority_schemas = {"Article", "FAQPage", "Organization", "LocalBusiness", "Person", "Product", "HowTo"}
    has_priority = bool(set(schemas) & priority_schemas)
    scores["schema"] = 100 if has_priority else (50 if schemas else 0)

    # 2. Content structure
    h2s = soup.find_all("h2")
    h3s = soup.find_all("h3")
    lists = soup.find_all(["ul", "ol"])
    tables = soup.find_all("table")
    question_headings = sum(1 for h in h2s + h3s if "?" in h.get_text())

    structure_score = 0
    if len(h2s) >= 3: structure_score += 25
    if len(lists) >= 2: structure_score += 25
    if tables: structure_score += 25
    if question_headings >= 1: structure_score += 25
    scores["content_structure"] = min(structure_score, 100)

    # 3. Passage length (optimal for AI: 134-167 words per section)
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    words = text.split()
    word_count = len(words)

    # Check paragraph lengths
    paragraphs = soup.find_all("p")
    good_passages = 0
    for p in paragraphs:
        p_words = len(p.get_text(strip=True).split())
        if 50 <= p_words <= 200:
            good_passages += 1

    scores["passage_quality"] = min(100, (good_passages / max(len(paragraphs), 1)) * 100)

    # 4. E-E-A-T signals
    eeat_score = 0
    text_lower = text.lower()
    if any(w in text_lower for w in ["author", "written by", "by ", "founder"]): eeat_score += 25
    if any(w in text_lower for w in ["years of experience", "certified", "qualified", "expert"]): eeat_score += 25
    if any(w in text_lower for w in ["according to", "research shows", "study", "data"]): eeat_score += 25
    if any(w in text_lower for w in ["updated", "reviewed", "published"]): eeat_score += 25
    scores["eeat"] = eeat_score

    # 5. AI citation potential
    citation_score = 0
    if re.search(r'\d+%', text): citation_score += 20  # Has statistics
    if re.search(r'(definition|what is|means)', text_lower): citation_score += 20  # Has definitions
    if tables: citation_score += 20  # Has comparison tables
    if re.search(r'(step \d|step-by-step|how to)', text_lower): citation_score += 20  # Has steps
    if word_count >= 500: citation_score += 20  # Substantial content
    scores["citation_potential"] = citation_score

    # Overall score (weighted)
    overall = (
        scores["schema"] * 0.25 +
        scores["content_structure"] * 0.20 +
        scores["passage_quality"] * 0.15 +
        scores["eeat"] * 0.20 +
        scores["citation_potential"] * 0.20
    )

    readiness = "Excellent" if overall >= 75 else "Good" if overall >= 50 else "Fair" if overall >= 25 else "Poor"

    return {
        "url": url,
        "overall_score": round(overall),
        "readiness": readiness,
        "scores": scores,
        "schemas": schemas,
        "word_count": word_count,
        "h2_count": len(h2s),
        "question_headings": question_headings,
        "list_count": len(lists),
        "table_count": len(tables),
        "good_passages": good_passages,
        "total_paragraphs": len(paragraphs),
    }


def audit_site(site_id, base_url):
    """Run full AI readiness audit on a site."""
    print(f"\nAuditing {base_url}...")

    # Check llms.txt
    llms = check_llms_txt(base_url)
    print(f"  llms.txt: {'Found' if llms['exists'] else 'Not found'}")

    # Check robots.txt
    robots = check_robots_txt(base_url)
    if robots["exists"]:
        print(f"  robots.txt: {robots.get('blocked_count', 0)} AI crawlers blocked, {robots.get('allowed_count', 0)} allowed")

    # Audit top pages (use crawl data if available)
    crawl_file = os.path.join(OUTPUT_DIR, f"crawl_{site_id}.json")
    pages_to_audit = []

    if os.path.exists(crawl_file):
        with open(crawl_file) as f:
            crawl_data = json.load(f)
        # Audit top 20 pages by internal links
        sorted_pages = sorted(crawl_data.get("pages", []), key=lambda p: p.get("internal_links_in", 0), reverse=True)
        pages_to_audit = [p["url"] for p in sorted_pages[:20]]
    else:
        pages_to_audit = [base_url]

    page_results = []
    for url in pages_to_audit:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
                result = analyze_page_ai_readiness(url, resp.text)
                page_results.append(result)
                print(f"  {result['overall_score']}/100 — {url}")
        except:
            pass
        import time
        time.sleep(0.3)

    # Calculate site-wide scores
    if page_results:
        avg_score = round(sum(r["overall_score"] for r in page_results) / len(page_results))
        avg_schema = round(sum(r["scores"]["schema"] for r in page_results) / len(page_results))
        avg_structure = round(sum(r["scores"]["content_structure"] for r in page_results) / len(page_results))
        avg_eeat = round(sum(r["scores"]["eeat"] for r in page_results) / len(page_results))
        avg_citation = round(sum(r["scores"]["citation_potential"] for r in page_results) / len(page_results))
    else:
        avg_score = avg_schema = avg_structure = avg_eeat = avg_citation = 0

    readiness = "Excellent" if avg_score >= 75 else "Good" if avg_score >= 50 else "Fair" if avg_score >= 25 else "Poor"

    return {
        "site_id": site_id,
        "domain": base_url,
        "audited_at": datetime.now().isoformat(),
        "pages_audited": len(page_results),
        "overall_score": avg_score,
        "readiness": readiness,
        "scores": {
            "schema": avg_schema,
            "content_structure": avg_structure,
            "eeat": avg_eeat,
            "citation_potential": avg_citation,
        },
        "llms_txt": llms,
        "robots_txt": robots,
        "page_results": page_results,
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_results = {}
    for site_id, url in SITES.items():
        result = audit_site(site_id, url)
        all_results[site_id] = result
        print(f"\n  Overall: {result['overall_score']}/100 ({result['readiness']})")

    output_file = os.path.join(OUTPUT_DIR, "ai_audit.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
