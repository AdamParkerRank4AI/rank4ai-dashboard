#!/bin/bash
# Fleet auto-sync. Runs every 15 min via launchd (com.rank4ai.fleet-sync).
#
# Step 1: Read source from each fleet repo, write crawl_<slug>.json into
#         dashboard repo. Commit + push if any changed.
# Step 2: Regenerate fleet-structure.json from those crawl files, write to
#         each fleet site's repo, auto-commit + push (each site's CF Pages
#         then auto-rebuilds /site-structure/).
#
# Both steps are idempotent — they no-op when nothing has changed.
# Cheap: ~6s when nothing has moved; ~15s with full fleet rebuild push.

set -e

cd "$HOME/rank4ai-dashboard" || exit 1

LOG="/tmp/rank4ai_fleet_sync.log"
echo "=== $(date -Iseconds) — fleet sync start ===" >> "$LOG"

# Step 1: Read source, update crawl_*.json
python3 scripts/read_fleet_source.py >> "$LOG" 2>&1

# Commit + push the crawl files AND any refreshed lead JSONs if changed.
# Lead JSONs (refreshed by fetch_leads.py via dashboard-refresh) were
# previously left uncommitted, so deployed lead data lagged behind Supabase.
CHANGED=$(git status --porcelain src/data/live/crawl_*.json src/data/live/*_leads.json | wc -l | tr -d ' ')
if [ "$CHANGED" != "0" ]; then
    echo "  $CHANGED data files changed, committing dashboard" >> "$LOG"
    git add src/data/live/crawl_*.json src/data/live/*_leads.json
    git commit -m "Fleet sync: source-reader refresh ($(date -Iseconds))" >> "$LOG" 2>&1
    # Self-heal: rebase onto any out-of-band origin commits BEFORE pushing, so
    # a single direct push to main can't permanently stall the auto-sync.
    git pull --rebase -X theirs origin main >> "$LOG" 2>&1 || git rebase --abort >> "$LOG" 2>&1
    git push origin main >> "$LOG" 2>&1
    echo "  dashboard pushed" >> "$LOG"
else
    echo "  no data-file changes (dashboard unchanged)" >> "$LOG"
fi

# Step 2: Regenerate fleet-structure.json across all 6 site repos
# Each repo auto-commits + pushes if its fleet-structure.json changed and
# no other files are dirty in that repo.
echo "  regenerating fleet-structure.json across 6 sites" >> "$LOG"
python3 scripts/regenerate_fleet_structure.py >> "$LOG" 2>&1

echo "  sync complete" >> "$LOG"
