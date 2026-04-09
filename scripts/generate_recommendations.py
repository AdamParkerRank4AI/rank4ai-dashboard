#!/usr/bin/env python3
"""
Auto-generate detailed, actionable recommendations from ALL dashboard data.
Every issue, gap, and low score generates a specific fix with affected pages listed.
"""
import json
import os
from datetime import datetime
from urllib.parse import urlparse

LIVE_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
OUTPUT = os.path.join(LIVE_DIR, "recommendations.json")


def load(filename):
    path = os.path.join(LIVE_DIR, filename)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def generate_for_client(client_id):
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
    serp = load("serp_data.json").get(client_id, {})

    recs = []

    # ============================================================
    # KNOWLEDGE GRAPH
    # ============================================================
    if kg and not kg.get("is_known_entity"):
        recs.append({
            "priority": "critical", "category": "AI Visibility",
            "title": "Not a known entity in Google Knowledge Graph",
            "detail": "Google does not recognise this brand as an entity. This severely limits AI citation potential. Actions: 1) Create a Wikidata entry 2) Build a Wikipedia stub page 3) Add comprehensive Organization schema 4) Get mentioned on authoritative sources (Crunchbase, LinkedIn company page, Companies House link) 5) Ensure consistent NAP across all directories.",
            "impact": "high", "pages": [],
        })

    # ============================================================
    # AI CITATIONS
    # ============================================================
    if citations:
        rate = citations.get("overall_rate", 0)
        if rate == 0:
            recs.append({
                "priority": "critical", "category": "AI Citations",
                "title": f"0% AI citation rate across {citations.get('total_queries', 0)} industry queries",
                "detail": "AI models do not recommend this brand for any industry queries. Actions: 1) Get mentioned on Reddit (r/SEO, r/digital_marketing, r/smallbusiness) 2) Contribute to relevant Wikipedia articles 3) Publish on high-authority platforms (Medium, LinkedIn articles, industry publications) 4) Build backlinks from sites AI models trust 5) Create definitive, quotable content with statistics and clear definitions.",
                "impact": "high", "pages": [],
            })
        elif rate < 20:
            recs.append({
                "priority": "high", "category": "AI Citations",
                "title": f"Low AI citation rate ({rate}%) — only brand queries cited",
                "detail": "AI knows the brand exists but doesn't recommend it for industry queries. The gap is in topical authority — AI doesn't associate this brand with the industry. Fix by creating definitive content that AI can quote: statistics, clear definitions, comparison tables, step-by-step guides.",
                "impact": "high", "pages": [],
            })

        # Competitors getting mentioned instead
        for comp in citations.get("top_competitors", [])[:3]:
            recs.append({
                "priority": "medium", "category": "AI Citations",
                "title": f"Competitor '{comp['name']}' mentioned {comp['mentions']}x instead of you",
                "detail": f"{comp['name']} is being cited by AI in {comp['mentions']} of your target queries. Analyse what content they have that you don't. Create better, more detailed, more authoritative versions of the same topics.",
                "impact": "medium", "pages": [],
            })

    # ============================================================
    # GOOGLE VISIBILITY
    # ============================================================
    if competitors:
        if competitors.get("client_visibility_pct", 0) == 0:
            top_comps = competitors.get("competitors", [])[:3]
            comp_detail = ", ".join([f"{c['domain']} ({c['visibility_pct']}%)" for c in top_comps])
            recs.append({
                "priority": "critical", "category": "Search Visibility",
                "title": f"0% Google visibility — not ranking for any target queries",
                "detail": f"Not in Google top 20 for any of {competitors.get('total_queries', 0)} target queries. Top competitors: {comp_detail}. Actions: 1) Create dedicated landing pages for each target query 2) Build topical authority with supporting content 3) Acquire backlinks to key pages 4) Improve internal linking to target pages.",
                "impact": "high",
                "pages": [qr.get("query", "") for qr in competitors.get("query_results", []) if not qr.get("rankings", {}).get(competitors.get("domain", ""))],
            })

    # ============================================================
    # SCHEMA MARKUP — specific pages missing schema
    # ============================================================
    if crawl:
        pages_without_schema = [p for p in crawl.get("pages", []) if not p.get("schemas")]
        pages_with_schema = crawl.get("pages_with_schema", 0)
        total_pages = crawl.get("pages_crawled", 0)

        if pages_without_schema:
            paths = [p["path"] for p in pages_without_schema[:20]]
            recs.append({
                "priority": "high" if len(pages_without_schema) > 10 else "medium",
                "category": "Schema",
                "title": f"{len(pages_without_schema)} pages missing structured data ({pages_with_schema}/{total_pages} have schema)",
                "detail": f"Pages with schema have 2.5x higher chance of AI citation. Add Article, FAQPage, or HowTo schema to these pages. Pages missing schema: {', '.join(paths[:10])}{'...' if len(paths) > 10 else ''}",
                "impact": "high",
                "pages": paths,
            })

    # ============================================================
    # SEO ISSUES — broken down by type with specific pages
    # ============================================================
    if crawl and crawl.get("issues"):
        issues_by_type = {}
        for issue in crawl["issues"]:
            t = issue.get("type", "other")
            if t not in issues_by_type:
                issues_by_type[t] = []
            issues_by_type[t].append(issue)

        for issue_type, issues in sorted(issues_by_type.items(), key=lambda x: -len(x[1])):
            paths = [urlparse(i["url"]).path for i in issues[:15]]
            label = issue_type.replace("_", " ").title()

            if issue_type == "missing_h1":
                detail = f"These pages have no H1 tag. Add a clear, descriptive H1 to each page. AI models use H1s to understand page topics."
                priority = "high"
            elif issue_type == "missing_meta_desc":
                detail = f"These pages have no meta description. Add unique, descriptive meta descriptions (150-160 chars) that summarise the page content."
                priority = "medium"
            elif issue_type == "missing_title":
                detail = f"These pages have no title tag. Every page needs a unique, keyword-rich title tag."
                priority = "high"
            elif issue_type == "multiple_h1":
                detail = f"These pages have more than one H1 tag. Each page should have exactly one H1."
                priority = "low"
            elif issue_type == "thin_content":
                detail = f"These pages have fewer than 100 words. Expand with detailed, authoritative content. AI models prefer pages with 500+ words."
                priority = "medium"
            elif issue_type == "broken":
                detail = f"These URLs returned HTTP errors. Fix or redirect broken pages."
                priority = "high"
            else:
                detail = f"Fix these {label.lower()} issues to improve crawlability."
                priority = "medium"

            recs.append({
                "priority": priority,
                "category": "SEO Health",
                "title": f"{len(issues)} pages with {label.lower()}",
                "detail": f"{detail} Affected pages: {', '.join(paths[:8])}{'...' if len(paths) > 8 else ''}",
                "impact": "medium",
                "pages": paths,
            })

    # ============================================================
    # ORPHAN PAGES
    # ============================================================
    if crawl and crawl.get("orphan_pages", 0) > 0:
        orphan_paths = crawl.get("orphans", [])
        orphan_short = [urlparse(u).path for u in orphan_paths[:15]]
        recs.append({
            "priority": "medium" if len(orphan_paths) < 20 else "high",
            "category": "Internal Links",
            "title": f"{len(orphan_paths)} orphan pages with no internal links pointing to them",
            "detail": f"Search engines and AI crawlers may not discover these pages. Add internal links from related content. Orphan pages: {', '.join(orphan_short[:8])}{'...' if len(orphan_short) > 8 else ''}",
            "impact": "medium",
            "pages": orphan_short,
        })

    # ============================================================
    # llms.txt
    # ============================================================
    if audit and not audit.get("llms_txt", {}).get("exists"):
        recs.append({
            "priority": "high", "category": "AI Readiness",
            "title": "No llms.txt file — AI crawlers can't identify your site",
            "detail": "Add /llms.txt to tell AI crawlers what your site is about. Include: site name, description, key topics, important pages, contact info. This is the new standard for AI discoverability. Use the astro-llms-txt plugin for auto-generation.",
            "impact": "medium", "pages": ["/llms.txt"],
        })

    # ============================================================
    # AI CRAWLERS BLOCKED
    # ============================================================
    if crawl_activity and crawl_activity.get("ai_bots_blocked", 0) > 0:
        blocked = [bot for bot, status in crawl_activity.get("ai_bot_access", {}).items() if status == "blocked"]
        recs.append({
            "priority": "high", "category": "AI Readiness",
            "title": f"{len(blocked)} AI crawlers blocked in robots.txt",
            "detail": f"These AI crawlers are blocked from accessing the site: {', '.join(blocked)}. Update robots.txt to allow them. Each blocked crawler means invisibility to that AI platform.",
            "impact": "high", "pages": ["/robots.txt"],
        })

    # ============================================================
    # AI CRAWLERS NOT MENTIONED (should add Allow)
    # ============================================================
    if crawl_activity:
        not_mentioned = [bot for bot, status in crawl_activity.get("ai_bot_access", {}).items() if status == "not_mentioned"]
        if not_mentioned:
            recs.append({
                "priority": "medium", "category": "AI Readiness",
                "title": f"{len(not_mentioned)} AI crawlers not explicitly allowed in robots.txt",
                "detail": f"These crawlers are not mentioned in robots.txt — add explicit 'Allow' rules to ensure they can access the site: {', '.join(not_mentioned)}. While not actively blocked, explicit rules are best practice for AI visibility.",
                "impact": "medium", "pages": ["/robots.txt"],
            })

    # ============================================================
    # MISSING SCHEMA TYPES
    # ============================================================
    if entities and entities.get("schema_types"):
        current_types = set(s["type"] for s in entities["schema_types"])
        ideal_types = {"Article", "FAQPage", "Organization", "LocalBusiness", "HowTo", "BreadcrumbList"}
        missing_types = ideal_types - current_types
        if missing_types:
            recs.append({
                "priority": "medium", "category": "Schema",
                "title": f"Missing schema types: {', '.join(missing_types)}",
                "detail": f"The site is using {', '.join(current_types)} but is missing these important schema types: {', '.join(missing_types)}. Organization and LocalBusiness schema help AI identify who you are. FAQPage and HowTo schema have the highest AI citation rates.",
                "impact": "medium", "pages": [],
            })

    # ============================================================
    # HIGH BOUNCE RATE
    # ============================================================
    if ga4 and ga4.get("overview", {}).get("bounce_rate", 0) > 60:
        bounce = ga4["overview"]["bounce_rate"]
        recs.append({
            "priority": "medium", "category": "Traffic",
            "title": f"High bounce rate: {bounce}%",
            "detail": f"Bounce rate is {bounce}% — over 60% suggests visitors aren't finding what they need. Improve: 1) Page load speed 2) Content relevance to search queries 3) Clear CTAs and navigation 4) Mobile experience 5) Internal linking to related content.",
            "impact": "medium", "pages": [],
        })

    # ============================================================
    # SLOW RESPONSE TIME
    # ============================================================
    uptime = load("uptime.json").get(client_id, {})
    if uptime and uptime.get("response_time_ms", 0) > 2000:
        recs.append({
            "priority": "medium", "category": "Performance",
            "title": f"Slow server response time: {uptime['response_time_ms']}ms",
            "detail": f"Server response time is {uptime['response_time_ms']}ms — should be under 500ms. Check server configuration, caching, CDN setup, and database queries.",
            "impact": "medium", "pages": [],
        })

    # ============================================================
    # NO BING CRAWL DATA
    # ============================================================
    if crawl_activity and crawl_activity.get("bing_total_crawled", 0) == 0 and crawl:
        recs.append({
            "priority": "medium", "category": "Indexing",
            "title": "No Bing crawl activity detected",
            "detail": f"Bing has not crawled any pages. Bing feeds Copilot (Microsoft's AI). Submit sitemap at bing.com/webmasters and run IndexNow submission: python3 scripts/submit_indexnow.py {client_id}",
            "impact": "medium", "pages": [],
        })

    # ============================================================
    # NO GSC DATA
    # ============================================================
    if gsc and gsc.get("totals", {}).get("impressions", 0) == 0:
        recs.append({
            "priority": "low", "category": "Search Visibility",
            "title": "No Google Search Console impressions",
            "detail": "Google Search Console shows zero impressions. The site may not be indexed, or the GSC property may need verification. Check coverage reports in GSC and submit sitemap.",
            "impact": "medium", "pages": [],
        })

    # ============================================================
    # LOW TRAFFIC (for sites that should have some)
    # ============================================================
    if ga4 and ga4.get("overview", {}).get("active_users", 0) == 0 and crawl and crawl.get("pages_crawled", 0) > 50:
        recs.append({
            "priority": "medium", "category": "Traffic",
            "title": "No traffic recorded in GA4 (30 days)",
            "detail": "GA4 shows zero users despite having content. Check: 1) GA4 tracking code is installed correctly 2) The measurement ID is correct 3) Filters aren't excluding all traffic.",
            "impact": "medium", "pages": [],
        })

    # ============================================================
    # PERFORMANCE
    # ============================================================
    if pagespeed and pagespeed.get("avg_scores"):
        scores = pagespeed["avg_scores"]
        if scores.get("performance", 100) < 50:
            slow_pages = [p["url"] for p in pagespeed.get("pages", []) if p.get("scores", {}).get("performance", 100) < 50]
            recs.append({
                "priority": "high", "category": "Performance",
                "title": f"Mobile performance score is {scores['performance']}/100",
                "detail": f"Poor mobile performance affects user experience, search rankings, and Core Web Vitals. Actions: 1) Optimise images (WebP, lazy loading) 2) Reduce JavaScript 3) Implement critical CSS 4) Use CDN caching. Slow pages: {', '.join([urlparse(u).path for u in slow_pages[:5]])}",
                "impact": "medium",
                "pages": [urlparse(u).path for u in slow_pages],
            })
        if scores.get("accessibility", 100) < 80:
            recs.append({
                "priority": "low", "category": "Accessibility",
                "title": f"Accessibility score is {scores['accessibility']}/100",
                "detail": "Improve alt text on images, heading hierarchy, colour contrast, and ARIA labels.",
                "impact": "low", "pages": [],
            })

    # ============================================================
    # AI READINESS — low-scoring pages
    # ============================================================
    if audit and audit.get("page_results"):
        low_ai_pages = [p for p in audit["page_results"] if p.get("overall_score", 100) < 40]
        if low_ai_pages:
            paths = [urlparse(p["url"]).path for p in low_ai_pages[:10]]
            recs.append({
                "priority": "medium", "category": "AI Readiness",
                "title": f"{len(low_ai_pages)} pages score below 40/100 for AI readiness",
                "detail": f"These pages have poor AI citation potential. Improve by adding: FAQ sections, clear definitions, comparison tables, statistics, author credentials. Low-scoring pages: {', '.join(paths[:6])}{'...' if len(paths) > 6 else ''}",
                "impact": "medium",
                "pages": paths,
            })

        # E-E-A-T specifically
        low_eeat = [p for p in audit["page_results"] if p.get("scores", {}).get("eeat", 100) < 25]
        if low_eeat and len(low_eeat) > 3:
            paths = [urlparse(p["url"]).path for p in low_eeat[:10]]
            recs.append({
                "priority": "medium", "category": "E-E-A-T",
                "title": f"{len(low_eeat)} pages have weak E-E-A-T signals",
                "detail": f"AI models prioritise content with expertise signals. Add: author bylines with credentials, publication dates, 'last updated' dates, citations to data sources, expert quotes. Pages: {', '.join(paths[:6])}",
                "impact": "medium",
                "pages": paths,
            })

    # ============================================================
    # CONTENT GAPS from GSC
    # ============================================================
    if gsc and gsc.get("content_gaps"):
        for gap in gsc["content_gaps"][:5]:
            recs.append({
                "priority": "medium", "category": "Content Gap",
                "title": f"'{gap['query']}' — {gap['impressions']} impressions, {gap['ctr']}% CTR",
                "detail": f"This query gets {gap['impressions']} impressions but only {gap['clicks']} clicks (CTR: {gap['ctr']}%). Position: {gap['position']}. Actions: 1) Improve the meta title and description for this query 2) Create or improve a dedicated page targeting this topic 3) Add FAQ schema addressing this query.",
                "impact": "medium",
                "pages": [],
            })

    # ============================================================
    # WIKIDATA
    # ============================================================
    wikidata = load("wikidata.json").get(client_id, {})
    if wikidata and not wikidata.get("exists"):
        recs.append({
            "priority": "high", "category": "Entity",
            "title": "Not listed on Wikidata",
            "detail": "Wikidata feeds Google Knowledge Graph and AI models. Create a Wikidata entry with: company name, type (Q4830453 = business), founding date, website, industry, founders. This is free and takes 10 minutes.",
            "impact": "high", "pages": [],
        })

    # ============================================================
    # MULTI-MODAL CONTENT
    # ============================================================
    if crawl:
        multimodal = crawl.get("pages_with_multimodal", 0)
        total = crawl.get("pages_crawled", 0)
        if total > 10 and multimodal < total * 0.1:
            recs.append({
                "priority": "medium", "category": "Content",
                "title": f"Only {multimodal}/{total} pages have multi-modal content (images + video)",
                "detail": "Pages with images AND video get 156-317% more AI citations. Add relevant images, infographics, and embedded videos to key content pages.",
                "impact": "high", "pages": [],
            })

    # ============================================================
    # COMPARISON TABLES
    # ============================================================
    if crawl:
        comp_tables = crawl.get("pages_with_comparison_table", 0)
        if comp_tables == 0:
            recs.append({
                "priority": "medium", "category": "Content",
                "title": "No comparison tables detected on the site",
                "detail": "Pages with comparison tables have 2.5x higher AI citation rate. Add comparison tables to key pages — e.g. pricing comparisons, feature comparisons, provider comparisons.",
                "impact": "medium", "pages": [],
            })

    # ============================================================
    # IMAGES MISSING ALT TEXT
    # ============================================================
    if crawl and crawl.get("images_missing_alt", 0) > 5:
        recs.append({
            "priority": "low", "category": "Accessibility",
            "title": f"{crawl['images_missing_alt']} images missing alt text",
            "detail": "Alt text helps search engines and AI understand images. Add descriptive alt text to all images.",
            "impact": "low", "pages": [],
        })

    # ============================================================
    # LONG-FORM CONTENT
    # ============================================================
    if crawl:
        long_pages = crawl.get("pages_over_2000_words", 0)
        if total > 20 and long_pages < 3:
            recs.append({
                "priority": "medium", "category": "Content",
                "title": f"Only {long_pages} pages have 2,000+ words",
                "detail": "Pages with 2,000+ words get 3x more AI citations. Create in-depth, comprehensive content on your key topics — guides, research reports, definitive explainers.",
                "impact": "medium", "pages": [],
            })

    # ============================================================
    # BING INDEXING
    # ============================================================
    if crawl_activity and crawl:
        bing_indexed = crawl_activity.get("bing_indexed", 0)
        total = crawl.get("pages_crawled", 0)
        if bing_indexed < total * 0.5 and total > 10:
            recs.append({
                "priority": "medium", "category": "Indexing",
                "title": f"Only {bing_indexed}/{total} pages indexed in Bing",
                "detail": f"Bing feeds Copilot (which has 94+ citations for some sites). Submit all pages via IndexNow: python3 scripts/submit_indexnow.py {client_id}",
                "impact": "medium", "pages": [],
            })

    # ============================================================
    # SERP — not ranking for any queries
    # ============================================================
    if serp and serp.get("organic_rate", 0) == 0 and serp.get("total_queries", 0) > 0:
        queries = [r["query"] for r in serp.get("results", []) if not r.get("brand_organic_position")]
        recs.append({
            "priority": "high", "category": "Search Visibility",
            "title": f"Not ranking in Google top 10 for any of {len(queries)} tested queries",
            "detail": f"Queries tested: {', '.join(queries[:5])}. Create dedicated, in-depth pages for each query. Target 1,500+ words with FAQ schema, comparison tables, and internal links.",
            "impact": "high",
            "pages": queries,
        })

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    recs.sort(key=lambda x: priority_order.get(x["priority"], 99))

    return recs


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
        for r in recs[:8]:
            pages_count = f" ({len(r.get('pages', []))} pages)" if r.get("pages") else ""
            print(f"  [{r['priority'].upper()}] {r['title'][:70]}{pages_count}")
        if len(recs) > 8:
            print(f"  ...and {len(recs) - 8} more")

    with open(OUTPUT, "w") as f:
        json.dump(all_recs, f, indent=2)
    print(f"\nSaved → {OUTPUT}")


if __name__ == "__main__":
    main()
