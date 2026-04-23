#!/usr/bin/env python3
"""AEO Readiness Scorecard — 60-point agent readiness score derived from
existing crawl + audit + crawl-activity data. Inspired by Addy Osmani's
6-layer agent readiness framework.

Layers (each scored 0-10):
  1. Crawlability     — robots.txt, llms.txt, AI bots allowed
  2. Discoverability  — sitemap, ai-sitemap, internal linking, orphans
  3. Readability      — content structure, passage quality, question H2s
  4. Citability       — author signals, E-E-A-T, references, stats
  5. Schema           — structured data coverage + variety
  6. Technical        — HTTPS, canonical, mobile, og, breadcrumbs

Writes src/data/live/aeo_scorecard.json — one entry per site.
"""
import json
import os
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

LIVE = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
OUTPUT = os.path.join(LIVE, "aeo_scorecard.json")

SITES = {
    "rank4ai":        "https://www.rank4ai.co.uk",
    "market-invoice": "https://marketinvoice.co.uk",
    "seocompare":     "https://seocompare.co.uk",
}


def load(name):
    path = os.path.join(LIVE, name)
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def check_url(url, timeout=5):
    """Cloudflare (and some CDNs) block the default urllib User-Agent with a
    403. Always send a Mozilla UA like a real client would."""
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Rank4AI-Dashboard-Check/1.0)"})
        r = urlopen(req, timeout=timeout)
        if r.status == 200:
            return True, len(r.read())
        return False, 0
    except (URLError, Exception):
        return False, 0


