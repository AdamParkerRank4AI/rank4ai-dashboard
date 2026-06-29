#!/usr/bin/env python3
"""archive_ai_fetches.py — build a DAILY history of live AI fetches for the fleet.

WHY (Adam, 29 Jun 2026): the Fleet Growth chart has a Bing-citations line, but the
bigger signal — user-triggered AI fetches (ChatGPT / Perplexity / Claude pulling our
pages live to answer someone) — had no daily history, because fleet_bot_hits.json is
only a rolling snapshot. This archives a per-day fleet total (+ per-engine split) so
that activity becomes a growth line too.

Self-healing: recomputes the trailing window from the raw Supabase rows each run
(authoritative for whatever Supabase still retains) and preserves any older days
already archived — so it seeds real history on first run AND stays correct daily.

Reads the same table + creds as the other fetchers (READ-ONLY).
Writes src/data/live/ai_fetch_history.json:
  {"generated_at": "...", "days": [{"date","total","openai","perplexity","claude","other"}, ...]}
"""
import json
import os
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone

SUPABASE_URL = "https://tsscscjcxbzhicuuhter.supabase.co"
TABLE = "fleet_bot_hits"
WINDOW_DAYS = 35  # trailing window recomputed each run (Supabase retention permitting)
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "src", "data", "live", "ai_fetch_history.json")


def supabase_key():
    k = os.environ.get("SUPABASE_SERVICE_KEY")
    if not k:
        p = os.path.expanduser("~/.supabase-service-key")
        if os.path.exists(p):
            k = open(p).read().strip()
    return k


def engine_of(bot_name):
    s = (bot_name or "").lower()
    if "perplexity" in s:
        return "perplexity"
    if "claude" in s or "anthropic" in s:
        return "claude"
    if "chatgpt" in s or "oai-" in s or "gptbot" in s or "openai" in s:
        return "openai"
    return "other"


def fetch_rows(key, since_iso):
    cols = "bot_name,created_at"
    rows, off = [], 0
    while True:
        q = (f"{SUPABASE_URL}/rest/v1/{TABLE}?select={cols}"
             f"&bot_category=in.(ai-user,ai-search)"
             f"&created_at=gt.{urllib.parse.quote(since_iso)}"
             f"&order=created_at.asc&limit=1000&offset={off}")
        req = urllib.request.Request(q, headers={"apikey": key, "Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=40) as r:
            batch = json.loads(r.read().decode())
        rows.extend(batch)
        if len(batch) < 1000:
            break
        off += 1000
    return rows


def main():
    key = supabase_key()
    if not key:
        print("no Supabase service key — skipping"); return
    since = (datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)).strftime("%Y-%m-%dT%H:%M:%S")
    rows = fetch_rows(key, since)

    # bucket the trailing window by date + engine
    win = defaultdict(lambda: defaultdict(int))
    for r in rows:
        ts = (r.get("created_at") or "")[:10]
        if not ts:
            continue
        win[ts]["total"] += 1
        win[ts][engine_of(r.get("bot_name"))] += 1

    # merge with existing archive: preserve days OLDER than the window, overwrite the rest
    existing = {}
    try:
        old = json.load(open(OUT))
        for d in old.get("days", []):
            existing[d["date"]] = d
    except Exception:
        pass
    window_start = (datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)).strftime("%Y-%m-%d")
    merged = {dt: d for dt, d in existing.items() if dt < window_start}  # keep older archived days
    for dt, eng in win.items():
        merged[dt] = {
            "date": dt,
            "total": eng["total"],
            "openai": eng["openai"],
            "perplexity": eng["perplexity"],
            "claude": eng["claude"],
            "other": eng["other"],
        }

    days = [merged[k] for k in sorted(merged)]
    out = {"generated_at": datetime.now(timezone.utc).isoformat(), "days": days}
    json.dump(out, open(OUT, "w"), indent=1)
    tail = days[-1] if days else {}
    print(f"archive_ai_fetches: {len(days)} days, latest {tail.get('date')} total={tail.get('total')} "
          f"(openai {tail.get('openai')}, perplexity {tail.get('perplexity')})")


if __name__ == "__main__":
    main()
