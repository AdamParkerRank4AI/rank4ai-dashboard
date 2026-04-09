#!/usr/bin/env python3
"""
Save daily metrics snapshot for trend charts.
Appends today's key metrics to a history file.
Run daily (included in refresh_all.py).
"""
import json
import os
from datetime import datetime

LIVE_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
HISTORY_FILE = os.path.join(LIVE_DIR, "daily_history.json")


def load(filename):
    path = os.path.join(LIVE_DIR, filename)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def main():
    today = datetime.now().strftime("%Y-%m-%d")

    # Load existing history
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            history = json.load(f)
    else:
        history = {}

    clients = ["rank4ai", "market-invoice", "seocompare"]

    for client_id in clients:
        if client_id not in history:
            history[client_id] = []

        # Check if we already have today's data
        existing_dates = [h["date"] for h in history[client_id]]
        if today in existing_dates:
            print(f"{client_id}: already have {today}")
            continue

        # Gather today's metrics
        ga4 = load("ga4.json").get(client_id, {})
        gsc = load("gsc.json").get(client_id, {})
        crawl = load(f"crawl_{client_id}.json")
        audit = load("ai_audit.json").get(client_id, {})
        citations = load("citations_by_type.json").get(client_id, {})
        uptime = load("uptime.json").get(client_id, {})
        pagespeed = load("pagespeed.json").get(client_id, {})
        competitors = load("competitor_serp.json").get(client_id, {})
        crawl_activity = load("crawl_activity.json").get(client_id, {})

        entry = {
            "date": today,
            # Traffic
            "users": ga4.get("overview", {}).get("active_users", 0),
            "sessions": ga4.get("overview", {}).get("sessions", 0),
            "pageviews": ga4.get("overview", {}).get("pageviews", 0),
            "bounce_rate": ga4.get("overview", {}).get("bounce_rate", 0),
            # Search
            "gsc_clicks": gsc.get("totals", {}).get("clicks", 0),
            "gsc_impressions": gsc.get("totals", {}).get("impressions", 0),
            "gsc_position": gsc.get("totals", {}).get("position", 0),
            "content_gaps": len(gsc.get("content_gaps", [])),
            # Site health
            "pages_crawled": crawl.get("pages_crawled", 0) if crawl else 0,
            "issues": crawl.get("total_issues", 0) if crawl else 0,
            "schema_pages": crawl.get("pages_with_schema", 0) if crawl else 0,
            "orphan_pages": crawl.get("orphan_pages", 0) if crawl else 0,
            "avg_word_count": crawl.get("avg_word_count", 0) if crawl else 0,
            # AI readiness
            "ai_score": audit.get("overall_score", 0),
            "schema_score": audit.get("scores", {}).get("schema", 0),
            "eeat_score": audit.get("scores", {}).get("eeat", 0),
            "citation_potential": audit.get("scores", {}).get("citation_potential", 0),
            # AI citations
            "citation_rate": citations.get("overall_rate", 0),
            "citations_total": citations.get("total_queries", 0),
            "citations_cited": citations.get("total_cited", 0),
            # Performance
            "perf_score": pagespeed.get("avg_scores", {}).get("performance", 0),
            "seo_score": pagespeed.get("avg_scores", {}).get("seo", 0),
            "a11y_score": pagespeed.get("avg_scores", {}).get("accessibility", 0),
            # Uptime
            "response_ms": uptime.get("response_time_ms", 0),
            "uptime_pct": uptime.get("uptime_pct", 0),
            # Competitors
            "competitor_visibility": competitors.get("client_visibility_pct", 0),
            # Crawl activity
            "bing_indexed": crawl_activity.get("bing_indexed", 0),
            "ai_bots_blocked": crawl_activity.get("ai_bots_blocked", 0),
        }

        history[client_id].append(entry)
        # Keep last 365 days
        history[client_id] = history[client_id][-365:]

        print(f"{client_id}: saved {today} — users={entry['users']}, ai_score={entry['ai_score']}, citation_rate={entry['citation_rate']}%")

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
    print(f"\nSaved → {HISTORY_FILE}")


if __name__ == "__main__":
    main()
