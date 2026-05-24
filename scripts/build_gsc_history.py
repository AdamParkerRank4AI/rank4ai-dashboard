#!/usr/bin/env python3
"""
build_gsc_history.py — daily snapshot of GSC top_queries into a rolling history.

Each day appends per-site top_queries (position + impressions + clicks) to
src/data/live/gsc_history.json keyed by date. Retains 90 days of history;
older entries pruned.

Consumed by:
  - detect_content_decay.py (compares today vs N days ago)
  - dashboard Search Performance section (sparkline charts in future)

Runs daily AFTER fetch_gsc.py completes.
"""
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

LIVE = Path(os.path.expanduser("~/rank4ai-dashboard/src/data/live"))
HISTORY = LIVE / "gsc_history.json"
TODAY = datetime.now(timezone.utc).date().isoformat()
RETAIN_DAYS = 90


def main():
    gsc = json.load(open(LIVE / "gsc.json")) if (LIVE / "gsc.json").exists() else {}
    if not gsc:
        print("No gsc.json — skipping")
        return

    history = {}
    if HISTORY.exists():
        try:
            history = json.load(open(HISTORY))
        except Exception:
            history = {}

    # Snapshot today: per-site, only the fields useful for decay analysis
    snapshot = {}
    for site_id, data in gsc.items():
        if not isinstance(data, dict): continue
        qs = data.get("top_queries", [])
        snapshot[site_id] = {
            "totals": data.get("totals", {}),
            "queries": {
                q["query"]: {
                    "position": q.get("position", 0),
                    "impressions": q.get("impressions", 0),
                    "clicks": q.get("clicks", 0),
                    "ctr": q.get("ctr", 0),
                }
                for q in qs if q.get("query")
            },
        }

    history[TODAY] = snapshot

    # Prune anything older than RETAIN_DAYS
    cutoff = (datetime.now(timezone.utc).date() - timedelta(days=RETAIN_DAYS)).isoformat()
    history = {d: v for d, v in history.items() if d >= cutoff}

    with open(HISTORY, "w") as f:
        json.dump(history, f, indent=2)
    print(f"Snapshotted {TODAY} across {len(snapshot)} sites. History now {len(history)} day(s).")


if __name__ == "__main__":
    main()
