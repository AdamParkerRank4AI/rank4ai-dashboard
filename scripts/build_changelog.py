#!/usr/bin/env python3
"""
Build full categorised changelog from all site repos.
Saves to src/data/live/full_changelog.json
"""
import json
import subprocess
import os

REPOS = {
    "marketinvoice.co.uk": os.path.expanduser("~/compare-invoice-finance"),
    "seocompare.co.uk": os.path.expanduser("~/compareaiseo"),
    "dashboard": os.path.expanduser("~/rank4ai-dashboard"),
}

OUTPUT = os.path.expanduser("~/rank4ai-dashboard/src/data/live/full_changelog.json")


def categorise(msg):
    m = msg.lower()
    if any(w in m for w in ['initial build', 'first build', 'initial commit']):
        return 'new'
    if any(w in m for w in ['fix ', 'fix:', 'hotfix', 'bug']):
        return 'fix'
    if any(w in m for w in ['add ', 'add:', 'new ', 'create', 'build ', 'connect']):
        return 'new'
    if any(w in m for w in ['improve', 'upgrade', 'enhance', 'expand', 'polish',
                             'update', 'redesign', 'overhaul', 'rewrite', 'refactor']):
        return 'improvement'
    if any(w in m for w in ['remove', 'delete', 'clean', 'revert']):
        return 'removal'
    if any(w in m for w in ['switch', 'move', 'rename', 'rebrand', 'convert']):
        return 'change'
    return 'update'


LABELS = {
    'new': 'NEW',
    'fix': 'FIX',
    'improvement': 'IMPROVEMENT',
    'removal': 'REMOVAL',
    'change': 'CHANGE',
    'update': 'UPDATE',
}


def main():
    print("Building full changelog...")
    all_entries = []

    for site, local in REPOS.items():
        if not os.path.exists(local):
            print(f"  {site}: repo not found at {local}")
            continue

        # Pull latest
        subprocess.run(
            ["git", "fetch", "origin"],
            capture_output=True, text=True, timeout=15, cwd=local,
        )

        result = subprocess.run(
            ["git", "log", "--pretty=format:%ai|%s", "--no-merges"],
            capture_output=True, text=True, timeout=10, cwd=local,
        )

        count = 0
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 1)
            if len(parts) != 2:
                continue
            date_str, msg = parts
            cat = categorise(msg)
            all_entries.append({
                "date": date_str[:10],
                "site": site,
                "message": msg.strip(),
                "category": cat,
                "label": LABELS[cat],
            })
            count += 1

        print(f"  {site}: {count} entries")

    all_entries.sort(key=lambda x: x["date"], reverse=True)

    with open(OUTPUT, "w") as f:
        json.dump(all_entries, f, indent=2)

    print(f"Total: {len(all_entries)} entries → {OUTPUT}")


if __name__ == "__main__":
    main()
