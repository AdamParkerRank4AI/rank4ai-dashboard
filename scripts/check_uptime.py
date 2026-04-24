#!/usr/bin/env python3
"""
Check uptime and response times for client sites.
Outputs JSON for the dashboard.
"""

import json
import os
from datetime import datetime

import requests

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")

SITES = {
    "rank4ai": "https://www.rank4ai.co.uk",
    "market-invoice": "https://www.marketinvoice.co.uk",
    "seocompare": "https://www.seocompare.co.uk",
    "rochellemarashi": "https://rochellemarashi.pages.dev",
}

HEADERS = {
    "User-Agent": "Rank4AI-Uptime-Check/1.0"
}


def check_site(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        return {
            "url": url,
            "status": resp.status_code,
            "response_time_ms": int(resp.elapsed.total_seconds() * 1000),
            "is_up": resp.status_code < 400,
            "ssl_valid": url.startswith("https"),
            "checked_at": datetime.now().isoformat(),
        }
    except requests.exceptions.Timeout:
        return {
            "url": url,
            "status": 0,
            "response_time_ms": 15000,
            "is_up": False,
            "ssl_valid": False,
            "error": "Timeout",
            "checked_at": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "url": url,
            "status": 0,
            "response_time_ms": 0,
            "is_up": False,
            "ssl_valid": False,
            "error": str(e)[:100],
            "checked_at": datetime.now().isoformat(),
        }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load existing history
    history_file = os.path.join(OUTPUT_DIR, "uptime_history.json")
    if os.path.exists(history_file):
        with open(history_file) as f:
            history = json.load(f)
    else:
        history = {}

    results = {}
    for site_id, url in SITES.items():
        result = check_site(url)
        results[site_id] = result
        print(f"{site_id}: {'UP' if result['is_up'] else 'DOWN'} — {result['response_time_ms']}ms")

        # Append to history (keep last 100 checks)
        if site_id not in history:
            history[site_id] = []
        history[site_id].append({
            "time": result["checked_at"],
            "status": result["status"],
            "ms": result["response_time_ms"],
            "up": result["is_up"],
        })
        history[site_id] = history[site_id][-100:]

    # Calculate uptime percentage from history
    for site_id in results:
        checks = history.get(site_id, [])
        if checks:
            up_count = sum(1 for c in checks if c["up"])
            results[site_id]["uptime_pct"] = round(up_count / len(checks) * 100, 1)
            results[site_id]["checks_total"] = len(checks)
            times = [c["ms"] for c in checks if c["up"]]
            if times:
                results[site_id]["avg_response_ms"] = round(sum(times) / len(times))

    # Save current results
    output_file = os.path.join(OUTPUT_DIR, "uptime.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    # Save history
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

    print(f"Saved → {output_file}")


if __name__ == "__main__":
    main()