def score_site(site_id, base_url):
    crawl = load(f"crawl_{site_id}.json")
    audit = (load("ai_audit.json") or {}).get(site_id, {})
    crawl_activity = (load("crawl_activity.json") or {}).get(site_id, {})
    pages = [p for p in crawl.get("pages", []) if p.get("status") == 200]
    total_pages = max(len(pages), 1)

    # 1. CRAWLABILITY (0-10)
    crawl_score = 0
    reasons = {"crawlability": []}
    robots_ok, _ = check_url(f"{base_url}/robots.txt")
    if robots_ok:
        crawl_score += 3
        reasons["crawlability"].append("robots.txt present (+3)")
    llms_ok, llms_size = check_url(f"{base_url}/llms.txt")
    if llms_ok:
        crawl_score += 3
        reasons["crawlability"].append(f"llms.txt present ({llms_size}b) (+3)")
        if llms_size > 500:
            crawl_score += 1
            reasons["crawlability"].append("llms.txt substantive (+1)")
    ai_bots = crawl_activity.get("ai_bot_access", {})
    allowed = sum(1 for v in ai_bots.values() if v == "allowed")
    blocked = sum(1 for v in ai_bots.values() if v == "blocked")
    if allowed >= 6 and blocked == 0:
        crawl_score += 3
        reasons["crawlability"].append(f"{allowed} AI bots allowed, 0 blocked (+3)")
    elif allowed >= 4:
        crawl_score += 2
        reasons["crawlability"].append(f"{allowed} AI bots allowed (+2)")
    crawl_score = min(crawl_score, 10)

    # 2. DISCOVERABILITY (0-10)
    disc_score = 0
    reasons["discoverability"] = []
    sm_ok, _ = check_url(f"{base_url}/sitemap-index.xml")
    if not sm_ok:
        sm_ok, _ = check_url(f"{base_url}/sitemap.xml")
    if sm_ok:
        disc_score += 3
        reasons["discoverability"].append("XML sitemap present (+3)")
    ai_sm_ok, _ = check_url(f"{base_url}/ai-sitemap.txt")
    if ai_sm_ok:
        disc_score += 2
        reasons["discoverability"].append("ai-sitemap.txt present (+2)")
    orphans = sum(1 for p in pages if (p.get("internal_links_in") or 0) == 0)
    orphan_pct = orphans / total_pages * 100
    if orphan_pct < 5:
        disc_score += 3
        reasons["discoverability"].append(f"{orphan_pct:.0f}% orphans (+3)")
    elif orphan_pct < 15:
        disc_score += 2
        reasons["discoverability"].append(f"{orphan_pct:.0f}% orphans (+2)")
    elif orphan_pct < 30:
        disc_score += 1
        reasons["discoverability"].append(f"{orphan_pct:.0f}% orphans (+1)")
    else:
        reasons["discoverability"].append(f"{orphan_pct:.0f}% orphans (+0)")
    avg_in = sum((p.get("internal_links_in") or 0) for p in pages) / total_pages
    if avg_in >= 3:
        disc_score += 2
        reasons["discoverability"].append(f"avg {avg_in:.1f} inbound per page (+2)")
    elif avg_in >= 1:
        disc_score += 1
        reasons["discoverability"].append(f"avg {avg_in:.1f} inbound per page (+1)")
    disc_score = min(disc_score, 10)

    # 3. READABILITY (0-10)
    read_score = 0
    reasons["readability"] = []
    avg_words = sum((p.get("word_count") or 0) for p in pages) / total_pages
    if avg_words >= 800:
        read_score += 2
        reasons["readability"].append(f"avg {int(avg_words)} words (+2)")
    elif avg_words >= 400:
        read_score += 1
        reasons["readability"].append(f"avg {int(avg_words)} words (+1)")
    with_capsule = sum(1 for p in pages if p.get("has_answer_capsule"))
    if with_capsule / total_pages > 0.5:
        read_score += 3
        reasons["readability"].append(f"{with_capsule}/{total_pages} pages have answer capsule (+3)")
    elif with_capsule / total_pages > 0.2:
        read_score += 2
        reasons["readability"].append(f"{with_capsule}/{total_pages} pages have answer capsule (+2)")
    elif with_capsule > 0:
        read_score += 1
    with_qh2 = sum(1 for p in pages if (p.get("question_h2s") or 0) > 0)
    if with_qh2 / total_pages > 0.3:
        read_score += 3
        reasons["readability"].append(f"{with_qh2}/{total_pages} pages have question H2s (+3)")
    elif with_qh2 / total_pages > 0.1:
        read_score += 2
    elif with_qh2 > 0:
        read_score += 1
    with_lists = sum(1 for p in pages if (p.get("list_count") or 0) > 0)
    if with_lists / total_pages > 0.7:
        read_score += 2
        reasons["readability"].append(f"{with_lists}/{total_pages} pages use lists (+2)")
    elif with_lists / total_pages > 0.3:
        read_score += 1
    read_score = min(read_score, 10)

    # 4. CITABILITY (0-10)
    cit_score = 0
    reasons["citability"] = []
    with_author = sum(1 for p in pages if p.get("has_author"))
    if with_author / total_pages > 0.9:
        cit_score += 3
        reasons["citability"].append(f"{with_author}/{total_pages} pages have author signal (+3)")
    elif with_author / total_pages > 0.5:
        cit_score += 2
    elif with_author > 0:
        cit_score += 1
    with_tables = sum(1 for p in pages if (p.get("table_count") or 0) > 0)
    if with_tables / total_pages > 0.1:
        cit_score += 2
        reasons["citability"].append(f"{with_tables}/{total_pages} pages use tables (+2)")
    elif with_tables > 0:
        cit_score += 1
    with_definitions = sum(1 for p in pages if p.get("has_definition"))
    if with_definitions > 0:
        cit_score += 1
        reasons["citability"].append(f"{with_definitions} pages have definitions (+1)")
    cp = (audit.get("scores") or {}).get("citation_potential") or 0
    if cp >= 70:
        cit_score += 4
        reasons["citability"].append(f"audit citation_potential {cp} (+4)")
    elif cp >= 50:
        cit_score += 3
    elif cp >= 30:
        cit_score += 2
    elif cp > 0:
        cit_score += 1
    cit_score = min(cit_score, 10)

    # 5. SCHEMA (0-10)
    schema_score = 0
    reasons["schema"] = []
    with_schema = sum(1 for p in pages if (p.get("schemas") or []))
    schema_pct = with_schema / total_pages * 100
    if schema_pct > 95:
        schema_score += 4
        reasons["schema"].append(f"{schema_pct:.0f}% pages have schema (+4)")
    elif schema_pct > 70:
        schema_score += 3
    elif schema_pct > 40:
        schema_score += 2
    elif schema_pct > 0:
        schema_score += 1
    # Variety — count distinct @types across the site
    all_types = set()
    for p in pages:
        for t in (p.get("schemas") or []):
            all_types.add(t)
    priority = {"Organization", "LocalBusiness", "WebSite", "Article", "FAQPage", "Person", "BreadcrumbList"}
    priority_hits = len(priority & all_types)
    if priority_hits >= 6:
        schema_score += 4
        reasons["schema"].append(f"{priority_hits}/7 priority types present (+4)")
    elif priority_hits >= 4:
        schema_score += 3
    elif priority_hits >= 2:
        schema_score += 2
    elif priority_hits >= 1:
        schema_score += 1
    if "Speakable" in all_types or "SpeakableSpecification" in all_types:
        schema_score += 2
        reasons["schema"].append("Speakable schema present (+2)")
    schema_score = min(schema_score, 10)

    # 6. TECHNICAL (0-10)
    tech_score = 0
    reasons["technical"] = []
    if base_url.startswith("https://"):
        tech_score += 2
        reasons["technical"].append("HTTPS (+2)")
    with_canonical = sum(1 for p in pages if p.get("canonical"))
    if with_canonical / total_pages > 0.9:
        tech_score += 2
        reasons["technical"].append(f"{with_canonical}/{total_pages} pages have canonical (+2)")
    elif with_canonical > 0:
        tech_score += 1
    with_og = sum(1 for p in pages if p.get("has_og_tags"))
    if with_og / total_pages > 0.9:
        tech_score += 2
        reasons["technical"].append(f"{with_og}/{total_pages} pages have OG tags (+2)")
    elif with_og > 0:
        tech_score += 1
    with_crumbs = sum(1 for p in pages if p.get("has_breadcrumbs"))
    if with_crumbs / total_pages > 0.7:
        tech_score += 2
        reasons["technical"].append(f"{with_crumbs}/{total_pages} pages have breadcrumbs (+2)")
    elif with_crumbs > 0:
        tech_score += 1
    with_viewport = sum(1 for p in pages if p.get("has_viewport"))
    if with_viewport / total_pages > 0.95:
        tech_score += 2
        reasons["technical"].append("Mobile viewport on all pages (+2)")
    tech_score = min(tech_score, 10)

    total = crawl_score + disc_score + read_score + cit_score + schema_score + tech_score

    return {
        "site_id": site_id,
        "computed_at": datetime.now().isoformat(),
        "total_score": total,
        "max_score": 60,
        "percentage": round(total / 60 * 100, 1),
        "layers": {
            "crawlability": {"score": crawl_score, "max": 10, "notes": reasons["crawlability"]},
            "discoverability": {"score": disc_score, "max": 10, "notes": reasons["discoverability"]},
            "readability": {"score": read_score, "max": 10, "notes": reasons["readability"]},
            "citability": {"score": cit_score, "max": 10, "notes": reasons["citability"]},
            "schema": {"score": schema_score, "max": 10, "notes": reasons["schema"]},
            "technical": {"score": tech_score, "max": 10, "notes": reasons["technical"]},
        },
    }


def main():
    results = {}
    for site_id, base_url in SITES.items():
        print(f"Scoring {site_id}...")
        results[site_id] = score_site(site_id, base_url)
        print(f"  Total: {results[site_id]['total_score']}/60 ({results[site_id]['percentage']}%)")
        for layer, d in results[site_id]["layers"].items():
            print(f"    {layer}: {d['score']}/{d['max']}")

    results["_meta"] = {"computed_at": datetime.now().isoformat()}

    with open(OUTPUT, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {OUTPUT}")


if __name__ == "__main__":
    main()
