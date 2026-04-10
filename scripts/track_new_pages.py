#!/usr/bin/env python3
"""
Track new pages added to client sites.
Compares current crawl against baseline to find new pages.
Categorises by type (blog, question, guide, provider, location, etc.)
"""
import json
import os
from datetime import datetime
from urllib.parse import urlparse

LIVE_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
SNAPSHOTS_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/snapshots")
OUTPUT = os.path.join(LIVE_DIR, "new_pages.json")


def load(filename):
    path = os.path.join(LIVE_DIR, filename)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def categorise_page(path, h1="", title=""):
    """Categorise a page by its URL pattern and content."""
    path_lower = path.lower()
    h1_lower = (h1 or "").lower()

    if "/blog/" in path_lower:
        return "Blog Post"
    elif "/questions/" in path_lower or "/ai-search-questions/" in path_lower:
        return "Question / Answer"
    elif "/guides/" in path_lower or "/guide" in path_lower:
        return "Guide"
    elif "/providers/" in path_lower:
        return "Provider Page"
    elif "/industries/" in path_lower:
        return "Industry Page"
    elif "/locations/" in path_lower:
        return "Location Page"
    elif "/compare/" in path_lower or "/comparisons/" in path_lower:
        return "Comparison Page"
    elif "/best/" in path_lower:
        return "Best-Of Page"
    elif "/stats/" in path_lower or "/research/" in path_lower or "/data/" in path_lower:
        return "Stats / Research"
    elif "/services" in path_lower or "/ai-services" in path_lower:
        return "Service Page"
    elif "/ai-seo-agency" in path_lower:
        return "Agency / Location Page"
    elif "/working-capital/" in path_lower:
        return "Working Capital"
    elif "/tools/" in path_lower or "/calculator" in path_lower:
        return "Tool / Calculator"
    elif "/insights/" in path_lower:
        return "Insight"
    elif "?" in h1_lower:
        return "Question / Answer"
    elif "how to" in h1_lower or "how do" in h1_lower:
        return "Guide"
    elif "what is" in h1_lower or "what are" in h1_lower:
        return "Explainer"
    else:
        return "Other"


def track_client(client_id):
    """Compare current crawl to baseline and find new pages."""
    # Load current crawl
    crawl = load(f"crawl_{client_id}.json")
    if not crawl:
        return None

    current_pages = {p["url"]: p for p in crawl.get("pages", [])}
    current_urls = set(current_pages.keys())

    # Load baseline — check crawl_baseline.json first, then baseline.json
    baseline_urls = set()
    baseline_crawl_file = os.path.join(SNAPSHOTS_DIR, client_id, "crawl_baseline.json")
    baseline_file = os.path.join(SNAPSHOTS_DIR, client_id, "baseline.json")

    if os.path.exists(baseline_crawl_file):
        with open(baseline_crawl_file) as f:
            bl_crawl = json.load(f)
        baseline_urls = set(p["url"] for p in bl_crawl.get("pages", []))
    elif os.path.exists(baseline_file):
        with open(baseline_file) as f:
            baseline = json.load(f)

    # If no baseline crawl saved, save current as baseline for future comparison
    if not os.path.exists(baseline_crawl_file):
        os.makedirs(os.path.dirname(baseline_crawl_file), exist_ok=True)
        # Save just URLs and basic info (not full crawl data)
        baseline_pages = [{"url": p["url"], "path": p.get("path", ""), "h1": p.get("h1", ""), "title": p.get("title", "")} for p in crawl.get("pages", [])]
        with open(baseline_crawl_file, "w") as f:
            json.dump({"pages": baseline_pages, "saved_at": datetime.now().isoformat()}, f, indent=2)
        print(f"  Saved crawl baseline ({len(baseline_pages)} pages)")
        baseline_urls = current_urls  # No diff on first run

    # Find new pages
    new_urls = current_urls - baseline_urls
    new_pages = []

    for url in sorted(new_urls):
        page = current_pages.get(url, {})
        path = urlparse(url).path
        category = categorise_page(path, page.get("h1", ""), page.get("title", ""))
        new_pages.append({
            "url": url,
            "path": path,
            "h1": page.get("h1", ""),
            "title": page.get("title", ""),
            "category": category,
            "word_count": page.get("word_count", 0),
            "has_schema": bool(page.get("schemas")),
            "schemas": page.get("schemas", []),
        })

    # Group by category
    by_category = {}
    for p in new_pages:
        cat = p["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(p)

    # Sort categories by count
    by_category_sorted = dict(sorted(by_category.items(), key=lambda x: -len(x[1])))

    return {
        "checked_at": datetime.now().isoformat(),
        "baseline_pages": len(baseline_urls),
        "current_pages": len(current_urls),
        "new_pages_count": len(new_pages),
        "by_category": {cat: {
            "count": len(pages),
            "pages": pages,
        } for cat, pages in by_category_sorted.items()},
        "all_new_pages": new_pages,
    }


def main():
    all_results = {}

    for client_id in ["rank4ai", "market-invoice", "seocompare"]:
        print(f"\n{client_id}:")
        result = track_client(client_id)
        if result:
            all_results[client_id] = result
            print(f"  Baseline: {result['baseline_pages']} pages")
            print(f"  Current: {result['current_pages']} pages")
            print(f"  New: {result['new_pages_count']} pages")
            for cat, data in result["by_category"].items():
                print(f"    {cat}: {data['count']}")

    with open(OUTPUT, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved → {OUTPUT}")


if __name__ == "__main__":
    main()
