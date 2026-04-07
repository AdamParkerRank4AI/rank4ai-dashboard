#!/usr/bin/env python3
"""
Take a baseline snapshot of a client site.
Captures: crawl data, uptime, AI citations, GA4, GSC.
Saves with a date stamp so you can track changes over time.

Usage:
  python3 take_snapshot.py rank4ai
  python3 take_snapshot.py market-invoice
  python3 take_snapshot.py all
"""

import json
import os
import sys
import shutil
from datetime import datetime

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)
LIVE_DIR = os.path.join(PROJECT_DIR, "src", "data", "live")
SNAPSHOTS_DIR = os.path.join(PROJECT_DIR, "src", "data", "snapshots")


def run_script(script_name):
    """Run a data collection script."""
    import subprocess
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    print(f"  Running {script_name}...")
    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True, text=True, timeout=600
    )
    if result.returncode != 0:
        print(f"    Warning: {script_name} had errors")
        if result.stderr:
            # Filter out FutureWarnings
            for line in result.stderr.split('\n'):
                if 'FutureWarning' not in line and 'NotOpenSSLWarning' not in line and line.strip():
                    print(f"    {line.strip()}")
    return result.returncode == 0


def take_snapshot(client_id):
    """Take a snapshot of the current state of a client."""
    today = datetime.now().strftime("%Y-%m-%d")
    snapshot_dir = os.path.join(SNAPSHOTS_DIR, client_id)
    os.makedirs(snapshot_dir, exist_ok=True)

    snapshot_file = os.path.join(snapshot_dir, f"{today}.json")

    print(f"\nTaking snapshot for {client_id} ({today})...")

    # Run all data collection scripts
    print("\n1. Crawling site...")
    run_script("crawl_sites.py")

    print("\n2. Checking uptime...")
    run_script("check_uptime.py")

    print("\n3. Checking AI citations...")
    run_script("check_ai_citations.py")

    print("\n4. Fetching GA4 data...")
    run_script("fetch_ga4.py")

    print("\n5. Fetching GSC data...")
    run_script("fetch_gsc.py")

    # Collect all data for this client into one snapshot
    snapshot = {
        "client_id": client_id,
        "snapshot_date": today,
        "snapshot_time": datetime.now().isoformat(),
        "type": "baseline" if not os.path.exists(os.path.join(snapshot_dir, "baseline.json")) else "update",
    }

    # Load each data source
    def load(filename):
        filepath = os.path.join(LIVE_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath) as f:
                return json.load(f)
        return None

    crawl = load(f"crawl_{client_id}.json")
    uptime = load("uptime.json")
    citations = load("ai_citations.json")
    ga4 = load("ga4.json")
    gsc = load("gsc.json")

    if crawl:
        snapshot["crawl"] = {
            "pages_crawled": crawl.get("pages_crawled", 0),
            "total_issues": crawl.get("total_issues", 0),
            "orphan_pages": crawl.get("orphan_pages", 0),
            "pages_with_schema": crawl.get("pages_with_schema", 0),
            "avg_word_count": crawl.get("avg_word_count", 0),
            "avg_depth": crawl.get("avg_depth", 0),
            "positive_signals": len(crawl.get("positive_signals", [])),
        }

    if uptime and client_id in uptime:
        u = uptime[client_id]
        snapshot["uptime"] = {
            "is_up": u.get("is_up"),
            "response_time_ms": u.get("response_time_ms"),
            "uptime_pct": u.get("uptime_pct"),
        }

    if citations and client_id in citations:
        c = citations[client_id]
        snapshot["ai_citations"] = {
            "citation_rate": c.get("citation_rate", 0),
            "cited_count": c.get("cited_count", 0),
            "total_queries": c.get("total_queries", 0),
        }

    if ga4 and client_id in ga4:
        g = ga4[client_id]
        snapshot["traffic"] = g.get("overview", {})
        snapshot["top_pages"] = g.get("top_pages", [])[:10]
        snapshot["sources"] = g.get("sources", [])

    if gsc and client_id in gsc:
        s = gsc[client_id]
        snapshot["search"] = s.get("totals", {})
        snapshot["top_queries"] = s.get("top_queries", [])[:10]
        snapshot["content_gaps"] = s.get("content_gaps", [])

    # Save snapshot
    with open(snapshot_file, "w") as f:
        json.dump(snapshot, f, indent=2)
    print(f"\nSnapshot saved → {snapshot_file}")

    # If this is the first snapshot, also save as baseline
    baseline_file = os.path.join(snapshot_dir, "baseline.json")
    if not os.path.exists(baseline_file):
        shutil.copy(snapshot_file, baseline_file)
        print(f"Baseline saved → {baseline_file}")
        snapshot["type"] = "baseline"
        with open(snapshot_file, "w") as f:
            json.dump(snapshot, f, indent=2)

    # Print summary
    print(f"\n{'='*50}")
    print(f"SNAPSHOT SUMMARY — {client_id} ({today})")
    print(f"{'='*50}")
    if "crawl" in snapshot:
        c = snapshot["crawl"]
        print(f"  Pages: {c['pages_crawled']} | Issues: {c['total_issues']} | Schema: {c['pages_with_schema']}")
    if "traffic" in snapshot:
        t = snapshot["traffic"]
        print(f"  Users: {t.get('active_users', 0)} | Sessions: {t.get('sessions', 0)} | Pageviews: {t.get('pageviews', 0)}")
    if "search" in snapshot:
        s = snapshot["search"]
        print(f"  GSC Clicks: {s.get('clicks', 0)} | Impressions: {s.get('impressions', 0)} | Avg Pos: {s.get('position', 0)}")
    if "ai_citations" in snapshot:
        a = snapshot["ai_citations"]
        print(f"  AI Citation Rate: {a['citation_rate']}% ({a['cited_count']}/{a['total_queries']})")
    if "uptime" in snapshot:
        u = snapshot["uptime"]
        print(f"  Uptime: {u.get('uptime_pct', 0)}% | Response: {u.get('response_time_ms', 0)}ms")
    print(f"{'='*50}")

    return snapshot


