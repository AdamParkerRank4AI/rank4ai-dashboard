#!/usr/bin/env python3
"""
Refresh all dashboard data and redeploy.
Run daily via launchd to keep the dashboard current.
"""
import subprocess
import sys
import os
from datetime import datetime

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)
LOG_FILE = "/tmp/rank4ai_dashboard_refresh.log"

sys.path.insert(0, SCRIPTS_DIR)
from notify import send_failure_alert


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def run_script(name, timeout=600):
    """Run a data collection script."""
    script_path = os.path.join(SCRIPTS_DIR, name)
    log(f"Running {name}...")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True, timeout=timeout,
            cwd=PROJECT_DIR,
            env={**os.environ},
        )
        if result.returncode == 0:
            log(f"  OK — {name}")
        else:
            stderr = result.stderr[:200] if result.stderr else ""
            # Filter out warnings
            errors = [l for l in stderr.split("\n") if "Warning" not in l and "warnings" not in l and l.strip()]
            if errors:
                log(f"  WARN — {name}: {errors[0]}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log(f"  TIMEOUT — {name} (>{timeout}s)")
        return False
    except Exception as e:
        log(f"  ERROR — {name}: {e}")
        return False


def build_and_deploy():
    """Build Astro and deploy to Cloudflare Pages."""
    log("Building dashboard...")
    result = subprocess.run(
        ["npm", "run", "build"],
        capture_output=True, text=True, timeout=120,
        cwd=PROJECT_DIR,
    )
    if result.returncode != 0:
        log(f"  BUILD FAILED: {result.stderr[:200]}")
        return False

    log("Deploying to Cloudflare Pages...")
    result = subprocess.run(
        ["npx", "wrangler", "pages", "deploy", "dist",
         "--project-name=rank4ai-dashboard", "--branch=main", "--commit-dirty=true"],
        capture_output=True, text=True, timeout=120,
        cwd=PROJECT_DIR,
    )
    if result.returncode != 0:
        log(f"  DEPLOY FAILED: {result.stderr[:200]}")
        return False

    log("  Deployed successfully")
    return True


def main():
    log("=" * 50)
    log("Dashboard refresh started")
    log("=" * 50)

    # Backup current live data before refreshing
    import shutil
    backup_dir = os.path.join(PROJECT_DIR, "src", "data", "live_backup")
    live_dir = os.path.join(PROJECT_DIR, "src", "data", "live")
    try:
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.copytree(live_dir, backup_dir)
        log(f"Backed up live data to live_backup/")
    except Exception as e:
        log(f"Backup failed: {e} — continuing anyway")

    # Run data collection scripts (order matters — crawl first, then analysis)
    scripts = [
        ("check_uptime.py", 30),
        ("fetch_ga4.py", 60),
        ("fetch_gsc.py", 60),
        ("fetch_bing.py", 30),
        ("fetch_crawl_activity.py", 30),
        ("fetch_bot_hits.py", 30),
        ("fetch_pagespeed.py", 120),
        ("extract_entities.py", 30),
        ("fetch_knowledge_graph.py", 30),
        ("fetch_dataforseo.py", 120),
        ("fetch_serp.py", 120),
        ("fetch_competitor_serp.py", 120),
        ("generate_recommendations.py", 30),
        ("track_new_pages.py", 30),
        ("save_daily_metrics.py", 30),
    ]

    results = {}
    for script, timeout in scripts:
        results[script] = run_script(script, timeout)

    # These take longer — run less frequently (check marker)
    today = datetime.now().strftime("%Y-%m-%d")
    crawl_marker = os.path.expanduser(f"~/.rank4ai_dashboard_crawl_{today}")

    if not os.path.exists(crawl_marker):
        # Full crawl — only once per day
        if run_script("crawl_sites.py", 600):
            run_script("run_ai_audit.py", 300)
            open(crawl_marker, "w").close()
    else:
        log("Crawl already done today — skipping")

    # Check if GA4 returned 0 users (token may have expired)
    import json as check_json
    ga4_file = os.path.join(PROJECT_DIR, "src", "data", "live", "ga4.json")
    if os.path.exists(ga4_file):
        try:
            with open(ga4_file) as f:
                ga4 = check_json.load(f)
            for cid, data in ga4.items():
                if data.get("overview", {}).get("active_users", 0) == 0:
                    log(f"WARNING: GA4 shows 0 users for {cid} — token may have expired")
                    log(f"  Run: cd ~/rank4ai-dashboard && python3 scripts/ga4_auth.py")
        except:
            pass

    # Validate data before deploying — don't deploy if key files are empty/corrupt
    log("\nValidating data files...")
    import json as vjson
    critical_files = [
        "src/data/live/crawl_rank4ai.json",
        "src/data/live/recommendations.json",
        "src/data/live/uptime.json",
    ]
    data_ok = True
    for cf in critical_files:
        full_path = os.path.join(PROJECT_DIR, cf)
        if not os.path.exists(full_path):
            log(f"  MISSING: {cf}")
            # Don't fail — file might not exist yet
            continue
        try:
            with open(full_path) as f:
                data = vjson.load(f)
            size = os.path.getsize(full_path)
            if size < 10:
                log(f"  WARNING: {cf} is only {size} bytes — may be empty")
            else:
                log(f"  OK: {cf} ({size // 1024}KB)")
        except vjson.JSONDecodeError as e:
            log(f"  CORRUPT: {cf} — {e}")
            data_ok = False

    if not data_ok:
        log("DATA VALIDATION FAILED — skipping deploy to protect live site")
        send_failure_alert("Dashboard Refresh", "Data validation failed — deploy blocked. Check for corrupt JSON files.", log_file=LOG_FILE)
        return

    # Submit new pages to Google Indexing API (200/day limit shared across all sites)
    log("\nSubmitting new pages to Google Indexing API...")
    for site in ["rank4ai", "market-invoice", "seocompare"]:
        script_path = os.path.join(SCRIPTS_DIR, "submit_google_indexing.py")
        try:
            result = subprocess.run(
                [sys.executable, script_path, site, "50"],
                capture_output=True, text=True, timeout=120,
                cwd=PROJECT_DIR, env={**os.environ},
            )
            if result.returncode == 0:
                log(f"  Indexing {site}: OK")
            else:
                log(f"  Indexing {site}: {result.stderr[:100] if result.stderr else 'error'}")
        except Exception as e:
            log(f"  Indexing {site}: {e}")

    # Build and deploy
    build_and_deploy()

    # Check site changelogs + build full changelog
    log("\nChecking site changelogs...")
    run_script("check_site_changes.py", 30)
    run_script("build_changelog.py", 30)

    # Run guardrails check (after everything else)
    log("\nRunning guardrails check...")
    run_script("check_guardrails.py", 30)

    # Summary
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    failed_scripts = [k for k, v in results.items() if not v]
    log(f"\nRefresh complete: {passed}/{total} scripts succeeded")

    # Email alert if anything failed
    if failed_scripts:
        send_failure_alert(
            "Dashboard Refresh",
            [f"{s} failed" for s in failed_scripts],
            log_file=LOG_FILE,
        )

    log("=" * 50)


if __name__ == "__main__":
    main()
