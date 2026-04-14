#!/usr/bin/env python3
"""
Guardrails check — runs every refresh, alerts if anything is broken.
Checks all critical systems across all clients.
"""
import json
import os
import sys
from datetime import datetime, timedelta

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)
LIVE_DIR = os.path.join(PROJECT_DIR, "src", "data", "live")
LOG_FILE = "/tmp/rank4ai_guardrails.log"

sys.path.insert(0, SCRIPTS_DIR)
from notify import send_failure_alert

CLIENTS = ["rank4ai", "market-invoice", "seocompare"]


def load(filename):
    try:
        with open(os.path.join(LIVE_DIR, filename)) as f:
            return json.load(f)
    except:
        return None


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def check_file_freshness(filename, max_hours=26):
    """Check a data file isn't stale."""
    path = os.path.join(LIVE_DIR, filename)
    if not os.path.exists(path):
        return f"MISSING: {filename}"
    age_hours = (datetime.now().timestamp() - os.path.getmtime(path)) / 3600
    if age_hours > max_hours:
        return f"STALE: {filename} ({age_hours:.0f}h old, max {max_hours}h)"
    return None


def check_file_not_empty(filename):
    """Check a JSON file isn't empty."""
    data = load(filename)
    if data is None:
        return f"MISSING: {filename}"
    if isinstance(data, dict) and len(data) == 0:
        return f"EMPTY: {filename} (0 keys)"
    if isinstance(data, list) and len(data) == 0:
        return f"EMPTY: {filename} (0 items)"
    return None


def check_client_data(filename, clients=None):
    """Check all clients are present in a multi-client JSON file."""
    clients = clients or CLIENTS
    data = load(filename)
    if not data:
        return [f"MISSING: {filename}"]
    issues = []
    for c in clients:
        if c not in data:
            issues.append(f"MISSING CLIENT: {c} not in {filename}")
        elif isinstance(data[c], dict) and len(data[c]) == 0:
            issues.append(f"EMPTY CLIENT: {c} in {filename}")
    return issues


def main():
    log("=" * 50)
    log("Guardrails check started")
    issues = []

    # 1. GA4 — must have data for all clients
    log("Checking GA4...")
    ga4_issues = check_client_data("ga4.json")
    issues.extend(ga4_issues)
    ga4 = load("ga4.json")
    if ga4:
        for c in CLIENTS:
            d = ga4.get(c, {})
            if d and d.get("overview", {}).get("active_users", 0) == 0:
                issues.append(f"GA4 WARNING: {c} shows 0 users — token may have expired")

    # 2. GSC — must have data for all clients
    log("Checking GSC...")
    issues.extend(check_client_data("gsc.json"))

    # 3. Bing — must have data for all clients
    log("Checking Bing...")
    issues.extend(check_client_data("bing.json"))

    # 4. Crawl files — one per client, must exist and not be empty
    log("Checking crawl data...")
    for c in CLIENTS:
        issue = check_file_not_empty(f"crawl_{c}.json")
        if issue:
            issues.append(issue)

    # 5. Recommendations — must exist for all clients
    log("Checking recommendations...")
    issues.extend(check_client_data("recommendations.json"))

    # 6. Key files freshness (should be updated daily by refresh)
    log("Checking freshness...")
    daily_files = [
        "ga4.json", "gsc.json", "bing.json", "uptime.json",
        "recommendations.json", "daily_history.json",
    ]
    for f in daily_files:
        issue = check_file_freshness(f, max_hours=26)
        if issue:
            issues.append(issue)

    # 7. Crawl files freshness (should be updated daily)
    for c in CLIENTS:
        issue = check_file_freshness(f"crawl_{c}.json", max_hours=26)
        if issue:
            issues.append(issue)

    # 8. AI audit — can be less frequent but shouldn't be more than 7 days
    log("Checking AI audit...")
    issue = check_file_freshness("ai_audit.json", max_hours=168)
    if issue:
        issues.append(issue)

    # 9. Citation results — shouldn't be more than 7 days
    issue = check_file_freshness("citation_results.json", max_hours=168)
    if issue:
        issues.append(issue)

    # 10. PageSpeed — shouldn't be more than 7 days
    issue = check_file_freshness("pagespeed.json", max_hours=168)
    if issue:
        issues.append(issue)

    # 11. Uptime — all clients should be 200
    log("Checking uptime...")
    uptime = load("uptime.json")
    if uptime:
        for c in CLIENTS:
            u = uptime.get(c, {})
            status = u.get("status")
            if status and status != 200:
                issues.append(f"DOWNTIME: {c} returned HTTP {status}")

    # 12. Automated tasks — check marker files exist for today
    log("Checking automated tasks...")
    today = datetime.now().strftime("%Y-%m-%d")
    markers = {
        "questions": os.path.expanduser(f"~/.rank4ai_questions_{today}"),
        "blog": os.path.expanduser(f"~/.rank4ai_blog_{today}"),
    }
    for name, path in markers.items():
        if not os.path.exists(path):
            # Only flag after expected run time
            hour = datetime.now().hour
            if name == "questions" and hour >= 22:
                issues.append(f"TASK FAILED: Daily {name} did not run today")
            elif name == "blog" and hour >= 22:
                issues.append(f"TASK FAILED: Daily {name} did not run today")

    # 13. DataForSEO — check it's not empty
    log("Checking DataForSEO...")
    issue = check_file_not_empty("ai_overview_serp.json")
    if issue:
        issues.append(issue)

    # Summary
    log(f"\nGuardrails check complete: {len(issues)} issues found")

    if issues:
        for i in issues:
            log(f"  !! {i}")

        # Send email alert
        send_failure_alert(
            "Guardrails Check",
            issues,
            log_file=LOG_FILE,
        )
    else:
        log("  All clear — no issues")

    log("=" * 50)
    return len(issues)


if __name__ == "__main__":
    sys.exit(main())