def compare_to_baseline(client_id):
    """Compare current snapshot to baseline."""
    snapshot_dir = os.path.join(SNAPSHOTS_DIR, client_id)
    baseline_file = os.path.join(snapshot_dir, "baseline.json")

    if not os.path.exists(baseline_file):
        print(f"No baseline found for {client_id}")
        return

    with open(baseline_file) as f:
        baseline = json.load(f)

    # Get latest snapshot
    snapshots = sorted([f for f in os.listdir(snapshot_dir) if f != "baseline.json" and f.endswith(".json")])
    if not snapshots:
        print("No snapshots to compare")
        return

    latest_file = os.path.join(snapshot_dir, snapshots[-1])
    with open(latest_file) as f:
        latest = json.load(f)

    print(f"\n{'='*60}")
    print(f"COMPARISON — {client_id}")
    print(f"Baseline: {baseline.get('snapshot_date')} → Latest: {latest.get('snapshot_date')}")
    print(f"{'='*60}")

    def compare(label, baseline_val, latest_val):
        if baseline_val is None or latest_val is None:
            return
        diff = latest_val - baseline_val
        arrow = "↑" if diff > 0 else "↓" if diff < 0 else "→"
        color = ""
        print(f"  {label}: {baseline_val} → {latest_val} ({arrow} {abs(diff)})")

    if "crawl" in baseline and "crawl" in latest:
        compare("Pages", baseline["crawl"].get("pages_crawled"), latest["crawl"].get("pages_crawled"))
        compare("Issues", baseline["crawl"].get("total_issues"), latest["crawl"].get("total_issues"))
        compare("Schema pages", baseline["crawl"].get("pages_with_schema"), latest["crawl"].get("pages_with_schema"))

    if "traffic" in baseline and "traffic" in latest:
        compare("Users", baseline["traffic"].get("active_users"), latest["traffic"].get("active_users"))
        compare("Sessions", baseline["traffic"].get("sessions"), latest["traffic"].get("sessions"))
        compare("Pageviews", baseline["traffic"].get("pageviews"), latest["traffic"].get("pageviews"))

    if "search" in baseline and "search" in latest:
        compare("GSC Clicks", baseline["search"].get("clicks"), latest["search"].get("clicks"))
        compare("GSC Impressions", baseline["search"].get("impressions"), latest["search"].get("impressions"))

    if "ai_citations" in baseline and "ai_citations" in latest:
        compare("Citation Rate %", baseline["ai_citations"].get("citation_rate"), latest["ai_citations"].get("citation_rate"))

    print(f"{'='*60}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 take_snapshot.py <client_id|all> [--compare]")
        print("  python3 take_snapshot.py rank4ai")
        print("  python3 take_snapshot.py market-invoice")
        print("  python3 take_snapshot.py all")
        print("  python3 take_snapshot.py rank4ai --compare")
        return

    client_id = sys.argv[1]
    do_compare = "--compare" in sys.argv

    # Load client list
    clients_file = os.path.join(PROJECT_DIR, "src", "data", "clients.json")
    with open(clients_file) as f:
        clients = json.load(f)

    client_ids = [c["id"] for c in clients]

    if client_id == "all":
        for cid in client_ids:
            take_snapshot(cid)
            if do_compare:
                compare_to_baseline(cid)
    elif client_id in client_ids:
        take_snapshot(client_id)
        if do_compare:
            compare_to_baseline(client_id)
    else:
        print(f"Unknown client: {client_id}")
        print(f"Available: {', '.join(client_ids)}")


if __name__ == "__main__":
    main()
