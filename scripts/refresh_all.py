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
        ("fetch_ga4.py", 240),  # 6 properties × ~7 reports each = 42 API calls; 60s too tight after 18 May fleet expansion
        ("fetch_gsc.py", 60),
        ("fetch_gsc_indexed_history.py", 60),  # daily snapshot of submitted/indexed for change-over-time graphs
        ("fetch_bing.py", 90),  # 6 properties; 30s too tight after fleet expansion
        # Pull fresh daily audit JSON from iCloud → dashboard live data.
        # run_daily_site_audit.py writes to iCloud at 7am via com.rank4ai.site-audit;
        # this fetcher mirrors it into the dashboard. Was missing from refresh_all,
        # so dashboard's daily_audit_*.json had been stale since 26 Apr.
        ("fetch_daily_audit.py", 120),  # 13 sites; 30s too tight
        # Pull per-site content plan markdown from iCloud.
        # Was a standalone 7:10am launchd job (com.rank4ai.dashboard-content-plans-fetch)
        # but launchd context lacks Full Disk Access for iCloud — moved here so it
        # inherits FDA from the dashboard-refresh launchd grant.
        ("fetch_content_plans.py", 120),  # 13 sites; 30s too tight
        ("fetch_crawl_activity.py", 30),
        ("fetch_bot_hits.py", 30),
        ("fetch_cf_ai_crawls.py", 180),  # 13 sites now; 60s too tight
        # PageSpeed — run weekly only (Sunday) to avoid rate limits
        # ("fetch_pagespeed.py", 120),
        ("extract_entities.py", 30),
        ("fetch_knowledge_graph.py", 30),
        ("fetch_dataforseo.py", 600),
        ("fetch_serp.py", 120),
        ("fetch_competitor_serp.py", 120),
        ("build_target_queries.py", 30),  # derive each site's REAL target queries from content + GSC; consumed by generate_recommendations + dashboard UI
        ("classify_queries.py", 30),      # split GSC queries by intent (branded-competitor/transactional/etc) -> intent_split.json -> dashboard Intent Split panel
        ("build_gsc_history.py", 30),     # daily GSC snapshot -> gsc_history.json (90-day rolling) for decay detection
        ("detect_content_decay.py", 30),  # diff today vs ~7d ago -> content_decay.json
        ("build_striking_distance.py", 30), # pos 11-20 ≥30 imp -> striking_distance.json
        ("detect_cannibalisation.py", 120), # GSC query+page dim, 2+ pages same query -> cannibalisation.json
        ("build_cluster_decisions.py", 30), # SERP-overlap clusters + Keep/Fix/Consolidate/Optimise/Prune decisions (needs cannibalisation + content_decay) -> cluster_decisions.json
        ("fleet_baseline_check.py", 120),  # daily live-HTML audit vs BASELINE_CHECKLIST.md; consumed by urgent_alert + dashboard tile
        ("youtube_ai_tracking.py", 300),   # daily AI citation probe for fleet YT channels + branded phrases (EN + foreign); output → youtube_ai_citations.json
        ("generate_recommendations.py", 30),
        ("track_new_pages.py", 30),
        ("save_daily_metrics.py", 30),
        ("generate_prompts_from_pages.py", 60),
        ("fetch_leads.py", 30),
        ("sync_upcoming_pages.py", 30),
        ("compute_aeo_score.py", 60),
        ("compute_wins.py", 30),
        ("build_manual_indexing_queue.py", 30),
        ("build_indexing_health.py", 60),
        # URL Inspection API: ground-truth indexed/not-indexed/404 per URL.
        # ~5 min for fleet (1500 calls/site cap, 0.4s sleep between).
        ("fetch_url_inspection.py", 1800),
        # GSC Coverage drilldown XLSX ingester — picks up any new exports
        # Adam drops in ~/Downloads (per-issue URL lists from Search Console).
        ("ingest_gsc_drilldown.py", 60),
        ("entity_class_classifier.py", 120),
        ("compute_content_freshness.py", 30),
        ("compute_syndication.py", 30),
        ("check_llms_txt.py", 120),
        ("check_drift.py", 240),
        ("check_title_truncation.py", 30),
        ("push_to_fleet.py", 60),
    ]

    results = {}
    for script, timeout in scripts:
        results[script] = run_script(script, timeout)

    # Fleet source reader — ~6s, runs every refresh.
    # Replaces crawler for owned fleet sites (R4/MI/SC/BBL/FB/CM). Crawler
    # only runs as fallback for sites we do not own (Rochelle, future clients).
    run_script("read_fleet_source.py", 120)

    today = datetime.now().strftime("%Y-%m-%d")
    crawl_marker = os.path.expanduser(f"~/.rank4ai_dashboard_crawl_{today}")

    if not os.path.exists(crawl_marker):
        # External crawl — fallback for non-owned sites; runs once per day.
        if run_script("crawl_sites.py", 1200):
            run_script("run_ai_audit.py", 300)
            open(crawl_marker, "w").close()
    else:
        log("External crawl already done today — skipping")

    # Entity coherence — sameAs URL liveness check. Run weekly (Mondays) since
    # social profile URLs do not change often and external HEADs are slow.
    weekday = datetime.now().weekday()  # Monday = 0
    entity_marker = os.path.expanduser(f"~/.rank4ai_dashboard_entity_{today}")
    if weekday == 0 and not os.path.exists(entity_marker):
        if run_script("check_entity_coherence.py", 600):
            open(entity_marker, "w").close()
    elif weekday != 0:
        log(f"Entity coherence runs Mondays — skipping (weekday={weekday})")

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

    # Weekly tasks (Monday only — rate limited APIs)
    import datetime as dt_mod
    if dt_mod.datetime.now().weekday() == 0:  # Monday only
        log("\nFetching Google Trends...")
        run_script("fetch_trends.py", 300)
        log("\nFetching PageSpeed...")
        run_script("fetch_pagespeed.py", 180)
        log("\nChecking citations by type (API ~$1-2)...")
        run_script("check_citations_by_type.py", 600)

    # Check site changelogs + build full changelog
    log("\nChecking site changelogs...")
    run_script("check_site_changes.py", 30)
    run_script("build_changelog.py", 30)

    # Run guardrails check (after everything else)
    log("\nRunning guardrails check...")
    run_script("check_guardrails.py", 30)

    # Validate data quality
    log("\nValidating data quality...")
    run_script("validate_data.py", 30)

    # Data freshness guardrail — alerts if any feed is stale beyond its schedule
    log("\nChecking data freshness...")
    run_script("check_data_freshness.py", 30)

    # Deploy parity guardrail — alerts (and optionally self-heals) if any
    # Pages project's live deploy doesn't match its origin/main commit
    log("\nChecking deploy parity (git HEAD vs live deployment)...")
    run_script("verify_deploy_parity.py", 60)

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
