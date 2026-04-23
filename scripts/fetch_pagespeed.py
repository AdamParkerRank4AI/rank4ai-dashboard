#!/usr/bin/env python3
"""
Fetch Google PageSpeed Insights + Core Web Vitals for dashboard.
Free API — 25,000 requests/day, no auth needed.
"""
import json
import os
from datetime import datetime

import requests

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")

# Test homepage + key pages per client
SITES = {
    "rank4ai": [
        "https://www.rank4ai.co.uk/",
        "https://www.rank4ai.co.uk/ai-search-visibility",
        "https://www.rank4ai.co.uk/questions",
        "https://www.rank4ai.co.uk/blog",
    ],
    "market-invoice": [
        "https://www.marketinvoice.co.uk/",
        "https://www.marketinvoice.co.uk/providers/",
        "https://www.marketinvoice.co.uk/guides/how-invoice-finance-works/",
        "https://www.marketinvoice.co.uk/compare/",
    ],
    "seocompare": [
        "https://www.seocompare.co.uk/",
    ],
}

API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def fetch_page(url, strategy="mobile"):
    """Fetch PageSpeed data for a single URL."""
    params = {
        "url": url,
        "strategy": strategy,
        "category": ["performance", "accessibility", "seo", "best-practices"],
    }

    try:
        resp = requests.get(API_URL, params=params, timeout=60)
        if resp.status_code != 200:
            return {"url": url, "error": f"HTTP {resp.status_code}"}

        data = resp.json()

        # Lighthouse scores
        categories = data.get("lighthouseResult", {}).get("categories", {})
        scores = {}
        for cat_id, cat_data in categories.items():
            scores[cat_id] = round((cat_data.get("score", 0) or 0) * 100)

        # Core Web Vitals from field data (CrUX)
        field = data.get("loadingExperience", {})
        metrics = field.get("metrics", {})

        cwv = {}
        if "LARGEST_CONTENTFUL_PAINT_MS" in metrics:
            cwv["lcp_ms"] = metrics["LARGEST_CONTENTFUL_PAINT_MS"].get("percentile")
            cwv["lcp_category"] = metrics["LARGEST_CONTENTFUL_PAINT_MS"].get("category")
        if "CUMULATIVE_LAYOUT_SHIFT_SCORE" in metrics:
            cwv["cls"] = metrics["CUMULATIVE_LAYOUT_SHIFT_SCORE"].get("percentile")
            cwv["cls_category"] = metrics["CUMULATIVE_LAYOUT_SHIFT_SCORE"].get("category")
        if "INTERACTION_TO_NEXT_PAINT" in metrics:
            cwv["inp_ms"] = metrics["INTERACTION_TO_NEXT_PAINT"].get("percentile")
            cwv["inp_category"] = metrics["INTERACTION_TO_NEXT_PAINT"].get("category")
        if "FIRST_CONTENTFUL_PAINT_MS" in metrics:
            cwv["fcp_ms"] = metrics["FIRST_CONTENTFUL_PAINT_MS"].get("percentile")

        overall_category = field.get("overall_category", "NONE")

        # Lab data
        audits = data.get("lighthouseResult", {}).get("audits", {})
        lab = {}
        for key in ["first-contentful-paint", "largest-contentful-paint", "total-blocking-time", "cumulative-layout-shift", "speed-index", "interactive"]:
            if key in audits:
                lab[key] = {
                    "value": audits[key].get("numericValue"),
                    "score": audits[key].get("score"),
                    "display": audits[key].get("displayValue"),
                }

        return {
            "url": url,
            "strategy": strategy,
            "scores": scores,
            "cwv": cwv,
            "cwv_pass": overall_category == "FAST",
            "overall_category": overall_category,
            "lab": lab,
        }

    except Exception as e:
        return {"url": url, "error": str(e)[:200]}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_results = {}

    for site_id, urls in SITES.items():
        print(f"\nFetching PageSpeed for {site_id}...")
        pages = []

        for url in urls:
            print(f"  {url}...")
            result = fetch_page(url, "mobile")
            pages.append(result)

            if "scores" in result:
                s = result["scores"]
                print(f"    Performance: {s.get('performance', '?')} | SEO: {s.get('seo', '?')} | Accessibility: {s.get('accessibility', '?')}")
                if result.get("cwv"):
                    cwv = result["cwv"]
                    print(f"    CWV: LCP={cwv.get('lcp_ms', '?')}ms | CLS={cwv.get('cls', '?')} | INP={cwv.get('inp_ms', '?')}ms | Overall: {result.get('overall_category', '?')}")
            elif "error" in result:
                print(f"    Error: {result['error']}")

        # Calculate averages
        scored = [p for p in pages if "scores" in p]
        avg_scores = {}
        if scored:
            for key in ["performance", "accessibility", "seo", "best-practices"]:
                vals = [p["scores"].get(key, 0) for p in scored]
                avg_scores[key] = round(sum(vals) / len(vals))

        cwv_pages = [p for p in pages if p.get("cwv")]
        cwv_pass_count = sum(1 for p in pages if p.get("cwv_pass"))

        all_results[site_id] = {
            "site_id": site_id,
            "fetched_at": datetime.now().isoformat(),
            "pages_tested": len(pages),
            "avg_scores": avg_scores,
            "cwv_pass_count": cwv_pass_count,
            "cwv_total": len(cwv_pages),
            "pages": pages,
        }

    output_file = os.path.join(OUTPUT_DIR, "pagespeed.json")
    now_iso = datetime.now().isoformat()

    # Load existing so we can preserve good data for sites that rate-limited this run
    existing = {}
    if os.path.exists(output_file):
        try:
            with open(output_file) as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    # Fully rate-limited run: keep existing per-site data, but ALWAYS record last_run_at
    # + rate_limited flag at the top level so dashboard can show "last attempted X ago"
    # instead of silently showing stale Apr data.
    has_any_scores = any(r.get("avg_scores") for r in all_results.values())
    merged = {}
    if not has_any_scores:
        print("\nAll requests rate limited — keeping existing site data")
        for site_id, data in existing.items():
            if isinstance(data, dict) and site_id not in ("_meta",):
                merged[site_id] = data
    else:
        # Per-site merge: keep existing for sites that returned no scores this run
        for site_id, data in all_results.items():
            if not data.get("avg_scores") and existing.get(site_id, {}).get("avg_scores"):
                merged[site_id] = existing[site_id]
                print(f"  Keeping existing data for {site_id} (rate limited)")
            else:
                merged[site_id] = data

    # Always stamp last_run_at at the top level so the dashboard can distinguish
    # "data is from Apr 9 AND script hasn't run since" from "data is from Apr 9
    # BUT script ran today and PSI was rate limited".
    merged["_meta"] = {
        "last_run_at": now_iso,
        "last_success_at": (existing.get("_meta", {}).get("last_success_at")
                            if not has_any_scores
                            else now_iso),
        "rate_limited_this_run": not has_any_scores,
    }

    with open(output_file, "w") as f:
        json.dump(merged, f, indent=2)
    print(f"\nSaved → {output_file} (rate_limited={not has_any_scores})")


if __name__ == "__main__":
    main()
