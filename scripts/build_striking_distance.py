#!/usr/bin/env python3
"""
build_striking_distance.py — per-site striking-distance opportunity list.

"Striking distance" = queries ranking on the cusp of page 1 where a small
nudge (better title, internal link, refreshed content) converts to clicks.

Default thresholds:
  - position between 11 and 20 (page 2)
  - impressions >= 30 last 30 days
  - CTR < 5% (room to grow)
  - non-branded (excludes own-brand queries the site already captures)

Output → src/data/live/striking_distance.json (per-site top 10 + roll-up).
Consumed by:
  - dashboard Intent Split / Search Performance section
  - fleet-daily-review remote agent (reads this to identify title-rewrite targets)
  - weekly SEO digest email (Saturday)
"""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

LIVE = Path(os.path.expanduser("~/rank4ai-dashboard/src/data/live"))

# Brand-own tokens per site so we exclude defensible queries from the list
BRAND_TOKENS = {
    "rank4ai": ["rank4ai", "rank 4 ai"],
    "market-invoice": ["market invoice", "marketinvoice"],
    "seocompare": ["seocompare", "seo compare"],
    "bestbusinessloans": ["bestbusinessloans", "best business loans"],
    "fundbiz": ["fundbiz"],
    "cardmachines": ["merchanthq", "merchant hq", "acceptcard"],
    "peptideclear": ["peptideclear", "peptide clear"],
    "kartapay": ["kartapay"],
}


def is_branded(text, brand):
    t = text.lower()
    return any(b in t for b in brand)


def is_noise(q_text):
    if not q_text or len(q_text) > 90: return True
    if "-site:" in q_text or '"' in q_text: return True
    return False


def main():
    gsc = json.load(open(LIVE / "gsc.json"))
    out = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "sites": {},
        "fleet_total": 0,
    }
    fleet_total = 0
    for site_id, brand in BRAND_TOKENS.items():
        site_data = gsc.get(site_id) or {}
        queries = site_data.get("top_queries") or []
        striking = []
        for q in queries:
            text = q.get("query", "")
            if is_noise(text): continue
            if is_branded(text, brand): continue
            pos = q.get("position", 0)
            imp = q.get("impressions", 0)
            ctr = q.get("ctr", 0)
            if 11 <= pos <= 20 and imp >= 30 and ctr < 5:
                striking.append({
                    **q,
                    "potential_clicks_at_page_1": int(imp * 0.06),  # conservative 6% page-1 CTR estimate
                    "potential_lift_pct": int((0.06 / max(ctr / 100, 0.001) - 1) * 100) if ctr > 0 else None,
                })
        striking.sort(key=lambda x: -x.get("impressions", 0))
        site_total_potential = sum(s.get("potential_clicks_at_page_1", 0) for s in striking)
        out["sites"][site_id] = {
            "count": len(striking),
            "total_impressions": sum(s.get("impressions", 0) for s in striking),
            "potential_clicks_at_page_1": site_total_potential,
            "top": striking[:15],
        }
        fleet_total += site_total_potential
    out["fleet_total"] = fleet_total

    output_path = LIVE / "striking_distance.json"
    with open(output_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote → {output_path}\n")
    print(f"Fleet potential clicks at page 1: {fleet_total}")
    for site, data in out["sites"].items():
        if data["count"] == 0: continue
        print(f"  {site:20s} {data['count']:2d} striking queries, {data['total_impressions']} imp, ~{data['potential_clicks_at_page_1']} clicks if lifted")


if __name__ == "__main__":
    main()
