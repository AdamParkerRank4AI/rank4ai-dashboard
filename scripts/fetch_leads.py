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
def _service_key_from_file():
    p = os.path.expanduser("~/.supabase-service-key")
    try:
        return open(p).read().strip() if os.path.exists(p) else ""
    except Exception:
        return ""

SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or _service_key_from_file() or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzc2NzY2pjeGJ6aGljdXVodGVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwMzU1NDEsImV4cCI6MjA5MTYxMTU0MX0.Q4z8-zHq0RAjZ1Vnv339JwAY36aq5TvnDBwE7OvUNOM"
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
    "seocompare":        ("seocompare_leads",        "seocompare_leads.json"),
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


# Sources that are NOT real external leads — internal/test submissions, staff
# fills, fee/admin rows. These must never be counted as leads (Adam 15 Jun: an
# "internal"-source row was showing on the lead tab as if it were a real lead).
INTERNAL_SOURCES = {"internal", "test", "fee", "admin", "staff", "qa"}


def _is_internal(row: dict) -> bool:
    return str(row.get("source") or "").strip().lower() in INTERNAL_SOURCES


def head_count(table: str) -> int:
    # Count only real leads — exclude internal/test sources at the query level so
    # the all-time total matches the (internal-stripped) recent counts.
    src_filter = ",".join(sorted(INTERNAL_SOURCES))
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/{table}?select=id&source=not.in.({src_filter})",
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

    # Strip internal/test rows so they never count as real leads or pollute the
    # source breakdown (e.g. a "fee"/"internal"-source row is not a lead).
    recent = [r for r in recent if not _is_internal(r)]

    # Submit-shaped event types across the fleet. 2026-05-28: added
    # form_submit_serverside (MI/MHQ server-side capture) and quote_request
    # (MHQ bespoke form). Null event_type with email+phone is also treated
    # as a submit (some sites' forms don't set event_type explicitly).
    SUBMIT_TYPES = {"form_submit", "form_submit_serverside", "quote_request", "submit"}
    def is_submit(r):
        et = (r.get("event_type") or "").strip()
        if et in SUBMIT_TYPES:
            return True
        return (not et) and bool(r.get("email")) and bool(r.get("phone"))

    # Dedup near-duplicate submits 2026-05-30: the defense-in-depth pattern
    # writes BOTH form_submit (client-side direct write from fleet-core) AND
    # form_submit_serverside (server-side from /api/<site>-lead-submit) for
    # every real submit, often <100ms apart. Without dedup the funnel reports
    # 200% conversion. Group by email within a 2-min window — counts each
    # unique submit once.
    def dedup_submits(rows):
        seen = {}
        kept_ids = set()
        from datetime import datetime as dt
        for r in sorted(rows, key=lambda x: x["created_at"]):
            if not is_submit(r):
                continue
            email = (r.get("email") or "").lower().strip()
            if not email:
                kept_ids.add(r["id"])
                continue
            try:
                ts = dt.fromisoformat(r["created_at"].replace("Z", "+00:00")).timestamp()
            except Exception:
                ts = 0
            key = email
            prev_ts = seen.get(key)
            if prev_ts is None or (ts - prev_ts) > 120:  # >2 min apart = different submit
                kept_ids.add(r["id"])
                seen[key] = ts
        return kept_ids
    deduped_submit_ids = dedup_submits(recent)

    total_7d = sum(1 for r in recent if r["created_at"] >= week_ago)
    total_30d = len(recent)
    total_all = head_count(table) if recent else 0

    step1_7d = sum(
        1 for r in recent
        if r["created_at"] >= week_ago and r.get("event_type") == "step_1_complete"
    )
    # Use deduped set so client+server pair counts as 1
    submit_7d = sum(1 for r in recent if r["created_at"] >= week_ago and r["id"] in deduped_submit_ids)
    conv_pct = round(100 * submit_7d / step1_7d, 1) if step1_7d > 0 else 0.0

    sources_counter = Counter()
    for r in recent:
        if is_submit(r) or r.get("event_type") == "step_1_complete":
            src = r.get("source") or "unknown"
            sources_counter[src] += 1
    sources = [{"source": k, "count": v} for k, v in sources_counter.most_common(10)]

    # Collapse the funnel into ONE row per real lead. A single person produces
    # up to 4 rows (step_1_complete, step_2_complete, form_submit AND
    # form_submit_serverside) — showing them all reads as duplicates. Group by
    # company_name, else email, else phone (the step rows carry company_name
    # even when email/phone are still null), keep the furthest stage reached,
    # and merge the most complete field values across the group.
    def _stage_rank(r):
        if is_submit(r):
            return 3
        et = (r.get("event_type") or "")
        if et == "step_2_complete":
            return 2
        if et == "step_1_complete":
            return 1
        return 0

    STAGE_LABEL = {3: "submit", 2: "step 2", 1: "step 1", 0: "other"}

    def _group_key(r):
        for f in ("company_name", "email", "phone"):
            v = (r.get(f) or "").strip().lower()
            if v:
                return f + ":" + v
        return "id:" + str(r.get("id"))  # ungroupable (e.g. empty diagnostic row)

    groups = {}
    for r in recent:
        groups.setdefault(_group_key(r), []).append(r)

    collapsed = []
    for rows in groups.values():
        rep = max(rows, key=lambda r: (_stage_rank(r), r["created_at"]))
        merged = dict(rep)
        # Fill any blank field on the representative from the other rows.
        for r in rows:
            for k, v in r.items():
                if (merged.get(k) in (None, "")) and v not in (None, ""):
                    merged[k] = v
        merged["created_at"] = max(r["created_at"] for r in rows)
        stages = sorted({_stage_rank(r) for r in rows}, reverse=True)
        merged["stages"] = [STAGE_LABEL[s] for s in stages]
        merged["_event_count"] = len(rows)
        collapsed.append(merged)

    # Furthest-stage leads first, then newest.
    collapsed.sort(key=lambda r: (_stage_rank(r), r["created_at"]), reverse=True)
    recent_display = collapsed[:20]

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
