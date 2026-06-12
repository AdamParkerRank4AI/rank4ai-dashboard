#!/bin/bash
# Commit + push the dashboard's FLEET_INBOX.md so the remote fleet-daily-review
# routine (which reads GitHub, not iCloud or this machine) always sees the
# current queue.
#
# CANONICAL inbox is now ~/rank4ai-dashboard/FLEET_INBOX.md (a normal git-tracked
# file). We deliberately do NOT read from iCloud: a launchd context cannot read
# iCloud Drive without Full Disk Access (macOS TCC blocks it with "Operation not
# permitted"), which silently broke + truncated this sync to 2 lines 8-12 Jun 2026.
# Git is the cross-device channel now -- edit FLEET_INBOX.md and commit, or any
# session edits it and this job commits+pushes it.
#
# Runs daily 08:45 BST via launchd (com.rank4ai.fleet-inbox-sync). Idempotent.

set -e
LOG="/tmp/rank4ai_fleet_inbox_sync.log"
DST="$HOME/rank4ai-dashboard/FLEET_INBOX.md"

echo "=== $(date -Iseconds) — fleet inbox commit ===" >> "$LOG"

cd "$HOME/rank4ai-dashboard" || { echo "  repo missing" >> "$LOG"; exit 1; }
if [ ! -f "$DST" ]; then
  echo "  ERROR: FLEET_INBOX.md missing -- not creating it (avoid clobber)" >> "$LOG"
  exit 1
fi

# Only act if FLEET_INBOX.md itself changed (scope the check to that one file;
# the repo always has live-data churn we must ignore).
if /usr/bin/git status --porcelain FLEET_INBOX.md | /usr/bin/grep -q .; then
  /usr/bin/git add FLEET_INBOX.md
  /usr/bin/git commit -m "Fleet inbox update ($(date '+%Y-%m-%d %H:%M'))" >> "$LOG" 2>&1
fi

# Push any unpushed inbox commit. --autostash because the repo always has
# uncommitted live-data churn; --rebase to avoid a merge commit if remote moved.
if [ -n "$(/usr/bin/git log origin/main..HEAD --oneline 2>/dev/null)" ]; then
  /usr/bin/git pull --rebase --autostash origin main >> "$LOG" 2>&1 || true
  /usr/bin/git push origin main >> "$LOG" 2>&1 && echo "  committed + pushed" >> "$LOG"
else
  echo "  no change" >> "$LOG"
fi
