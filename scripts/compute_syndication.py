#!/usr/bin/env python3
"""
Syndication tracker (Batch 8).

Reads src/data/syndication_log.json (manually maintained for now,
will be auto-fed when syndication endpoints are wired) and computes
per-post + per-site distribution scores.

Output: src/data/live/syndication.json
Schema:
  {
    "<site_id>": {
      "post_count": N,
      "median_distribution": 0-100,
      "fully_distributed": N,  // 8/8 platforms
      "under_distributed": [...top 10 with score < 50%],
      "recent_posts": [...last 10 with per-platform breakdown]
    },
    "fleet_summary": {...}
  }

Distribution score = published_platforms / 8 * 100.
Canonical-to-origin = required for the platform to count toward score
(syndicating without canonical = duplicate content risk, doesn't count).
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "src" / "data" / "syndication_log.json"
OUT = ROOT / "src" / "data" / "live" / "syndication.json"

PLATFORMS = ["medium", "linkedin", "devto", "youtube", "threads", "bluesky", "x", "instagram"]


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def post_distribution(post):
    """Count platforms with valid syndication. Requires canonical_to_origin=true."""
    plats = post.get("platforms", {}) or {}
    valid = 0
    by_platform = {}
    for p in PLATFORMS:
        entry = plats.get(p)
        if entry and isinstance(entry, dict):
            if entry.get("canonical_to_origin", False):
                valid += 1
                by_platform[p] = "ok"
            elif entry.get("url"):
                by_platform[p] = "no_canonical"
            else:
                by_platform[p] = "missing"
        else:
            by_platform[p] = "missing"
    score = round(100 * valid / len(PLATFORMS))
    return score, valid, by_platform


def main():
    data = load_json(LOG) or {"posts": []}
    posts = data.get("posts", []) or []

    by_site = {}
    for post in posts:
        site_id = post.get("site_id")
        if not site_id:
            continue
        score, valid, by_plat = post_distribution(post)
        record = {
            "url": post.get("url"),
            "title": post.get("title"),
            "published_iso": post.get("published_iso"),
            "score": score,
            "platforms_published": valid,
            "by_platform": by_plat,
        }
        by_site.setdefault(site_id, []).append(record)

    out = {}
    fleet = {"post_count": 0, "fully_distributed": 0, "under_distributed": 0}
    now_iso = datetime.now(timezone.utc).isoformat()

    for site_id, records in by_site.items():
        records.sort(key=lambda r: r.get("published_iso") or "", reverse=True)
        scores = [r["score"] for r in records]
        median = sorted(scores)[len(scores)//2] if scores else 0
        fully = sum(1 for s in scores if s == 100)
        under = [r for r in records if r["score"] < 50]
        out[site_id] = {
            "fetched_at": now_iso,
            "post_count": len(records),
            "median_distribution": median,
            "fully_distributed": fully,
            "under_distributed": under[:10],
            "recent_posts": records[:10],
        }
        fleet["post_count"] += len(records)
        fleet["fully_distributed"] += fully
        fleet["under_distributed"] += len(under)

    # If no posts at all, still write a sensible empty shape so the UI tile
    # renders the "no syndication tracked yet" state instead of crashing.
    if not by_site:
        for site_id in ("rank4ai", "market-invoice", "seocompare", "rochellemarashi"):
            out[site_id] = {
                "fetched_at": now_iso,
                "post_count": 0,
                "median_distribution": 0,
                "fully_distributed": 0,
                "under_distributed": [],
                "recent_posts": [],
            }

    out["fleet_summary"] = {
        **fleet,
        "platforms_tracked": PLATFORMS,
        "fetched_at": now_iso,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"✓ wrote {OUT}")
    print(f"  fleet: {fleet['post_count']} posts · {fleet['fully_distributed']} fully distributed · {fleet['under_distributed']} under-distributed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
