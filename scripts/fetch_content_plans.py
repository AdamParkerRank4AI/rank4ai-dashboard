#!/usr/bin/env python3
"""
Pull per-site content plans from iCloud and surface in dashboard live data.

Source files (per site, multiple may exist):
  iCloud/claude/astro/rank4ai/CONTENT_*.md, BLOG_STRATEGY.md, DAILY_CONTENT_PLAN*.md
  iCloud/claude/astro/plan/ONGOING_WORK_MARKET_INVOICE.md, CONTENT_*.md (shared)

Output: src/data/live/content_plan_<site_id>.json — list of plan docs with
title, source path, last-modified date, first 1500 chars excerpt.
"""

import json
import os
import re
from datetime import datetime

ICLOUD = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/claude")
OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")

SITE_PLAN_DIRS = {
    "rank4ai": [
        f"{ICLOUD}/astro/rank4ai",
    ],
    "market-invoice": [
        f"{ICLOUD}/astro/plan",
    ],
    "seocompare": [
        f"{ICLOUD}/astro/rank4ai",
        f"{ICLOUD}/astro/compareaiseo" if os.path.isdir(f"{ICLOUD}/astro/compareaiseo") else None,
    ],
}

PLAN_FILE_PATTERNS = [
    r"^CONTENT_.*\.md$",
    r"^BLOG_STRATEGY\.md$",
    r"^DAILY_CONTENT_PLAN.*\.md$",
    r"^ONGOING_WORK_.*\.md$",
    r"^.*_PLAN\.md$",
]


def is_plan_file(name):
    return any(re.match(p, name) for p in PLAN_FILE_PATTERNS)


def collect(site_id, dirs):
    items = []
    seen = set()
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            full = os.path.join(d, name)
            if not os.path.isfile(full) or not is_plan_file(name) or name in seen:
                continue
            seen.add(name)
            try:
                stat = os.stat(full)
                with open(full, encoding="utf-8") as fh:
                    text = fh.read()
                title = name.replace(".md", "").replace("_", " ").title()
                # Try to pick first H1
                m = re.search(r"^# (.+)$", text, re.M)
                if m:
                    title = m.group(1).strip()
                items.append({
                    "title": title,
                    "filename": name,
                    "source_path": full.replace(os.path.expanduser("~"), "~"),
                    "size_bytes": stat.st_size,
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "excerpt": text[:1500],
                    "section_count": len(re.findall(r"^#{1,3} ", text, re.M)),
                })
            except Exception as e:
                print(f"  Skipped {name}: {e}")
    items.sort(key=lambda x: x["last_modified"], reverse=True)
    return items


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    summary = {}
    for site_id, dirs in SITE_PLAN_DIRS.items():
        items = collect(site_id, dirs)
        out_path = os.path.join(OUTPUT_DIR, f"content_plan_{site_id}.json")
        payload = {
            "site_id": site_id,
            "generated_at": datetime.now().isoformat(),
            "plan_count": len(items),
            "plans": items,
        }
        with open(out_path, "w") as fh:
            json.dump(payload, fh, indent=2)
        summary[site_id] = len(items)
        print(f"  {site_id}: {len(items)} plans → {os.path.basename(out_path)}")
    print(f"Summary: {sum(summary.values())} plans across {len(summary)} sites")


if __name__ == "__main__":
    raise SystemExit(main())
