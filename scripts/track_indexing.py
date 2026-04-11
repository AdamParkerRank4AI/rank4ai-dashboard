#!/usr/bin/env python3
"""
Track time-to-index for submitted URLs.
Logs submissions and checks if indexed via Serper.
"""
import json
import os
import time
from datetime import datetime

import requests

LIVE_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
LOG_FILE = os.path.join(LIVE_DIR, "indexing_tracker.json")
SERPER_KEY = "28257708ebacca0e696d3cfaebda39de3496fa75"


def load_tracker():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            return json.load(f)
    return {}


def save_tracker(data):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def log_submission(client_id, url, method="indexnow"):
    """Log that a URL was submitted for indexing."""
    tracker = load_tracker()
    if client_id not in tracker:
        tracker[client_id] = {"submissions": []}

    # Check if already tracked
    existing = [s for s in tracker[client_id]["submissions"] if s["url"] == url]
    if existing:
        return  # Already tracking

    tracker[client_id]["submissions"].append({
        "url": url,
        "method": method,
        "submitted_at": datetime.now().isoformat(),
        "indexed": False,
        "indexed_at": None,
        "checks": 0,
        "last_checked": None,
    })
    save_tracker(tracker)


def check_indexed(url):
    """Check if a URL is indexed via Serper site: query."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        query = f"site:{parsed.netloc}{parsed.path}"

        resp = requests.post("https://google.serper.dev/search", json={
            "q": query, "gl": "gb", "num": 5,
        }, headers={
            "X-API-KEY": SERPER_KEY,
            "Content-Type": "application/json",
        }, timeout=15)

        if resp.status_code == 200:
            data = resp.json()
            results = data.get("organic", [])
            for r in results:
                if parsed.path.rstrip("/") in r.get("link", ""):
                    return True
        return False
    except:
        return False


def check_all_pending():
    """Check all pending URLs for indexing status."""
    tracker = load_tracker()
    checked = 0

    for client_id, data in tracker.items():
        for sub in data.get("submissions", []):
            if sub.get("indexed"):
                continue

            # Don't check more than once per day
            if sub.get("last_checked"):
                last = datetime.fromisoformat(sub["last_checked"])
                if (datetime.now() - last).days < 1:
                    continue

            print(f"  Checking {sub['url'][:60]}...")
            indexed = check_indexed(sub["url"])
            sub["checks"] = sub.get("checks", 0) + 1
            sub["last_checked"] = datetime.now().isoformat()

            if indexed:
                sub["indexed"] = True
                sub["indexed_at"] = datetime.now().isoformat()
                submitted = datetime.fromisoformat(sub["submitted_at"])
                days = (datetime.now() - submitted).days
                print(f"    INDEXED! ({days} days after submission)")
            else:
                submitted = datetime.fromisoformat(sub["submitted_at"])
                days = (datetime.now() - submitted).days
                print(f"    Not yet ({days} days, {sub['checks']} checks)")

            checked += 1
            time.sleep(1)  # Rate limit Serper

    save_tracker(tracker)
    return checked


def get_summary(client_id):
    """Get indexing summary for a client."""
    tracker = load_tracker()
    data = tracker.get(client_id, {"submissions": []})
    subs = data["submissions"]

    indexed = [s for s in subs if s.get("indexed")]
    pending = [s for s in subs if not s.get("indexed")]

    avg_days = 0
    if indexed:
        total_days = 0
        for s in indexed:
            submitted = datetime.fromisoformat(s["submitted_at"])
            idx_at = datetime.fromisoformat(s["indexed_at"])
            total_days += (idx_at - submitted).days
        avg_days = round(total_days / len(indexed), 1)

    return {
        "total": len(subs),
        "indexed": len(indexed),
        "pending": len(pending),
        "avg_days_to_index": avg_days,
    }


def main():
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "check":
        print("Checking pending URLs...")
        checked = check_all_pending()
        print(f"Checked {checked} URLs")
    elif len(sys.argv) > 2 and sys.argv[1] == "log":
        # log <client_id> <url> [method]
        client_id = sys.argv[2]
        url = sys.argv[3] if len(sys.argv) > 3 else ""
        method = sys.argv[4] if len(sys.argv) > 4 else "indexnow"
        if url:
            log_submission(client_id, url, method)
            print(f"Logged: {url} for {client_id}")
    else:
        # Show summary
        tracker = load_tracker()
        for client_id in tracker:
            summary = get_summary(client_id)
            print(f"{client_id}: {summary['indexed']}/{summary['total']} indexed, {summary['pending']} pending, avg {summary['avg_days_to_index']} days")


if __name__ == "__main__":
    main()
