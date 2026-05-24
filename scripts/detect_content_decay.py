#!/usr/bin/env python3
"""
detect_content_decay.py — flag queries that have lost positions or impressions
over the last 7 days (or whatever history is available).

Reads gsc_history.json (built daily by build_gsc_history.py). Compares today's
snapshot vs ~7 days ago (fallback: oldest snapshot in history). Surfaces:

  - position_drop: query dropped 5+ positions (e.g. 7 → 14)
  - dropped_off_page_1: was pos <= 10, now > 10
  - dropped_off_page_2: was pos <= 20, now > 20
  - impressions_collapse: impressions dropped >= 50% AND was >= 50

Output → src/data/live/content_decay.json (per-site rolled-up).

Consumed by dashboard + weekly digest email + fleet-daily-review agent.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

LIVE = Path(os.path.expanduser("~/rank4ai-dashboard/src/data/live"))
HISTORY = LIVE / "gsc_history.json"


def main():
    if not HISTORY.exists():
        print("No gsc_history.json yet — run build_gsc_history.py first")
        # Write empty payload so dashboard tile doesn't 404
        with open(LIVE / "content_decay.json", "w") as f:
            json.dump({"checked_at": datetime.now(timezone.utc).isoformat(),
                       "history_days": 0,
                       "message": "Decay detection requires >=2 days of GSC history. Starts working tomorrow.",
                       "sites": {}}, f, indent=2)
        return

    history = json.load(open(HISTORY))
    dates = sorted(history.keys())
    if len(dates) < 2:
        print(f"Only {len(dates)} day(s) of history — need 2+ to detect decay. Skipping.")
        with open(LIVE / "content_decay.json", "w") as f:
            json.dump({"checked_at": datetime.now(timezone.utc).isoformat(),
                       "history_days": len(dates),
                       "message": "Decay detection requires >=2 days of GSC history. Comes online tomorrow.",
                       "sites": {}}, f, indent=2)
        return

    today = dates[-1]
    # Use 7-day-ago or oldest if less
    target = dates[max(0, len(dates) - 8)]
    today_snap = history[today]
    target_snap = history[target]

    out = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "today": today,
        "compared_to": target,
        "history_days": len(dates),
        "sites": {},
    }

    for site_id, today_data in today_snap.items():
        prev_data = target_snap.get(site_id, {})
        today_qs = today_data.get("queries", {})
        prev_qs = prev_data.get("queries", {})

        site_flags = {
            "position_drop": [],
            "dropped_off_page_1": [],
            "dropped_off_page_2": [],
            "impressions_collapse": [],
        }
        for query, today_q in today_qs.items():
            prev_q = prev_qs.get(query)
            if not prev_q: continue  # new query, nothing to compare
            tp = today_q.get("position", 0)
            pp = prev_q.get("position", 0)
            ti = today_q.get("impressions", 0)
            pi = prev_q.get("impressions", 0)

            # Skip queries with negligible impressions either side
            if max(ti, pi) < 5: continue

            entry = {"query": query, "position_now": tp, "position_before": pp,
                     "impressions_now": ti, "impressions_before": pi}

            if pp > 0 and tp - pp >= 5:
                site_flags["position_drop"].append(entry)
            if pp <= 10 and tp > 10:
                site_flags["dropped_off_page_1"].append(entry)
            if pp <= 20 and tp > 20:
                site_flags["dropped_off_page_2"].append(entry)
            if pi >= 50 and ti < pi * 0.5:
                site_flags["impressions_collapse"].append(entry)

        # Sort each list by severity
        for key in site_flags:
            if key == "impressions_collapse":
                site_flags[key].sort(key=lambda x: -(x["impressions_before"] - x["impressions_now"]))
            else:
                site_flags[key].sort(key=lambda x: -(x["position_now"] - x["position_before"]))
            site_flags[key] = site_flags[key][:15]

        total = sum(len(v) for v in site_flags.values())
        if total > 0:
            out["sites"][site_id] = {"total_decayed": total, **site_flags}

    with open(LIVE / "content_decay.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Compared {today} vs {target} ({len(dates)} days of history).")
    for site, data in out["sites"].items():
        print(f"  {site}: {data['total_decayed']} decay signals")


if __name__ == "__main__":
    main()
