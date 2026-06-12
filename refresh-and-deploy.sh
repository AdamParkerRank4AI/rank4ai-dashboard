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

# 1. Stats fetch (the original 6am job: GSC/GA4/uptime/etc into src/data/live)
/usr/bin/python3 "$HOME/rank4ai_content_pipeline/dashboard.py" >> "$LOG" 2>&1 || echo "WARN dashboard.py nonzero" >> "$LOG"

# 2. AI audit (previously unscheduled - now part of the daily run)
cd "$HOME/rank4ai-dashboard"
/usr/bin/python3 scripts/run_ai_audit.py >> "$LOG" 2>&1 || echo "WARN run_ai_audit.py nonzero" >> "$LOG"

# 3. Rebuild the static dashboard with the fresh data (abort on failure - do not deploy broken)
npm run build >> "$LOG" 2>&1

# 4. Deploy live to Cloudflare Pages (headless API token, info@rank4ai account)
CLOUDFLARE_API_TOKEN="$(cat "$HOME/.cloudflare-dashboard-token")" \
CLOUDFLARE_ACCOUNT_ID="$ACC" \
  npx wrangler pages deploy dist --project-name=rank4ai-dashboard --branch=main --commit-dirty=true >> "$LOG" 2>&1

echo "==== $(date) dashboard refresh + deploy done ====" >> "$LOG"
