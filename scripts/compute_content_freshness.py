#!/usr/bin/env python3
"""
Content freshness (Batch 6).

Reads each fleet site's crawl_<site>.json + the per-site
page-publish-dates.json (when present) to compute days-since-update
per page, surfaces oldest pages, and flags 30d / 12mo thresholds.

Output: src/data/live/content_freshness.json
Schema:
  {
    "<site_id>": {
      "fetched_at": "...",
      "total_pages": N,
      "with_dates": N,
      "fresh_30d": N,
      "fresh_90d": N,
      "stale_12mo": N,
      "median_age_days": N,
      "oldest_pages": [{"url", "last_modified", "age_days", "h1"}],
      "refresh_pile": [...] // top 10 oldest non-archive pages
    },
    "fleet_summary": {...}
  }
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LIVE = Path(__file__).resolve().parent.parent / "src" / "data" / "live"
OUT = LIVE / "content_freshness.json"

SITES = [
    {"id": "rank4ai", "crawl": "crawl_rank4ai.json", "dates_path": Path.home() / "rank4ai-site" / "src" / "data" / "page-dates.json"},
    {"id": "market-invoice", "crawl": "crawl_market-invoice.json", "dates_path": Path.home() / "compare-invoice-finance" / "src" / "data" / "page-dates.json"},
    {"id": "seocompare", "crawl": "crawl_seocompare.json", "dates_path": Path.home() / "compareaiseo" / "src" / "data" / "page-dates.json"},
    {"id": "rochellemarashi", "crawl": "crawl_rochellemarashi.json", "dates_path": Path.home() / "rochellemarashi" / "src" / "data" / "page-dates.json"},
]

# Paths to skip from the refresh pile (boilerplate / archive / not refreshable)
SKIP_PATTERNS = (
    "/privacy", "/terms", "/cookies", "/accessibility", "/disclaimer",
    "/complaints", "/sitemap", "/404", "/robots", "/admin", "/lp/",
    "/preview/", "/_redirects", "/contact", "/thank",
)


def parse_date(s):
    """Parse ISO-ish date strings, return aware datetime or None."""
    if not s or not isinstance(s, str):
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        if "T" in s:
            return datetime.fromisoformat(s).replace(tzinfo=timezone.utc) if "+" not in s and "-" not in s[10:] else datetime.fromisoformat(s).astimezone(timezone.utc)
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def is_skippable(path):
    return any(p in path for p in SKIP_PATTERNS)


def compute_for_site(site, now):
    crawl = load_json(LIVE / site["crawl"])
    dates_lookup = {}
    dates_data = load_json(site["dates_path"])
    # page-dates.json on each site is { "/path/": {"added": "YYYY-MM-DD", "updated": "YYYY-MM-DD"} }
    if isinstance(dates_data, dict):
        for k, v in dates_data.items():
            if isinstance(v, dict):
                dates_lookup[k] = v.get("updated") or v.get("added")
            elif isinstance(v, str):
                dates_lookup[k] = v

    if not crawl or not isinstance(crawl, dict):
        return {"error": "no crawl data", "fetched_at": now.isoformat()}

    pages = crawl.get("pages", [])
    if not isinstance(pages, list):
        return {"error": "crawl.pages malformed", "fetched_at": now.isoformat()}

    enriched = []
    for p in pages:
        if not isinstance(p, dict):
            continue
        path = p.get("path") or ""
        url = p.get("url") or ""
        # Prefer page-publish-dates.json (canonical) over crawl-extracted last_modified
        last_modified = None
        if path and path in dates_lookup:
            last_modified = dates_lookup[path]
        elif (path + "/") in dates_lookup:
            last_modified = dates_lookup[path + "/"]
        elif path.rstrip("/") in dates_lookup:
            last_modified = dates_lookup[path.rstrip("/")]
        if not last_modified:
            last_modified = p.get("last_modified")

        dt = parse_date(last_modified)
        age_days = None
        if dt:
            age_days = max(0, (now - dt).days)

        enriched.append({
            "url": url,
            "path": path,
            "h1": (p.get("h1") or "")[:120],
            "last_modified": last_modified,
            "age_days": age_days,
            "word_count": p.get("word_count"),
        })

    with_dates = [e for e in enriched if e["age_days"] is not None]
    ages = sorted([e["age_days"] for e in with_dates])

    fresh_30d = sum(1 for a in ages if a <= 30)
    fresh_90d = sum(1 for a in ages if a <= 90)
    stale_12mo = sum(1 for a in ages if a > 365)

    median_age = ages[len(ages)//2] if ages else None

    # Oldest pages overall
    oldest_overall = sorted(with_dates, key=lambda e: e["age_days"], reverse=True)[:10]

    # Refresh pile = oldest pages excluding boilerplate
    refresh_pile = [
        e for e in sorted(with_dates, key=lambda e: e["age_days"], reverse=True)
        if not is_skippable(e["path"])
    ][:10]

    return {
        "fetched_at": now.isoformat(),
        "total_pages": len(enriched),
        "with_dates": len(with_dates),
        "fresh_30d": fresh_30d,
        "fresh_90d": fresh_90d,
        "stale_12mo": stale_12mo,
        "median_age_days": median_age,
        "oldest_pages": oldest_overall,
        "refresh_pile": refresh_pile,
    }


def main():
    now = datetime.now(timezone.utc)
    out = {}
    fleet = {"total_pages": 0, "with_dates": 0, "fresh_30d": 0, "fresh_90d": 0, "stale_12mo": 0}
    for site in SITES:
        site_out = compute_for_site(site, now)
        out[site["id"]] = site_out
        for k in fleet:
            fleet[k] += site_out.get(k, 0) or 0
        if "error" in site_out:
            print(f"  {site['id']}: {site_out['error']}")
        else:
            print(f"  {site['id']}: {site_out['with_dates']}/{site_out['total_pages']} dated · "
                  f"fresh30={site_out['fresh_30d']} stale12mo={site_out['stale_12mo']} "
                  f"median={site_out['median_age_days']}d")

    out["fleet_summary"] = {
        **fleet,
        "fetched_at": now.isoformat(),
    }

    LIVE.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\n✓ wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
