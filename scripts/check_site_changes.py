#!/usr/bin/env python3
"""
Check site repos for recent changes and verify the dashboard has picked them up.
Runs daily as part of guardrails. Logs what changed and flags if crawl data is stale.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta

LIVE_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
OUTPUT = os.path.join(LIVE_DIR, "site_changelog.json")

REPOS = {
    "rank4ai": {
        "owner": "AdamParkerRank4AI",
        "repo": "rank4ai-preview",
        "local": os.path.expanduser("~/rank4ai-site"),
        "crawl_file": "crawl_rank4ai.json",
    },
    "market-invoice": {
        "owner": "AdamParkerRank4AI",
        "repo": "market-invoice",
        "local": os.path.expanduser("~/compare-invoice-finance"),
        "crawl_file": "crawl_market-invoice.json",
    },
    "seocompare": {
        "owner": "AdamParkerRank4AI",
        "repo": "seocompare",
        "local": os.path.expanduser("~/compareaiseo"),
        "crawl_file": "crawl_seocompare.json",
    },
    "rank4ai-dashboard": {
        "owner": "AdamParkerRank4AI",
        "repo": "rank4ai-dashboard",
        "local": os.path.expanduser("~/rank4ai-dashboard"),
        "crawl_file": None,
    },
}


def get_recent_commits(local_path, days=7):
    """Get commits from the last N days from local git repo."""
    try:
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        result = subprocess.run(
            ["git", "log", f"--since={since}", "--pretty=format:%H|%ai|%s", "--no-merges"],
            capture_output=True, text=True, timeout=10,
            cwd=local_path,
        )
        if result.returncode != 0:
            return []

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) == 3:
                commits.append({
                    "hash": parts[0][:8],
                    "date": parts[1][:19],
                    "message": parts[2][:200],
                })
        return commits
    except Exception as e:
        print(f"  Error reading git log: {e}")
        return []


def get_changed_files(local_path, days=1):
    """Get files changed in the last N days."""
    try:
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        result = subprocess.run(
            ["git", "log", f"--since={since}", "--name-only", "--pretty=format:", "--no-merges"],
            capture_output=True, text=True, timeout=10,
            cwd=local_path,
        )
        if result.returncode != 0:
            return []
        files = [f for f in result.stdout.strip().split("\n") if f.strip()]
        return list(set(files))
    except:
        return []


def check_crawl_freshness(crawl_file):
    """Check if crawl data is newer than the latest commit."""
    path = os.path.join(LIVE_DIR, crawl_file)
    if not os.path.exists(path):
        return None, "no crawl data"
    mtime = datetime.fromtimestamp(os.path.getmtime(path))
    age_hours = (datetime.now() - mtime).total_seconds() / 3600
    return mtime, f"{age_hours:.0f}h ago"


def count_new_pages(changed_files):
    """Count how many new pages were added based on changed files."""
    page_dirs = ["src/pages/", "src/content/"]
    new_pages = [f for f in changed_files if any(f.startswith(d) for d in page_dirs)]
    return new_pages


def main():
    print("Checking site changelogs...")
    results = {}
    alerts = []

    for site_id, config in REPOS.items():
        local = config["local"]
        print(f"\n  {site_id}:")

        if not os.path.exists(local):
            print(f"    Local repo not found: {local}")
            results[site_id] = {"error": "local repo not found"}
            continue

        # Pull latest
        subprocess.run(
            ["git", "fetch", "origin"],
            capture_output=True, text=True, timeout=15,
            cwd=local,
        )

        # Get recent commits (90 days for full history)
        commits = get_recent_commits(local, days=90)
        today_commits = get_recent_commits(local, days=1)
        changed_today = get_changed_files(local, days=1)
        new_pages = count_new_pages(changed_today)

        print(f"    Last 7 days: {len(commits)} commits")
        print(f"    Last 24h: {len(today_commits)} commits, {len(changed_today)} files changed")
        if new_pages:
            print(f"    New pages: {len(new_pages)}")

        # Check if crawl is up to date
        crawl_status = None
        if config["crawl_file"]:
            crawl_mtime, crawl_age = check_crawl_freshness(config["crawl_file"])
            print(f"    Crawl data: {crawl_age}")

            # If site was updated today but crawl is older, flag it
            if today_commits and crawl_mtime:
                latest_commit_date = today_commits[0]["date"][:10]
                crawl_date = crawl_mtime.strftime("%Y-%m-%d")
                if crawl_date < latest_commit_date:
                    crawl_status = "stale"
                    msg = f"{site_id}: site updated today ({len(today_commits)} commits) but crawl data is from {crawl_date}"
                    alerts.append(msg)
                    print(f"    !! STALE: {msg}")

        results[site_id] = {
            "checked_at": datetime.now().isoformat(),
            "commits_7d": len(commits),
            "commits_24h": len(today_commits),
            "files_changed_24h": len(changed_today),
            "new_pages_24h": len(new_pages),
            "recent_commits": commits[:10],
            "changed_files": changed_today[:50],
            "new_page_files": new_pages[:20],
            "crawl_status": crawl_status or "ok",
        }

        # Print latest commits
        for c in commits[:5]:
            print(f"    {c['date'][:10]} {c['hash']} {c['message'][:60]}")

    # Merge with existing history (keep last 90 days of commits)
    existing = {}
    if os.path.exists(OUTPUT):
        try:
            with open(OUTPUT) as f:
                existing = json.load(f)
        except:
            pass

    for site_id, data in results.items():
        if "error" in data:
            continue
        old = existing.get(site_id, {})
        old_commits = old.get("all_commits", [])
        new_commits = data.get("recent_commits", [])

        # Merge — dedupe by hash
        seen = set()
        merged = []
        for c in new_commits + old_commits:
            if c["hash"] not in seen:
                seen.add(c["hash"])
                merged.append(c)

        # Sort by date desc, keep last 500
        merged.sort(key=lambda x: x["date"], reverse=True)
        data["all_commits"] = merged[:500]

    # Save
    with open(OUTPUT, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved → {OUTPUT}")

    # Alert if sites changed but dashboard didn't update
    if alerts:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from notify import send_failure_alert
            send_failure_alert(
                "Site Changes Not Reflected",
                alerts,
                log_file="/tmp/rank4ai_guardrails.log",
            )
        except:
            pass

    return len(alerts)


if __name__ == "__main__":
    sys.exit(main())
