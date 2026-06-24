#!/bin/bash
# Daily dashboard refresh + DEPLOY. Wired into launchd com.rank4ai.dashboard (6am).
# Root-cause fix (12 Jun 2026): the dashboard is a static Astro build, so fetching fresh
# data is not enough - the site must be rebuilt and redeployed or the live URL goes stale.
# This wrapper does: stats fetch -> AI audit -> build -> deploy live to Cloudflare Pages.
set -e
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
LOG=/tmp/dashboard_refresh.log
ACC=a29a9e6a4fa4965762858586f129b445
echo "==== $(date) dashboard refresh start ====" >> "$LOG"

# Once-a-day guard. The old single 6am launchd slot silently never fired (Mac asleep
# at 6am — macOS does not catch up missed calendar jobs), so the board froze 15 Jun.
# Fix: multiple morning/afternoon slots run this at the first slot the Mac is awake for.
# This marker (touched at the END, on full success) makes later slots skip; a partial or
# aborted run leaves no marker so the next slot retries.
MARKER="$HOME/.dashboard_refresh_$(date +%Y-%m-%d)"
if [ -f "$MARKER" ]; then echo "$(date) already refreshed today — skipping." >> "$LOG"; exit 0; fi

# 1. Stats fetch (legacy HTML stats cache; kept because the standalone HTML board reads it)
/usr/bin/python3 "$HOME/rank4ai_content_pipeline/dashboard.py" >> "$LOG" 2>&1 || echo "WARN dashboard.py nonzero" >> "$LOG"

# 1b. CORE DATA FETCHERS — the actual fix (14 Jun 2026). dashboard.py above only
# caches a stats blob the Astro board does NOT read; it never refetches the
# live/*.json feeds the board renders. The old full fetcher (refresh_all.py via the
# now-DISABLED com.rank4ai.dashboard-refresh job) ran these, but since it was
# disabled (~27 May) GA4/GSC/Bing/decay/striking-distance froze — so the board
# redeployed daily with stale numbers. Run the fast, board-facing fetchers here in
# dependency order (GSC before history before decay/striking) so what someone sees
# on the board is actually current. Heavy passes (URL inspection, dataforseo, crawl)
# are intentionally left to refresh_all.py / their own jobs — this stays lightweight.
cd "$HOME/rank4ai-dashboard"
for s in \
  check_uptime.py \
  fetch_ga4.py \
  fetch_gsc.py \
  fetch_gsc_daily.py \
  fetch_bing.py \
  fetch_crawl_activity.py \
  fetch_bot_hits.py \
  fetch_fleet_bot_hits.py \
  fetch_human_traffic.py \
  fetch_competitor_serp.py \
  track_new_pages.py \
  build_gsc_history.py \
  detect_content_decay.py \
  build_striking_distance.py \
  generate_recommendations.py ; do
    /usr/bin/python3 "scripts/$s" >> "$LOG" 2>&1 || echo "WARN $s nonzero" >> "$LOG"
done

# 1c. WEEKLY feeds (Mondays). Google Trends / PageSpeed / citations-by-type are
# rate-limited, so they only run once a week — they used to run inside refresh_all.py's
# Monday branch, which died with that job, leaving them ~weeks stale. Run them here on
# Mondays so the weekly tiles stay current too. (citation-by-type costs ~$1-2/run.)
if [ "$(date +%u)" = "1" ]; then
  for s in fetch_trends.py fetch_pagespeed.py check_citations_by_type.py ; do
    /usr/bin/python3 "scripts/$s" >> "$LOG" 2>&1 || echo "WARN $s nonzero" >> "$LOG"
  done
fi

# 2. AI audit (previously unscheduled - now part of the daily run)
cd "$HOME/rank4ai-dashboard"
/usr/bin/python3 scripts/run_ai_audit.py >> "$LOG" 2>&1 || echo "WARN run_ai_audit.py nonzero" >> "$LOG"

