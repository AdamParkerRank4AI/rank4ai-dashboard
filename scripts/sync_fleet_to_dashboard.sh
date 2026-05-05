#!/bin/bash
# Fleet → Dashboard sync. Runs every 15 min via launchd.
# Reads source from each fleet repo, writes crawl_<slug>.json,
# commits + pushes if anything changed. Triggers CF Pages rebuild.
#
# Cheap: skips push when no diff. ~6s when source unchanged.

set -e

cd "$HOME/rank4ai-dashboard" || exit 1

LOG="/tmp/rank4ai_fleet_sync.log"
echo "=== $(date -Iseconds) — fleet sync start ===" >> "$LOG"

# 1. Read source from all 6 fleet repos
python3 scripts/read_fleet_source.py >> "$LOG" 2>&1

# 2. If any crawl_*.json changed, commit + push
CHANGED=$(git status --porcelain src/data/live/crawl_*.json | wc -l | tr -d ' ')
if [ "$CHANGED" = "0" ]; then
    echo "  no changes" >> "$LOG"
    exit 0
fi

echo "  $CHANGED files changed — committing" >> "$LOG"
git add src/data/live/crawl_*.json
git commit -m "Fleet sync: source-reader refresh ($(date -Iseconds))" >> "$LOG" 2>&1
git push origin main >> "$LOG" 2>&1
echo "  pushed; CF Pages will rebuild" >> "$LOG"
