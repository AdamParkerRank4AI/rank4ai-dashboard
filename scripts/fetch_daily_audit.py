#!/usr/bin/env python3
"""
Pull the daily site audit results from iCloud and surface them in the dashboard.

Source: ~/Library/Mobile Documents/com~apple~CloudDocs/claude/Audits/daily-site-audit-YYYY-MM-DD.json
  (written 7am by ~/run_daily_site_audit.py via launchd com.rank4ai.site-audit)

Outputs to ~/rank4ai-dashboard/src/data/live/:
  - daily_audit_<site_id>.json   (latest run, per site)
  - daily_audit_summary.json     (rollup across all 3 sites)
  - daily_audit_history.json     (last 14 days of summary stats per site)
"""

import json
import os
import glob
from datetime import datetime

AUDIT_DIR = os.path.expanduser(
    "~/Library/Mobile Documents/com~apple~CloudDocs/claude/Audits"
)
OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")

# Map audit file site name → dashboard client id (from clients.json)
SITE_ID_MAP = {
    "Rank4AI": "rank4ai",
    "Market Invoice": "market-invoice",
    "SEO Compare": "seocompare",
}


def latest_audit_file():
    files = sorted(glob.glob(os.path.join(AUDIT_DIR, "daily-site-audit-*.json")))
    return files[-1] if files else None


def load_audit(path):
    with open(path) as f:
        return json.load(f)


def per_site_payload(site, audit_date):
    pages = site.get("pages", [])
    issues_total = sum(len(p.get("issues", [])) for p in pages)
    pages_with_issues = [p for p in pages if p.get("issues")]
    return {
        "site_name": site.get("name"),
        "url": site.get("url"),
        "audit_date": audit_date,
        "pages_checked": len(pages),
        "issues_total": issues_total,
        "pages_with_issues": len(pages_with_issues),
        "all_pages": pages,
        "flagged_pages": pages_with_issues,
    }


def append_history(history, site_id, payload):
    entry = {
        "date": payload["audit_date"],
        "pages_checked": payload["pages_checked"],
        "issues_total": payload["issues_total"],
        "pages_with_issues": payload["pages_with_issues"],
    }
    site_history = history.get(site_id, [])
    if site_history and site_history[-1]["date"] == entry["date"]:
        site_history[-1] = entry
    else:
        site_history.append(entry)
    history[site_id] = site_history[-14:]
    return history


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    audit_path = latest_audit_file()
    if not audit_path:
        print(f"No daily audit files found in {AUDIT_DIR}")
        return 1

    audit_date = os.path.basename(audit_path).replace(
        "daily-site-audit-", ""
    ).replace(".json", "")
    print(f"Reading {audit_path} (date: {audit_date})")

    audit = load_audit(audit_path)

    history_path = os.path.join(OUTPUT_DIR, "daily_audit_history.json")
    history = {}
    if os.path.exists(history_path):
        with open(history_path) as f:
            history = json.load(f)

    summary_sites = []
    for site in audit:
        site_name = site.get("name")
        site_id = SITE_ID_MAP.get(site_name)
        if not site_id:
            print(f"  Skipping unmapped site: {site_name}")
            continue

        payload = per_site_payload(site, audit_date)
        out_path = os.path.join(OUTPUT_DIR, f"daily_audit_{site_id}.json")
        with open(out_path, "w") as f:
            json.dump(payload, f, indent=2)
        print(
            f"  {site_id}: {payload['pages_checked']} pages, "
            f"{payload['issues_total']} issues → {os.path.basename(out_path)}"
        )

        history = append_history(history, site_id, payload)

        summary_sites.append(
            {
                "site_id": site_id,
                "site_name": site_name,
                "url": site.get("url"),
                "pages_checked": payload["pages_checked"],
                "issues_total": payload["issues_total"],
                "pages_with_issues": payload["pages_with_issues"],
            }
        )

    summary = {
        "audit_date": audit_date,
        "generated_at": datetime.now().isoformat(),
        "total_sites": len(summary_sites),
        "total_pages_checked": sum(s["pages_checked"] for s in summary_sites),
        "total_issues": sum(s["issues_total"] for s in summary_sites),
        "sites": summary_sites,
    }
    with open(os.path.join(OUTPUT_DIR, "daily_audit_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

    print(
        f"Summary: {summary['total_sites']} sites, "
        f"{summary['total_pages_checked']} pages, "
        f"{summary['total_issues']} issues"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
