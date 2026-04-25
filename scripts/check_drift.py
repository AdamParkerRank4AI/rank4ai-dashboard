#!/usr/bin/env python3
"""Drift detector — cross-checks CLAUDE.md / project assertions against live page content.

Catches silent drift like: MI says base rate is 3.75% in CLAUDE.md but live site
still shows 4.00% from a previous BoE move. Or Companies House number changed.
Or director name updated everywhere except one stale About page.

Reads:
- src/data/drift_assertions.json (config: per-site list of expected values)
- src/data/live/crawl_<site>.json (page text + URLs)

Writes:
- src/data/live/drift_report.json — per-site findings, ready for dashboard tile

Findings types:
- ok: expected value found on every relevant page
- missing: expected value not found anywhere (potential drift)
- mismatch: alternate (deprecated) value found on N pages — needs refresh
"""
import json
import os
import re
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(PROJECT_DIR, "src", "data", "live")
ASSERTIONS = os.path.join(PROJECT_DIR, "src", "data", "drift_assertions.json")
OUTPUT = os.path.join(LIVE, "drift_report.json")

# Crawl JSON stores structural metadata (title/h1/meta) only, not body_text.
# Drift checks need body content (e.g. "base rate" mentioned in a paragraph),
# so this script does its own targeted fetches of money pages per site.
PAGES_PER_SITE = 12
UA = "Mozilla/5.0 (compatible; Rank4AI-Drift-Detector/1.0)"


def fetch_page_text(url):
    try:
        req = Request(url, headers={"User-Agent": UA})
        with urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")
    except (URLError, HTTPError, Exception):
        return ""
    # Strip scripts/styles, then tags. Cheap text extraction.
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text


def pick_money_pages(crawl, n):
    """Pick a diverse set of pages worth scanning for assertions: homepage,
    about, contact, recent blog posts, top inbound-linked pages."""
    pages = [p for p in crawl.get("pages", []) if p.get("status") == 200]
    if not pages:
        return []

    seeds = []
    seen_urls = set()

    def add(p):
        u = p.get("url")
        if u and u not in seen_urls:
            seeds.append(p)
            seen_urls.add(u)

    # Homepage / shallow pages
    for p in sorted(pages, key=lambda x: x.get("path", "/").count("/")):
        if len(seeds) >= n // 2:
            break
        add(p)

    # Highest internal-link-in (probably authoritative)
    for p in sorted(pages, key=lambda x: -(x.get("internal_links_in") or 0)):
        if len(seeds) >= n:
            break
        add(p)

    return seeds[:n]


def load_crawl(site_id):
    path = os.path.join(LIVE, f"crawl_{site_id}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def find_in_page(haystack, needle, context_words):
    """Return True if needle appears in haystack, optionally near context words."""
    if not haystack or not needle:
        return False
    haystack_lower = haystack.lower()
    needle_lower = needle.lower()
    if needle_lower not in haystack_lower:
        return False
    if not context_words:
        return True
    # Within 200 chars of any context word
    for ctx in context_words:
        ctx_lower = ctx.lower()
        for m in re.finditer(re.escape(ctx_lower), haystack_lower):
            window_start = max(0, m.start() - 200)
            window_end = min(len(haystack_lower), m.end() + 200)
            if needle_lower in haystack_lower[window_start:window_end]:
                return True
    return False


def page_text(page, body_cache):
    """Combine crawl-stored structural fields with live-fetched body text."""
    url = page.get("url", "")
    parts = [
        page.get("title") or "",
        page.get("meta_desc") or "",
        page.get("h1") or "",
        body_cache.get(url, ""),
    ]
    return " ".join(parts)


def check_assertion(assertion, pages, body_cache):
    expected = assertion["expected"]
    context = assertion.get("context_required", [])
    alternates = assertion.get("alternates_to_flag", [])
    exclude_paths = assertion.get("exclude_paths", [])

    expected_hits = []
    alternate_hits = []
    no_hit_pages = []

    for p in pages:
        text = page_text(p, body_cache)
        url = p.get("url", "")
        path = p.get("path", "")

        # Skip pages where alternate values are expected (e.g. calculators show ranges)
        if any(ex in path for ex in exclude_paths):
            continue

        # Only check pages where the context is mentioned (otherwise irrelevant)
        if context:
            relevant = any(c.lower() in text.lower() for c in context)
            if not relevant:
                continue

        if find_in_page(text, expected, context):
            expected_hits.append(url)
        else:
            no_hit_pages.append(url)

        for alt in alternates:
            if find_in_page(text, alt, context):
                alternate_hits.append({"url": url, "value": alt})

    relevant_total = len(expected_hits) + len(no_hit_pages)
    return {
        "id": assertion["id"],
        "label": assertion["label"],
        "expected": expected,
        "relevant_pages": relevant_total,
        "expected_hits": len(expected_hits),
        "missing_pages": no_hit_pages[:10],
        "alternate_hits": alternate_hits[:10],
        "drift_detected": len(alternate_hits) > 0,
        "coverage_pct": round(len(expected_hits) / relevant_total * 100, 1) if relevant_total else 0,
    }


def check_site(site_id, assertions):
    crawl = load_crawl(site_id)
    if not crawl:
        return {"error": f"No crawl data for {site_id}"}

    pages = pick_money_pages(crawl, PAGES_PER_SITE)

    # Fetch body text once per URL (assertions may overlap)
    body_cache = {}
    for p in pages:
        url = p.get("url")
        if url:
            print(f"    fetching {url}")
            body_cache[url] = fetch_page_text(url)

    findings = [check_assertion(a, pages, body_cache) for a in assertions]

    drift_count = sum(1 for f in findings if f.get("drift_detected"))
    return {
        "site_id": site_id,
        "pages_scanned": len(pages),
        "assertions_checked": len(assertions),
        "drift_count": drift_count,
        "findings": findings,
    }


def main():
    if not os.path.exists(ASSERTIONS):
        print(f"No assertions config at {ASSERTIONS}")
        return

    with open(ASSERTIONS) as f:
        config = json.load(f)

    report = {
        "computed_at": datetime.now().isoformat(),
        "per_site": {},
        "fleet_drift_count": 0,
    }

    for site_id, assertions in config.items():
        print(f"\n{site_id}:")
        result = check_site(site_id, assertions)
        report["per_site"][site_id] = result
        if result.get("error"):
            print(f"  {result['error']}")
            continue
        print(f"  Pages: {result['pages_scanned']}, drift: {result['drift_count']}")
        for f in result["findings"]:
            flag = "⚠" if f.get("drift_detected") else "✓"
            print(f"    {flag} {f['label']}: expected '{f['expected']}' on {f['expected_hits']}/{f['relevant_pages']} relevant pages ({f['coverage_pct']}%)")
            if f.get("alternate_hits"):
                for ah in f["alternate_hits"][:3]:
                    print(f"        ⚠ Found alternate '{ah['value']}' at {ah['url']}")
        report["fleet_drift_count"] += result.get("drift_count", 0)

    with open(OUTPUT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nFleet drift: {report['fleet_drift_count']} findings")
    print(f"Saved → {OUTPUT}")


if __name__ == "__main__":
    main()