# 2b. Leads + daily site audit. dashboard.py (step 1) caches GSC/GA4/bot/etc but
# NOT the Supabase leads or per-site daily audit - those live in refresh_all.py,
# which this deploy job never ran, so the leads pages + audit tiles drifted a
# cycle (or more) behind. Pull them here so what the dashboard shows is current.
/usr/bin/python3 scripts/fetch_leads.py >> "$LOG" 2>&1 || echo "WARN fetch_leads.py nonzero" >> "$LOG"
# Bing AI Performance (real ChatGPT/Copilot citations) — ingests the weekly CSV
# exports Adam drops in ~/Downloads (no API yet). Monday email reminder = com.fleet.bing-ai-reminder.
/usr/bin/python3 scripts/ingest_bing_ai_performance.py >> "$LOG" 2>&1 || echo "WARN ingest_bing_ai_performance.py nonzero" >> "$LOG"
/usr/bin/python3 scripts/fetch_daily_audit.py >> "$LOG" 2>&1 || echo "WARN fetch_daily_audit.py nonzero" >> "$LOG"

# 2b-i. INDEXING. IndexNow (free, instant Bing/Yandex) wasn't scheduled anywhere —
# it had gone dark. Submit the live sitemaps daily, then rebuild indexing_health so
# the dashboard reflects real submissions (Google API rollup + IndexNow), not the
# stale per-URL google log that froze on 20 May.
/usr/bin/python3 scripts/submit_indexnow.py all >> "$LOG" 2>&1 || echo "WARN submit_indexnow.py nonzero" >> "$LOG"
/usr/bin/python3 scripts/build_indexing_health.py >> "$LOG" 2>&1 || echo "WARN build_indexing_health.py nonzero" >> "$LOG"

# 2b-ii. Rebuild the persistent enhancement backlog from the fresh feeds. Accumulates
# (never loses an open item), backfills missed opportunities from gsc_history, and
# applies enhancement_done.json so finished items stop resurfacing.
/usr/bin/python3 scripts/build_enhancement_backlog.py >> "$LOG" 2>&1 || echo "WARN build_enhancement_backlog.py nonzero" >> "$LOG"

# 2c. Data-freshness guardrail. Must run LAST (after every fetch) so it reflects
# reality at deploy time. It was never invoked by this job before, so its output
# froze on 20 May; now it auto-covers every live/*.json and the dashboard's
# "Data feeds" tile will surface any silently-failed fetcher.
/usr/bin/python3 scripts/check_data_freshness.py >> "$LOG" 2>&1 || echo "WARN check_data_freshness.py nonzero" >> "$LOG"

# 3. Build + deploy BOTH boards from the same fresh data. There are two CF Pages
# projects: `rank4ai-dashboard` (the DASHBOARD=current board → dashboard.rank4ai.co.uk,
# rank4ai + resiliencebuilder) and `fleet-dashboard` (DASHBOARD=fleet board →
# fleet-dashboard-1nt.pages.dev, the whole fleet). This job used to build+deploy
# ONLY the current board, so the fleet board silently drifted (was 5 days stale on
# 14 Jun). Now both are rebuilt and redeployed every run. Abort on a broken build.
TOKEN="$(cat "$HOME/.cloudflare-dashboard-token")"

# 3a. Current board → rank4ai-dashboard. rm -rf dist first: building both boards
# into the same dist/ without cleaning intermittently leaves a stale .prerender
# chunk and the second build dies with ERR_MODULE_NOT_FOUND (hit manually 23 Jun).
rm -rf dist .astro/.prerender
DASHBOARD=current npm run build >> "$LOG" 2>&1
CLOUDFLARE_API_TOKEN="$TOKEN" CLOUDFLARE_ACCOUNT_ID="$ACC" \
  npx wrangler pages deploy dist --project-name=rank4ai-dashboard --branch=main --commit-dirty=true >> "$LOG" 2>&1

# 3b. Fleet board → fleet-dashboard
rm -rf dist .astro/.prerender
DASHBOARD=fleet npm run build >> "$LOG" 2>&1
CLOUDFLARE_API_TOKEN="$TOKEN" CLOUDFLARE_ACCOUNT_ID="$ACC" \
  npx wrangler pages deploy dist --project-name=fleet-dashboard --branch=main --commit-dirty=true >> "$LOG" 2>&1

touch "$MARKER"
echo "==== $(date) dashboard refresh + deploy done (both boards) ====" >> "$LOG"
