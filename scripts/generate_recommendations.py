#!/usr/bin/env python3
"""
Auto-generate prioritised recommendations from all dashboard data.
Produces a "Top 10 things to fix" list per client.
"""
import json
import os
from datetime import datetime

LIVE_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
OUTPUT = os.path.join(LIVE_DIR, "recommendations.json")


def load(filename):
    path = os.path.join(LIVE_DIR, filename)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def generate_for_client(client_id):
    """Generate recommendations from all data sources."""
    crawl = load(f"crawl_{client_id}.json")
    audit = load("ai_audit.json").get(client_id, {})
    citations = load("citations_by_type.json").get(client_id, {})
    ga4 = load("ga4.json").get(client_id, {})
    gsc = load("gsc.json").get(client_id, {})
    pagespeed = load("pagespeed.json").get(client_id, {})
    kg = load("knowledge_graph.json").get(client_id, {})
    competitors = load("competitor_serp.json").get(client_id, {})
    crawl_activity = load("crawl_activity.json").get(client_id, {})
    entities = load("nlp_entities.json").get(client_id, {})

    recs = []

    # --- CRITICAL (Red) ---

    # Knowledge Graph
    if kg and not kg.get("is_known_entity"):
        recs.append({
            "priority": "critical",
            "category": "AI Visibility",
            "title": "Not a known entity in Google Knowledge Graph",
            "detail": "Google does not recognise this brand as an entity. This severely limits AI citation potential. Build entity signals through structured data, Wikipedia, Wikidata, and authoritative mentions.",
            "impact": "high",
        })

    # AI citation rate
    if citations and citations.get("overall_rate", 0) == 0:
        recs.append({
            "priority": "critical",
            "category": "AI Citations",
            "title": f"0% AI citation rate across {citations.get('total_queries', 0)} industry queries",
            "detail": "AI models do not recommend this brand for any industry-relevant queries. Need to build authority through content, backlinks, and ecosystem presence on sources AI models trust.",
            "impact": "high",
        })
    elif citations and citations.get("overall_rate", 0) < 20:
        brand_rate = citations.get("by_type", {}).get("brand", {}).get("rate", 0)
        recs.append({
            "priority": "high",
            "category": "AI Citations",
            "title": f"Low AI citation rate ({citations.get('overall_rate')}%) — brand queries {brand_rate}%",
            "detail": "AI knows the brand exists but doesn't recommend it for industry queries. Focus on getting mentioned on authoritative sources (Reddit, industry publications, Wikipedia).",
            "impact": "high",
        })

    # Competitor visibility gap
    if competitors and competitors.get("client_visibility_pct", 0) == 0:
        top_comp = competitors.get("competitors", [{}])[0] if competitors.get("competitors") else {}
        recs.append({
            "priority": "critical",
            "category": "Search Visibility",
            "title": f"0% Google visibility for target queries — top competitor at {top_comp.get('visibility_pct', 0)}%",
            "detail": f"Not ranking in Google top 20 for any of {competitors.get('total_queries', 0)} target queries. {top_comp.get('domain', 'Competitors')} is visible in {top_comp.get('visibility_pct', 0)}% of queries. Need targeted content + link building for these terms.",
            "impact": "high",
        })

    # --- HIGH (Orange) ---

    # llms.txt
    if audit and not audit.get("llms_txt", {}).get("exists"):
        recs.append({
            "priority": "high",
            "category": "AI Readiness",
            "title": "No llms.txt file found",
            "detail": "Add /llms.txt to tell AI crawlers what your site is about. This is the new standard for AI discoverability — like robots.txt but for LLMs.",
            "impact": "medium",
        })

    # AI crawlers blocked
    if crawl_activity and crawl_activity.get("ai_bots_blocked", 0) > 0:
        recs.append({
            "priority": "high",
            "category": "AI Readiness",
            "title": f"{crawl_activity['ai_bots_blocked']} AI crawlers blocked in robots.txt",
            "detail": "AI crawlers are being blocked from accessing the site. Update robots.txt to allow GPTBot, ClaudeBot, PerplexityBot, and Google-Extended.",
            "impact": "high",
        })

    # Performance
    if pagespeed and pagespeed.get("avg_scores", {}).get("performance", 100) < 50:
        score = pagespeed["avg_scores"]["performance"]
        recs.append({
            "priority": "high",
            "category": "Performance",
            "title": f"Mobile performance score is {score}/100",
            "detail": "Poor mobile performance affects both user experience and search rankings. Optimise images, reduce JavaScript, implement lazy loading.",
            "impact": "medium",
        })

    # Schema coverage
    if crawl:
        schema_pct = round(crawl.get("pages_with_schema", 0) / max(crawl.get("pages_crawled", 1), 1) * 100)
        if schema_pct < 50:
            recs.append({
                "priority": "high",
                "category": "AI Readiness",
                "title": f"Only {schema_pct}% of pages have structured data",
                "detail": f"{crawl.get('pages_with_schema', 0)} of {crawl.get('pages_crawled', 0)} pages have schema markup. Pages with schema have 2.5x higher chance of AI citation. Add Article, FAQPage, or HowTo schema to all content pages.",
                "impact": "high",
            })

    # --- MEDIUM (Yellow) ---

    # Content gaps from GSC
    if gsc and gsc.get("content_gaps"):
        gaps = gsc["content_gaps"]
        recs.append({
            "priority": "medium",
            "category": "Content",
            "title": f"{len(gaps)} content gap opportunities from Google Search Console",
            "detail": f"Queries with high impressions but low clicks. Top gap: '{gaps[0]['query']}' ({gaps[0]['impressions']} impressions, {gaps[0]['ctr']}% CTR). Improve meta titles/descriptions or create dedicated content.",
            "impact": "medium",
        })

    # SEO issues
    if crawl and crawl.get("total_issues", 0) > 10:
        # Count by type
        issue_types = {}
        for issue in crawl.get("issues", []):
            t = issue.get("type", "other")
            issue_types[t] = issue_types.get(t, 0) + 1
        top_issue = max(issue_types.items(), key=lambda x: x[1]) if issue_types else ("unknown", 0)
        recs.append({
            "priority": "medium",
            "category": "SEO Health",
            "title": f"{crawl['total_issues']} technical SEO issues found",
            "detail": f"Most common: {top_issue[0].replace('_', ' ')} ({top_issue[1]} instances). Fix these to improve crawlability and indexing.",
            "impact": "medium",
        })

    # Orphan pages
    if crawl and crawl.get("orphan_pages", 0) > 0:
        recs.append({
            "priority": "medium",
            "category": "Internal Links",
            "title": f"{crawl['orphan_pages']} orphan pages with no internal links",
            "detail": "These pages have no internal links pointing to them — search engines and AI crawlers may not discover them. Add internal links from related content.",
            "impact": "medium",
        })

    # E-E-A-T score
    if audit and audit.get("scores", {}).get("eeat", 100) < 40:
        recs.append({
            "priority": "medium",
            "category": "AI Readiness",
            "title": f"Low E-E-A-T score ({audit['scores']['eeat']}/100)",
            "detail": "AI models prioritise content with clear expertise signals. Add author bylines, credentials, publication dates, and cite data sources.",
            "impact": "medium",
        })

    # Thin content
    if crawl and crawl.get("avg_word_count", 999) < 300:
        recs.append({
            "priority": "medium",
            "category": "Content",
            "title": f"Average word count is only {crawl['avg_word_count']} words",
            "detail": "Pages with substantial content (500+ words) are more likely to be cited by AI. Expand thin pages with detailed, authoritative content.",
            "impact": "medium",
        })

    # --- LOW (Blue) ---

    # Accessibility
    if pagespeed and pagespeed.get("avg_scores", {}).get("accessibility", 100) < 80:
        recs.append({
            "priority": "low",
            "category": "Accessibility",
            "title": f"Accessibility score is {pagespeed['avg_scores']['accessibility']}/100",
            "detail": "Improve alt text, heading hierarchy, and ARIA labels for better accessibility and SEO.",
            "impact": "low",
        })

    # Bing indexed
    if crawl_activity and crawl_activity.get("bing_indexed", 0) < crawl.get("pages_crawled", 0) * 0.5 if crawl else False:
        recs.append({
            "priority": "low",
            "category": "Indexing",
            "title": f"Only {crawl_activity.get('bing_indexed', 0)} pages indexed in Bing (site has {crawl.get('pages_crawled', 0)})",
            "detail": "Submit all pages via IndexNow to improve Bing/Copilot visibility. Run: python3 scripts/submit_indexnow.py " + client_id,
            "impact": "medium",
        })

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    recs.sort(key=lambda x: priority_order.get(x["priority"], 99))

    return recs[:15]  # Top 15


def main():
    all_recs = {}

    for client_id in ["rank4ai", "market-invoice", "seocompare"]:
        recs = generate_for_client(client_id)
        all_recs[client_id] = {
            "generated_at": datetime.now().isoformat(),
            "total": len(recs),
            "critical": sum(1 for r in recs if r["priority"] == "critical"),
            "high": sum(1 for r in recs if r["priority"] == "high"),
            "medium": sum(1 for r in recs if r["priority"] == "medium"),
            "low": sum(1 for r in recs if r["priority"] == "low"),
            "recommendations": recs,
        }
        print(f"\n{client_id}: {len(recs)} recommendations")
        print(f"  Critical: {all_recs[client_id]['critical']} | High: {all_recs[client_id]['high']} | Medium: {all_recs[client_id]['medium']} | Low: {all_recs[client_id]['low']}")
        for r in recs[:5]:
            print(f"  [{r['priority'].upper()}] {r['title'][:70]}")

    with open(OUTPUT, "w") as f:
        json.dump(all_recs, f, indent=2)
    print(f"\nSaved → {OUTPUT}")


if __name__ == "__main__":
    main()
