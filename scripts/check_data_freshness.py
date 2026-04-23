#!/usr/bin/env python3
"""Daily data-freshness guardrail.

Checks every dashboard data file has an internal timestamp matching its
expected schedule. Catches bugs like:
- pagespeed.json: script runs daily but rate-limited, fetched_at stays stale
- competitor_serp.json: script runs but forgets to record timestamp
- any fetcher silently failing while refresh_all.py reports OK

Exits 0 and writes src/data/live/data_freshness.json so the dashboard can
surface it. Sends email alert if anything is red.
"""
import json
import os
import sys
from datetime import datetime, timedelta

LIVE = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
OUTPUT = os.path.join(LIVE, "data_freshness.json")

# (file, expected max age in hours, label, timestamp path)
# Path is a list of keys; site-level files use "*" to check any site's value
FEEDS = [
    # Daily
    ("ga4.json",                 30, "GA4 (traffic)",          ["*", "fetched_at"]),
    ("gsc.json",                 30, "GSC (search perf)",       ["*", "fetched_at"]),
    ("bing.json",                30, "Bing Webmaster",          ["*", "fetched_at"]),
    ("uptime.json",              30, "Uptime",                  ["*", "checked_at"]),
    ("crawl_activity.json",      30, "Bing crawl stats",        ["*", "fetched_at"]),
    ("bot_hits.json",            30, "AI bot hits",             ["*", "fetched_at"]),
    ("knowledge_graph.json",     30, "Knowledge Graph",         ["*", "fetched_at"]),
    ("nlp_entities.json",        30, "NLP entities",            ["*", "fetched_at"]),
    ("ai_overview_serp.json",    30, "AI Overviews SERP",       ["*", "fetched_at"]),
    ("ai_audit.json",            30, "AI audit",                ["*", "audited_at"]),
    ("recommendations.json",     30, "Recommendations",         ["*", "generated_at"]),
    ("competitor_serp.json",     30, "Competitor SERP",         ["*", "checked_at"]),
    ("new_pages.json",           30, "New-page scan",           ["*", "checked_at"]),
    ("serp_data.json",           30, "SERP data",               ["*", "fetched_at"]),
    ("crawl_rank4ai.json",       30, "R4 site crawl",           ["crawled_at"]),
    ("crawl_market-invoice.json",30, "MI site crawl",           ["crawled_at"]),
    ("crawl_seocompare.json",    30, "SC site crawl",           ["crawled_at"]),
    ("mi_leads.json",            30, "MI leads (Supabase)",     ["fetched_at"]),
    ("daily_audit_summary.json", 30, "Daily site audit",        ["generated_at"]),

    # Weekly
    ("pagespeed.json",          8*24, "PageSpeed (weekly)",     ["_meta", "last_run_at"]),
    ("citation_results.json",   8*24, "Citation baseline",      ["*", "tested_at"]),
    ("citations_by_type.json",  8*24, "Citation by type",       ["*", "tested_at"]),
    ("google_trends.json",      8*24, "Google Trends",          ["*", "fetched_at"]),

    # Static reference (but track staleness)
    ("citation_prompts.json",   30,   "Citation prompts",       None),  # no internal ts, use mtime
]


def get_nested(obj, path):
    """Resolve a dotted path, with '*' meaning 'any sub-dict value'."""
    if not path:
        return None
    if isinstance(obj, dict) and path[0] == "*":
        for v in obj.values():
            if isinstance(v, dict):
                got = get_nested(v, path[1:])
                if got:
                    return got
        return None
    if isinstance(obj, dict) and path[0] in obj:
        if len(path) == 1:
            return obj[path[0]]
        return get_nested(obj[path[0]], path[1:])
    return None


def check_feed(filename, max_age_hours, label, ts_path):
    path = os.path.join(LIVE, filename)
    if not os.path.exists(path):
        return {"file": filename, "label": label, "status": "missing",
                "age_hours": None, "ts": None, "max_age_hours": max_age_hours}

    # Internal timestamp
    ts = None
    if ts_path:
        try:
            with open(path) as f:
                data = json.load(f)
            ts = get_nested(data, ts_path)
        except Exception:
            ts = None

    # Fallback to file mtime
    used_mtime = False
    if not ts:
        ts_dt = datetime.fromtimestamp(os.path.getmtime(path))
        used_mtime = True
    else:
        try:
            ts_str = str(ts).replace("Z", "+00:00")
            # Strip timezone to compare as naive (local)
            ts_dt = datetime.fromisoformat(ts_str)
            if ts_dt.tzinfo is not None:
                ts_dt = ts_dt.replace(tzinfo=None)
        except Exception:
            ts_dt = datetime.fromtimestamp(os.path.getmtime(path))
            used_mtime = True

    age_h = (datetime.now() - ts_dt).total_seconds() / 3600

    if age_h > max_age_hours * 3:
        status = "very_stale"
    elif age_h > max_age_hours:
        status = "stale"
    else:
        status = "fresh"

    return {
        "file": filename, "label": label, "status": status,
        "age_hours": round(age_h, 1),
        "ts": ts_dt.isoformat(),
        "max_age_hours": max_age_hours,
        "used_mtime_fallback": used_mtime,
    }


def main():
    results = [check_feed(*f) for f in FEEDS]

    fresh = sum(1 for r in results if r["status"] == "fresh")
    stale = sum(1 for r in results if r["status"] == "stale")
    very_stale = sum(1 for r in results if r["status"] == "very_stale")
    missing = sum(1 for r in results if r["status"] == "missing")

    # Sort worst first
    order = {"missing": 0, "very_stale": 1, "stale": 2, "fresh": 3}
    results.sort(key=lambda r: (order[r["status"]], -(r.get("age_hours") or 0)))

    payload = {
        "checked_at": datetime.now().isoformat(),
        "summary": {
            "fresh": fresh,
            "stale": stale,
            "very_stale": very_stale,
            "missing": missing,
            "total": len(results),
        },
        "feeds": results,
    }
    with open(OUTPUT, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Data freshness: {fresh} fresh, {stale} stale, {very_stale} very stale, {missing} missing")
    for r in results:
        if r["status"] != "fresh":
            age = f"{r['age_hours']:.1f}h" if r["age_hours"] is not None else "n/a"
            print(f"  [{r['status'].upper()}] {r['label']}: {age} old (limit {r['max_age_hours']}h)")

    # Alert via notify.py if any red
    alerts = [r for r in results if r["status"] in ("very_stale", "missing")]
    if alerts:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from notify import send_failure_alert
            lines = [f"{r['label']}: {r['status']} (age {r['age_hours']}h, limit {r['max_age_hours']}h)" for r in alerts]
            send_failure_alert("Dashboard data freshness", lines)
        except Exception as e:
            print(f"  (alert failed: {e})")


if __name__ == "__main__":
    main()
