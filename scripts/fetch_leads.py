#!/usr/bin/env python3
"""Fetch Market Invoice lead submissions from Supabase.

Produces src/data/live/mi_leads.json:
  {
    "fetched_at": ISO-8601,
    "count_7d": int, "count_30d": int, "count_total": int,
    "funnel_7d": {"form_view": int, "step_1_complete": int, "form_submit": int},
    "sources_30d": [{"source": str, "count": int}, ...],
    "recent_leads": [{...}]  # 20 most recent rows (submit first)
  }

Free to run frequently, no API cost. Run daily via refresh_all.py.
"""
import json
import os
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

SUPABASE_URL = "https://tsscscjcxbzhicuuhter.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzc2NzY2pjeGJ6aGljdXVodGVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwMzU1NDEsImV4cCI6MjA5MTYxMTU0MX0.Q4z8-zHq0RAjZ1Vnv339JwAY36aq5TvnDBwE7OvUNOM"
OUTPUT = os.path.expanduser("~/rank4ai-dashboard/src/data/live/mi_leads.json")


def fetch(path: str, params: dict):
    query = urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/{path}?{query}",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()
    month_ago = (now - timedelta(days=30)).isoformat()

    # All leads from last 30 days (will re-use for sources + funnel)
    recent = fetch(
        "market_invoice_leads",
        {
            "select": "*",
            "created_at": f"gte.{month_ago}",
            "order": "created_at.desc",
            "limit": 500,
        },
    )

    # Totals
    total_7d = sum(1 for r in recent if r["created_at"] >= week_ago)
    total_30d = len(recent)

    # All-time count via count header
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/market_invoice_leads?select=id",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Prefer": "count=exact",
            "Range": "0-0",
        },
        method="HEAD",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            cr = r.headers.get("Content-Range", "")  # like "0-0/123"
            total_all = int(cr.rsplit("/", 1)[-1]) if "/" in cr else total_30d
    except Exception:
        total_all = total_30d

    # Funnel (7d): form_view count via GA4 we don't have here; we use submit/step1 for Supabase funnel
    # step_1_complete (anyone who hit "Next") and form_submit (full lead)
    step1_7d = sum(
        1 for r in recent
        if r["created_at"] >= week_ago and r.get("event_type") == "step_1_complete"
    )
    submit_7d = sum(
        1 for r in recent
        if r["created_at"] >= week_ago and r.get("event_type") == "form_submit"
    )
    # "test" and other event types excluded

    # Conversion % (submit / step_1_complete)
    conv_pct = round(100 * submit_7d / step1_7d, 1) if step1_7d > 0 else 0.0

    # Source breakdown (30d, submit + step_1_complete only, deduplicated by session-like key)
    from collections import Counter
    sources_counter = Counter()
    for r in recent:
        if r.get("event_type") in ("form_submit", "step_1_complete"):
            src = r.get("source") or "unknown"
            sources_counter[src] += 1
    sources = [{"source": k, "count": v} for k, v in sources_counter.most_common(10)]

    # Recent 20 rows: prefer submits, then step 1
    def sort_key(r):
        kind_rank = {"form_submit": 0, "step_1_complete": 1}.get(r.get("event_type"), 2)
        return (kind_rank, r["created_at"])
    recent_display = sorted(recent, key=sort_key)[:20]

    payload = {
        "fetched_at": now.isoformat(),
        "count_total": total_all,
        "count_30d": total_30d,
        "count_7d": total_7d,
        "funnel_7d": {
            "step_1_complete": step1_7d,
            "form_submit": submit_7d,
            "conversion_pct": conv_pct,
        },
        "sources_30d": sources,
        "recent_leads": recent_display,
    }

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {OUTPUT}: total={total_all}, 30d={total_30d}, 7d={total_7d}, submit_7d={submit_7d}, step1_7d={step1_7d}")


if __name__ == "__main__":
    main()
