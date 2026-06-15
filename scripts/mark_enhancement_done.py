#!/usr/bin/env python3
"""Mark enhancement-backlog items DONE so they stop resurfacing.

The backlog (build_enhancement_backlog.py) is regenerated every refresh, so
"done" can't live only in that file — a rebuild would wipe it. Done-state lives
here in enhancement_done.json, keyed by the stable action id, and the builder
applies it on every run. Once an id is marked done, the next copy-into-session
box will skip it.

Usage:
  python3 scripts/mark_enhancement_done.py <id> [<id> ...] [--note "what you did"]
  python3 scripts/mark_enhancement_done.py --undo <id> [<id> ...]
  python3 scripts/mark_enhancement_done.py --list            # show open ids

ids are the short tokens shown on each backlog row (e.g. mark-rank-1a2b3c4d).
"""
import json
import os
import sys
from datetime import datetime

LIVE = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
DONE = os.path.join(LIVE, "enhancement_done.json")
BACKLOG = os.path.join(LIVE, "enhancement_backlog.json")


def load(p, default):
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return default


def main(argv):
    done = load(DONE, {})

    if "--list" in argv:
        bl = load(BACKLOG, {"items": []})
        for it in bl.get("items", []):
            if it.get("status") != "done":
                print(f'{it["id"]}  [{it["kind"]}] {it["site"]}: {it["label"]}')
        return 0

    undo = "--undo" in argv
    note = ""
    if "--note" in argv:
        i = argv.index("--note")
        note = argv[i + 1] if i + 1 < len(argv) else ""
        argv = argv[:i] + argv[i + 2:]
    ids = [a for a in argv if not a.startswith("--")]
    if not ids:
        print("No ids given. Use --list to see open ids.")
        return 2

    if undo:
        for i in ids:
            done.pop(i, None)
        print(f"Reopened {len(ids)} item(s).")
    else:
        stamp = datetime.now().isoformat()
        for i in ids:
            done[i] = {"done_at": stamp, "note": note}
        print(f"Marked {len(ids)} item(s) done" + (f' — "{note}"' if note else ""))

    with open(DONE, "w") as f:
        json.dump(done, f, indent=2)
    print("Run build_enhancement_backlog.py (or the daily refresh) to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
