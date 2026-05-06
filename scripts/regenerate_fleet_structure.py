#!/usr/bin/env python3
"""
regenerate_fleet_structure.py

Reads each fleet site's `src/data/live/crawl_<slug>.json` (produced by the
source reader, which is already fresh because it ran in the same sync cycle)
and writes the fleet-structure data to every fleet site's repo.

Each site's /site-structure/ page renders that JSON.

If only the fleet-structure.json file is dirty in a fleet repo, the script
auto-commits + pushes (CF Pages auto-redeploys). If other files are also
dirty in that repo, we skip the commit to avoid stepping on in-flight work.

Hooked from sync_fleet_to_dashboard.sh, runs every 15 minutes via
com.rank4ai.fleet-sync launchd.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DASHBOARD = Path(__file__).resolve().parent.parent
LIVE_DIR = DASHBOARD / "src" / "data" / "live"

# slug -> (display_name, abbr, tagline, tier, repo_path, domain)
FLEET = [
    ("rank4ai",          "Rank4AI",          "R4",  "AI search agency",                           "editorial", Path.home() / "rank4ai-site",            "rank4ai.co.uk"),
    ("market-invoice",   "Market Invoice",   "MI",  "UK invoice finance comparison",              "editorial", Path.home() / "compare-invoice-finance", "marketinvoice.co.uk"),
    ("seocompare",       "SEOCompare",       "SC",  "AI search optimisation comparison",          "editorial", Path.home() / "compareaiseo",            "seocompare.co.uk"),
    ("bestbusinessloans","BestBusinessLoans","BBL", "Business loan editorial and lead capture",   "leadgen",   Path.home() / "bestbusinessloans",       "bestbusinessloans.co.uk"),
    ("fundbiz",          "FundBiz",          "FB",  "Specialty UK SMB finance broker",            "leadgen",   Path.home() / "fundbiz",                 "fundbiz.co.uk"),
    ("cardmachines",     "CardTerminals",    "CT",  "Card machines and merchant accounts",        "product",   Path.home() / "cardmachines",            "cardmachines.co.uk"),
]


def derive_sections_from_crawl(crawl: dict) -> tuple[int, list[dict]]:
    """Walk the crawl JSON's `pages` list and group by top-level section."""
    pages = crawl.get("pages", [])
    groups: dict[str, list[str | None]] = defaultdict(list)
    for p in pages:
        path = (p.get("path") or "/").rstrip("/")
        if not path or path == "":
            groups["(home)"].append(None)
            continue
        parts = [s for s in path.split("/") if s]
        if not parts:
            groups["(home)"].append(None)
        else:
            section = parts[0]
            child = "/" + "/".join(parts[1:]) + "/" if len(parts) > 1 else None
            groups[section].append(child)

    sections = []
    for name, children in sorted(groups.items(), key=lambda x: (x[0] != "(home)", -len(x[1]), x[0])):
        leaf_paths = sorted([c for c in children if c is not None])
        sample = [p.strip("/").split("/")[-1] or "/" for p in leaf_paths[:8]]
        sections.append({
            "name": name,
            "leaf_count": len(leaf_paths),
            "sample": sample,
            "more": max(0, len(leaf_paths) - 8),
        })
    return len(pages), sections[:14]


def build_fleet_data() -> list[dict]:
    fleet = []
    for slug, name, abbr, tagline, tier, _repo, domain in FLEET:
        crawl_file = LIVE_DIR / f"crawl_{slug}.json"
        if not crawl_file.exists():
            print(f"  skip {slug}: crawl file missing")
            continue
        try:
            with open(crawl_file) as f:
                crawl = json.load(f)
        except Exception as e:
            print(f"  skip {slug}: parse error {e}")
            continue
        total, sections = derive_sections_from_crawl(crawl)
        fleet.append({
            "slug": slug, "name": name, "abbr": abbr, "tagline": tagline,
            "tier": tier, "domain": domain,
            "total": total,
            "sections": sections,
        })
    return fleet


def git_status(repo: Path) -> list[str]:
    res = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True, text=True, check=False,
    )
    return [line.strip() for line in res.stdout.splitlines() if line.strip()]


def is_only_fleet_structure_dirty(repo: Path) -> bool:
    lines = git_status(repo)
    if not lines:
        return False
    # All status lines must reference src/data/fleet-structure.json
    target = "src/data/fleet-structure.json"
    return all(target in line for line in lines)


def write_and_maybe_push(repo: Path, slug: str, fleet_json: str) -> str:
    target = repo / "src" / "data" / "fleet-structure.json"
    if not target.parent.exists():
        return f"skip {slug}: src/data/ missing"
    existing = target.read_text() if target.exists() else ""
    if existing.strip() == fleet_json.strip():
        return f"{slug}: unchanged"
    target.write_text(fleet_json)

    # Decide whether to auto-commit
    other_dirty_count = sum(1 for line in git_status(repo) if "src/data/fleet-structure.json" not in line)
    if other_dirty_count > 0:
        return f"{slug}: written ({other_dirty_count} other dirty files in repo, skip auto-commit)"

    if not is_only_fleet_structure_dirty(repo):
        # No diff after write (rare race) — nothing to commit
        return f"{slug}: written, no diff"

    msg = f"Auto-sync fleet-structure.json ({datetime.now().isoformat(timespec='seconds')})"
    subprocess.run(["git", "-C", str(repo), "add", "src/data/fleet-structure.json"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", msg], check=True, capture_output=True)
    push = subprocess.run(["git", "-C", str(repo), "push", "origin", "main"], capture_output=True, text=True)
    if push.returncode != 0:
        return f"{slug}: committed but push failed: {push.stderr.strip().splitlines()[-1] if push.stderr else 'unknown'}"
    return f"{slug}: pushed (CF Pages will rebuild)"


def main():
    print(f"=== regenerate fleet-structure {datetime.now().isoformat(timespec='seconds')} ===")
    fleet = build_fleet_data()
    if len(fleet) < 6:
        print(f"  warning: only {len(fleet)}/6 sites available")

    fleet_json = json.dumps(fleet, indent=2)

    for slug, _name, _abbr, _tagline, _tier, repo, _domain in FLEET:
        if not repo.exists():
            print(f"  {slug}: repo path missing ({repo})")
            continue
        if not (repo / ".git").exists():
            print(f"  {slug}: not a git repo, skip")
            continue
        result = write_and_maybe_push(repo, slug, fleet_json)
        print(f"  {result}")


if __name__ == "__main__":
    main()
