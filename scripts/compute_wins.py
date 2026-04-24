#!/usr/bin/env python3
"""Compute Wins This Week — diff today's recommendations vs snapshots from
yesterday and 7 days ago. Surfaces what cleared (wins), what regressed
(new issues), and what stuck (long-term strategic).

Writes src/data/live/wins_this_week.json:
  {
    "computed_at": ...,
    "per_site": {
      "rank4ai": {
        "cleared_today": [titles],      # wins since yesterday
        "cleared_7d": [titles],          # wins this week
        "new_today": [titles],           # regressions since yesterday
        "stuck": [titles],               # present 7+ days
        "counts": {...}
      }
    },
    "fleet_cleared_today": int,
    "fleet_cleared_7d": int,
    "fleet_new_today": int,
  }
"""
import json
import os
import shutil
from datetime import datetime, timedelta

LIVE = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
SNAPSHOT_DIR = os.path.join(LIVE, "rec_snapshots")
OUTPUT = os.path.join(LIVE, "wins_this_week.json")

os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def load_recs(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def titles_of(site_data):
    """Set of rec titles for a site."""
    recs = site_data.get("recommendations", []) if isinstance(site_data, dict) else []
    return {r.get("title") for r in recs if r.get("title")}


def read_snapshot(date_str):
    p = os.path.join(SNAPSHOT_DIR, f"recommendations_{date_str}.json")
    return load_recs(p) if os.path.exists(p) else {}


def save_today_snapshot(current):
    today = datetime.now().strftime("%Y-%m-%d")
    p = os.path.join(SNAPSHOT_DIR, f"recommendations_{today}.json")
    with open(p, "w") as f:
        json.dump(current, f, indent=2)


def prune_old_snapshots(keep_days=21):
    cutoff = datetime.now() - timedelta(days=keep_days)
    for f in os.listdir(SNAPSHOT_DIR):
        if not f.startswith("recommendations_") or not f.endswith(".json"):
            continue
        try:
            d = datetime.strptime(f.replace("recommendations_", "").replace(".json", ""), "%Y-%m-%d")
            if d < cutoff:
                os.remove(os.path.join(SNAPSHOT_DIR, f))
        except Exception:
            pass


def main():
    current = load_recs(os.path.join(LIVE, "recommendations.json"))
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    seven_ago_str = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    yesterday = read_snapshot(yesterday_str)
    seven_ago = read_snapshot(seven_ago_str)

    per_site = {}
    fleet = {"cleared_today": 0, "cleared_7d": 0, "new_today": 0, "stuck": 0}

    for site in ["rank4ai", "market-invoice", "seocompare"]:
        today_titles = titles_of(current.get(site, {}))
        yest_titles = titles_of(yesterday.get(site, {}))
        seven_titles = titles_of(seven_ago.get(site, {}))

        cleared_today = yest_titles - today_titles
        new_today = today_titles - yest_titles
        cleared_7d = seven_titles - today_titles
        # Stuck: present both 7d ago AND today (long-term items)
        stuck = seven_titles & today_titles

        per_site[site] = {
            "today_count": len(today_titles),
            "yesterday_count": len(yest_titles),
            "seven_days_ago_count": len(seven_titles),
            "cleared_today": sorted(cleared_today),
            "cleared_7d": sorted(cleared_7d),
            "new_today": sorted(new_today),
            "stuck": sorted(stuck),
            "counts": {
                "cleared_today": len(cleared_today),
                "cleared_7d": len(cleared_7d),
                "new_today": len(new_today),
                "stuck": len(stuck),
            },
        }
        fleet["cleared_today"] += len(cleared_today)
        fleet["cleared_7d"] += len(cleared_7d)
        fleet["new_today"] += len(new_today)
        fleet["stuck"] += len(stuck)

    payload = {
        "computed_at": datetime.now().isoformat(),
        "per_site": per_site,
        **{f"fleet_{k}": v for k, v in fleet.items()},
    }
    with open(OUTPUT, "w") as f:
        json.dump(payload, f, indent=2)

    # Snapshot today's recs for tomorrow's diff
    save_today_snapshot(current)
    prune_old_snapshots()

    print(f"Fleet: {fleet['cleared_today']} cleared today, {fleet['cleared_7d']} cleared 7d, {fleet['new_today']} new today, {fleet['stuck']} stuck")
    for site, data in per_site.items():
        c = data['counts']
        print(f"  {site}: {c['cleared_today']} cleared today, {c['cleared_7d']} cleared 7d, {c['new_today']} new")


if __name__ == "__main__":
    main()
