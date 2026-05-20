#!/usr/bin/env python3
"""
build_indexing_health.py — unified indexing rollup.

Consumes:
  - indexing_activity.json     (per-day API submission counts as recorded by submit_google_indexing.py)
  - google_indexing_log.json   (per-URL submission status, ground truth)
  - gsc_coverage.json          (manual GSC export — indexed/not-indexed; usually only R4)
  - manual_indexing_queue.json (top URLs to paste into URL Inspection)

Writes:
  - indexing_health.json with per_site + fleet_summary

Trust order on disagreement:
  google_indexing_log.json (per-URL) > indexing_activity.json (rollup).
  The rollup has historically over-counted success because it records
  what was submitted, not what Google accepted.
"""
import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
LIVE = PROJECT_DIR / "src" / "data" / "live"

SITES = ["rank4ai", "market-invoice", "seocompare", "bestbusinessloans", "fundbiz", "cardmachines", "kartapay", "peptideclear"]

NOW = datetime.now(timezone.utc)
TODAY = NOW.date()
TODAY_STR = TODAY.isoformat()


def load_json(name, default=None):
    p = LIVE / name
    if not p.exists():
        return default if default is not None else {}, None
    try:
        with open(p) as f:
            data = json.load(f)
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        return data, mtime
    except Exception:
        return default if default is not None else {}, None


def submission_breakdown(submissions, since=None):
    """Count submissions by status, optionally filtered by ISO timestamp prefix or cutoff."""
    if since is not None:
        if isinstance(since, str):
            filtered = [s for s in submissions if (s.get("submitted_at") or "").startswith(since)]
        else:
            filtered = [s for s in submissions if (s.get("submitted_at") or "") >= since.isoformat()]
    else:
        filtered = submissions
    counts = Counter(s.get("status") for s in filtered)
    return {
        "submitted": len(filtered),
        "ok": counts.get("ok", 0),
        "error": counts.get("error", 0),
        "success_rate": round(counts.get("ok", 0) / len(filtered) * 100, 1) if filtered else None,
    }


def site_health(site_id, log_data, activity_last_run, coverage_data, queue_data):
    submissions = (log_data.get(site_id) or {}).get("submissions", [])

    # Per-URL ground truth (last 500 entries kept by submit_google_indexing.py)
    today = submission_breakdown(submissions, since=TODAY_STR)
    seven_days_ago = NOW - timedelta(days=7)
    last_7d = submission_breakdown(submissions, since=seven_days_ago)
    all_time = submission_breakdown(submissions)

    # Activity rollup view (what the script *thinks* happened — kept for diff)
    activity_today = (activity_last_run.get("per_site") or {}).get(site_id, {}) if activity_last_run else {}

    # GSC coverage — only present where Adam has uploaded an XLSX
    coverage = (coverage_data.get(site_id) or {}).get("coverage")

    # Manual queue
    queue = (queue_data.get("per_site") or {}).get(site_id, {}) if queue_data else {}

    # Last submission timestamp (regardless of status)
    last_sub = submissions[-1].get("submitted_at") if submissions else None

    # Status assessment
    reasons = []
    status = "healthy"
    if today["submitted"] == 0:
        status = "warning"
        reasons.append("No submissions recorded today")
    elif today["success_rate"] is not None:
        if today["success_rate"] < 50:
            status = "error"
            reasons.append(f"Today's success rate {today['success_rate']}% — likely quota or auth issue")
        elif today["success_rate"] < 90:
            status = "warning"
            reasons.append(f"Today's success rate {today['success_rate']}% (below 90%)")
    # Cross-check the rollup
    if activity_today and activity_today.get("success", 0) > today["ok"] + 5:
        reasons.append(
            f"indexing_activity rollup claims {activity_today.get('success')} success but per-URL log shows only {today['ok']} — rollup is over-counting"
        )

    return {
        "site_id": site_id,
        "today": today,
        "last_7d": last_7d,
        "all_time": all_time,
        "activity_rollup_today": activity_today,
        "last_submission_at": last_sub,
        "gsc_coverage": coverage,
        "manual_queue": {
            "never_api_submitted": queue.get("never_api_submitted"),
            "sitemap_url_count": queue.get("sitemap_url_count"),
            "top_5": (queue.get("top") or [])[:5],
        },
        "status": status,
        "status_reasons": reasons,
    }


def main():
    log_data, _ = load_json("google_indexing_log.json", {})
    activity, _ = load_json("indexing_activity.json", {})
    coverage_data, _ = load_json("gsc_coverage.json", {})
    queue_data, _ = load_json("manual_indexing_queue.json", {})

    activity_last_run = activity.get("last_run") if isinstance(activity, dict) else None

    per_site = {}
    for site in SITES:
        per_site[site] = site_health(site, log_data, activity_last_run, coverage_data, queue_data)

    # Fleet summary
    total_today = sum(per_site[s]["today"]["submitted"] for s in SITES)
    ok_today = sum(per_site[s]["today"]["ok"] for s in SITES)
    err_today = sum(per_site[s]["today"]["error"] for s in SITES)
    sites_healthy = sum(1 for s in SITES if per_site[s]["status"] == "healthy")
    sites_warning = sum(1 for s in SITES if per_site[s]["status"] == "warning")
    sites_error = sum(1 for s in SITES if per_site[s]["status"] == "error")

    fleet = {
        "submissions_today": total_today,
        "ok_today": ok_today,
        "error_today": err_today,
        "fleet_success_rate_today": round(ok_today / total_today * 100, 1) if total_today else None,
        "sites_healthy": sites_healthy,
        "sites_warning": sites_warning,
        "sites_error": sites_error,
        "sites_with_gsc_coverage": sum(1 for s in SITES if per_site[s]["gsc_coverage"]),
    }

    out = {
        "computed_at": NOW.isoformat(),
        "per_site": per_site,
        "fleet_summary": fleet,
    }

    out_path = LIVE / "indexing_health.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    # CLI output
    print(f"build_indexing_health.py — {TODAY}")
    for s in SITES:
        d = per_site[s]
        t = d["today"]
        flag = {"healthy": "✓", "warning": "⚠", "error": "✗"}[d["status"]]
        sr = f"{t['success_rate']}%" if t["success_rate"] is not None else "—"
        print(f"  {flag} {s}: today {t['ok']}/{t['submitted']} ({sr}) · 7d {d['last_7d']['ok']}/{d['last_7d']['submitted']}")
        for r in d["status_reasons"]:
            print(f"      ↳ {r}")
    print(f"\n  fleet today: {ok_today}/{total_today} ({fleet['fleet_success_rate_today']}%)")
    print(f"  written to: {out_path}")


if __name__ == "__main__":
    main()
