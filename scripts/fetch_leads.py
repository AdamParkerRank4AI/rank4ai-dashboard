#!/usr/bin/env python3
"""Fetch lead submissions from Supabase across all 4 commercial sites.

Tables (all on same Supabase project tsscscjcxbzhicuuhter):
  market_invoice_leads  → mi_leads.json
  bestbusinessloans_leads → bbl_leads.json
  fundbiz_leads         → fundbiz_leads.json
  merchanthq_leads      → cardmachines_leads.json

Per-site payload:
  {
    "fetched_at": ISO-8601,
    "count_7d" / "count_30d" / "count_total": int,
    "funnel_7d": {"step_1_complete": int, "form_submit": int, "conversion_pct": float},
    "sources_30d": [{"source": str, "count": int}, ...],
    "recent_leads": [{...}]
  }

Free to run frequently, no API cost. Daily via refresh_all.py.
"""
import json
import os
import urllib.request
import urllib.parse
from collections import Counter
from datetime import datetime, timedelta, timezone

SUPABASE_URL = "https://tsscscjcxbzhicuuhter.supabase.co"
# Prefer the service_role key (from env) so we can READ the insert-only lead
# tables. BBL/FundBiz/MHQ/Kartapay allow anon INSERT but block anon SELECT via
# RLS, so the anon key returns a false 0 for them. service_role bypasses RLS.
# Falls back to anon (which works for MI's permissive select policy).
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzc2NzY2pjeGJ6aGljdXVodGVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwMzU1NDEsImV4cCI6MjA5MTYxMTU0MX0.Q4z8-zHq0RAjZ1Vnv339JwAY36aq5TvnDBwE7OvUNOM"
OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")

# Hold-back window: ignore step_1_complete rows newer than this. The user might
# still submit, so counting a fresh step-1 row inflates the abandon number.
STEP1_HOLDBACK_MINUTES = 5

# Map dashboard site_id → (Supabase table, output filename)
SITE_TABLES = {
    "market-invoice":    ("market_invoice_leads",    "mi_leads.json"),
    "bestbusinessloans": ("bestbusinessloans_leads", "bbl_leads.json"),
    "fundbiz":           ("fundbiz_leads",           "fundbiz_leads.json"),
    "cardmachines":      ("merchanthq_leads",        "cardmachines_leads.json"),
    "kartapay":          ("kartapay_leads",          "kartapay_leads.json"),
    "peptideclear":      ("peptideclear_leads",      "peptideclear_leads.json"),
}


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


def head_count(table: str) -> int:
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/{table}?select=id",
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
            cr = r.headers.get("Content-Range", "")
            return int(cr.rsplit("/", 1)[-1]) if "/" in cr else 0
    except Exception:
        return 0


def build_payload(site_id: str, table: str, now: datetime, week_ago: str, month_ago: str) -> dict:
    try:
        recent = fetch(table, {
            "select": "*",
            "created_at": f"gte.{month_ago}",
            "order": "created_at.desc",
            "limit": 500,
        })
    except Exception as e:
        print(f"  {site_id}: fetch failed ({e}) — table may not exist yet, writing empty payload")
        recent = []

    holdback_cutoff = (now - timedelta(minutes=STEP1_HOLDBACK_MINUTES)).isoformat()
    recent = [
        r for r in recent
        if not (r.get("event_type") == "step_1_complete" and r["created_at"] >= holdback_cutoff)
    ]

    total_7d = sum(1 for r in recent if r["created_at"] >= week_ago)
    total_30d = len(recent)
    total_all = head_count(table) if recent else 0

    step1_7d = sum(
        1 for r in recent
        if r["created_at"] >= week_ago and r.get("event_type") == "step_1_complete"
    )
    submit_7d = sum(
        1 for r in recent
        if r["created_at"] >= week_ago and r.get("event_type") == "form_submit"
    )
    conv_pct = round(100 * submit_7d / step1_7d, 1) if step1_7d > 0 else 0.0

    sources_counter = Counter()
    for r in recent:
        if r.get("event_type") in ("form_submit", "step_1_complete"):
            src = r.get("source") or "unknown"
            sources_counter[src] += 1
    sources = [{"source": k, "count": v} for k, v in sources_counter.most_common(10)]

    def sort_key(r):
        kind_rank = {"form_submit": 0, "step_1_complete": 1}.get(r.get("event_type"), 2)
        return (kind_rank, r["created_at"])
    recent_display = sorted(recent, key=sort_key)[:20]

    return {
        "fetched_at": now.isoformat(),
        "site_id": site_id,
        "table": table,
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


def main():
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()
    month_ago = (now - timedelta(days=30)).isoformat()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for site_id, (table, fname) in SITE_TABLES.items():
        payload = build_payload(site_id, table, now, week_ago, month_ago)
        out = os.path.join(OUTPUT_DIR, fname)
        with open(out, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"  {site_id}: total={payload['count_total']}, 30d={payload['count_30d']}, 7d={payload['count_7d']}, submit_7d={payload['funnel_7d']['form_submit']}")


if __name__ == "__main__":
    main()
