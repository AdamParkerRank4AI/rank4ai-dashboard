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

    # Run data collection scripts (order matters — crawl first, then analysis)
    scripts = [
        ("check_uptime.py", 30),
        ("fetch_ga4.py", 60),
        ("fetch_gsc.py", 60),
        ("fetch_bing.py", 30),
        ("fetch_crawl_activity.py", 30),
        ("fetch_pagespeed.py", 120),
        ("extract_entities.py", 30),
        ("fetch_knowledge_graph.py", 30),
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

    # Build and deploy
    build_and_deploy()

    # Summary
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    log(f"\nRefresh complete: {passed}/{total} scripts succeeded")
    log("=" * 50)


if __name__ == "__main__":
    main()
