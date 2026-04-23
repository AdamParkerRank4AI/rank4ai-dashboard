#!/usr/bin/env python3
"""
Data Validation Agent — runs after every refresh to catch dodgy data.
Checks for anomalies, contradictions, stale data, and things that don't look right.
Emails alert if anything suspicious found.
"""
import json
import os
import sys
from datetime import datetime

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)
LIVE_DIR = os.path.join(PROJECT_DIR, "src", "data", "live")

sys.path.insert(0, SCRIPTS_DIR)
from notify import send_failure_alert

def load(f):
    try:
        with open(os.path.join(LIVE_DIR, f)) as fh:
            return json.load(fh)
    except:
        return None

CLIENTS = ["rank4ai", "market-invoice", "seocompare"]


def main():
    issues = []
    warnings = []
    now = datetime.now()

    # 1. GA4 — check for 0 users (token expiry)
    ga4 = load("ga4.json") or {}
    for c in CLIENTS:
        d = ga4.get(c, {})
        users = d.get("overview", {}).get("active_users", 0)
        if users == 0:
            issues.append(f"GA4: {c} shows 0 users — token likely expired")

    # 2. Crawl page count — check for sudden drops
    hist = load("daily_history.json") or {}
    for c in CLIENTS:
        h = hist.get(c, [])
        if len(h) >= 2:
            prev = h[-2].get("pages_crawled", 0)
            curr = h[-1].get("pages_crawled", 0)
            if prev > 0 and curr > 0:
                drop = (prev - curr) / prev * 100
                if drop > 30:
                    issues.append(f"CRAWL DROP: {c} dropped from {prev} to {curr} pages ({drop:.0f}% drop)")
                elif drop > 15:
                    warnings.append(f"Crawl dip: {c} went from {prev} to {curr} pages")

    # 3. GSC impressions — check for sudden drops
    for c in CLIENTS:
        h = hist.get(c, [])
        if len(h) >= 3:
            recent = [d.get("gsc_impressions", 0) for d in h[-3:]]
            prev_avg = sum(recent[:2]) / 2 if recent[:2] else 0
            curr = recent[-1]
            if prev_avg > 50 and curr < prev_avg * 0.5:
                issues.append(f"GSC DROP: {c} impressions dropped to {curr} from avg {prev_avg:.0f}")

    # 4. Recommendations — check for sudden spikes (false positives reintroduced)
    recs = load("recommendations.json") or {}
    for c in CLIENTS:
        r = recs.get(c, {})
        total = r.get("total", 0)
        if total > 30:
            warnings.append(f"REC SPIKE: {c} has {total} recommendations — possible false positives")

    # 5. AI audit — check scores are realistic
    audit = load("ai_audit.json") or {}
    for c in CLIENTS:
        a = audit.get(c, {})
        score = a.get("overall_score", 0)
        schema = a.get("scores", {}).get("schema", 0)
        blocked = a.get("robots_txt", {}).get("blocked_count", 0)
        if blocked > 0:
            warnings.append(f"AI BOTS BLOCKED: {c} has {blocked} AI crawlers blocked in robots.txt")
        if score == 0:
            issues.append(f"AI AUDIT: {c} score is 0 — audit may have failed")

    # 6. Crawl data — check for contradictions
    for c in CLIENTS:
        crawl = load(f"crawl_{c}.json")
        if crawl:
            pages = crawl.get("pages_crawled", 0)
            with_schema = crawl.get("pages_with_schema", 0)
            issues_count = crawl.get("total_issues", 0)
            avg_depth = crawl.get("avg_depth", 0)

            if pages > 0 and with_schema == 0:
                warnings.append(f"SCHEMA: {c} has {pages} pages but 0 with schema — check crawler detection")
            if avg_depth > 50:
                warnings.append(f"DEPTH: {c} avg page depth is {avg_depth} — looks wrong (should be 1-5)")
            if pages > 0 and issues_count > pages:
                warnings.append(f"ISSUES: {c} has more issues ({issues_count}) than pages ({pages})")

    # 7. Bot hits — check data is flowing
    bh = load("bot_hits.json") or {}
    for c in CLIENTS:
        d = bh.get(c, {})
        days = d.get("days", [])
        total = sum(dd.get("total", 0) for dd in days)
        if len(days) > 3 and total == 0:
            warnings.append(f"BOT HITS: {c} has 0 bot hits over {len(days)} days — logger may not be working")

    # 8. DataForSEO — check not empty
    aio = load("ai_overview_serp.json") or {}
    for c in CLIENTS:
        d = aio.get(c, {})
        if not d.get("results"):
            warnings.append(f"DATAFORSEO: {c} has no SERP results")

    # 9. Daily history — check for data gaps (0 values that shouldn't be 0)
    for c in CLIENTS:
        h = hist.get(c, [])
        if len(h) >= 3:
            zeros = sum(1 for d in h[-5:] if d.get("users", 0) == 0)
            if zeros >= 3:
                issues.append(f"GA4 GAPS: {c} has {zeros} days of 0 users in last 5 days — token keeps expiring")

    # 10. Cross-check: crawl pages vs sitemap
    for c in CLIENTS:
        crawl = load(f"crawl_{c}.json")
        if crawl:
            crawled = crawl.get("pages_crawled", 0)
            # Simple sanity check
            if c == "rank4ai" and crawled < 600:
                warnings.append(f"CRAWL SHORT: {c} only found {crawled} pages (expected 600+)")
            elif c == "market-invoice" and crawled < 300:
                warnings.append(f"CRAWL SHORT: {c} only found {crawled} pages (expected 300+)")
            elif c == "seocompare" and crawled < 250:
                warnings.append(f"CRAWL SHORT: {c} only found {crawled} pages (expected 250+)")

    # 11. Citations — check test results make sense
    cit = load("citation_results.json") or {}
    for c in CLIENTS:
        d = cit.get(c, {})
        s = d.get("summary", {})
        for model in ["claude", "chatgpt", "gemini"]:
            m = s.get(model, {})
            if isinstance(m, dict) and m.get("total", 0) == 0:
                warnings.append(f"CITATIONS: {c} has 0 test queries for {model}")

    # 12. Position change alerts — flag rankings that dropped >3 positions vs yesterday
    #     and new queries that appeared with >10 impressions (both useful signals)
    gsc = load("gsc.json") or {}
    gsc_prev_path = os.path.join(LIVE_DIR, "gsc_previous.json")
    try:
        with open(gsc_prev_path) as f:
            gsc_prev = json.load(f)
    except Exception:
        gsc_prev = {}

    for c in CLIENTS:
        curr_queries = {q["query"]: q for q in gsc.get(c, {}).get("top_queries", []) if q.get("query")}
        prev_queries = {q["query"]: q for q in gsc_prev.get(c, {}).get("top_queries", []) if q.get("query")}

        # Drops
        for q, curr in curr_queries.items():
            prev = prev_queries.get(q)
            if not prev:
                continue
            curr_pos = curr.get("position")
            prev_pos = prev.get("position")
            if curr_pos is None or prev_pos is None:
                continue
            # Lower number = better rank. Drop means position INCREASED by >3.
            if curr_pos - prev_pos > 3 and curr.get("impressions", 0) >= 10:
                issues.append(
                    f"RANKING DROP: {c} '{q[:50]}' fell {prev_pos:.1f} → {curr_pos:.1f} "
                    f"({int(curr['impressions'])} impressions)"
                )

        # New high-impression queries
        for q, curr in curr_queries.items():
            if q not in prev_queries and curr.get("impressions", 0) >= 10:
                warnings.append(
                    f"NEW QUERY: {c} '{q[:50]}' appeared with {int(curr['impressions'])} impressions, "
                    f"pos {curr.get('position', 0):.1f}"
                )

    # Save current gsc snapshot as previous for next run
    try:
        with open(gsc_prev_path, "w") as f:
            json.dump(gsc, f)
    except Exception:
        pass

    # Report
    print(f"Data validation: {len(issues)} issues, {len(warnings)} warnings")

    if issues:
        print("\nISSUES (email alert sent):")
        for i in issues:
            print(f"  !! {i}")
        send_failure_alert("Data Validation", issues, log_file="/tmp/rank4ai_guardrails.log")

    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  ! {w}")

    if not issues and not warnings:
        print("  All data looks clean")

    return len(issues)


if __name__ == "__main__":
    sys.exit(main())
