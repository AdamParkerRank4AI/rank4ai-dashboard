#!/usr/bin/env python3
"""
Fetch crawler activity data — Bing crawl stats + AI bot detection.
Outputs daily crawl data for dashboard charts.
"""
import json
import os
from datetime import datetime

import requests

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
BING_API_KEY = "c129b8c91294404d96cca29e1cf613fe"

SITES = {
    "rank4ai": "https://www.rank4ai.co.uk/",
    "market-invoice": "https://www.marketinvoice.co.uk/",
    "seocompare": "https://www.seocompare.co.uk/",
}

AI_BOTS = [
    "GPTBot", "ChatGPT-User", "Google-Extended", "GoogleOther",
    "ClaudeBot", "Claude-Web", "PerplexityBot", "Bytespider",
    "CCBot", "cohere-ai", "Amazonbot", "anthropic-ai",
    "FacebookBot", "Applebot-Extended", "Bingbot",
]


def parse_bing_date(date_str):
    """Parse Bing's /Date(timestamp)/ format."""
    import re
    match = re.search(r'/Date\((\d+)', date_str)
    if match:
        ts = int(match.group(1)) / 1000
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    return date_str


def fetch_bing_crawl_stats(site_url):
    """Get Bing crawler activity over time."""
    try:
        resp = requests.get(
            "https://ssl.bing.com/webmaster/api.svc/json/GetCrawlStats",
            params={"apikey": BING_API_KEY, "siteUrl": site_url},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json().get("d", [])
            daily = []
            for d in data:
                daily.append({
                    "date": parse_bing_date(d["Date"]),
                    "crawled_pages": d.get("CrawledPages", 0),
                    "in_index": d.get("InIndex", 0),
                    "in_links": d.get("InLinks", 0),
                    "code_2xx": d.get("Code2xx", 0),
                    "code_301": d.get("Code301", 0),
                    "code_4xx": d.get("Code4xx", 0),
                    "code_5xx": d.get("Code5xx", 0),
                    "blocked_robots": d.get("BlockedByRobotsTxt", 0),
                    "errors": d.get("CrawlErrors", 0),
                })
            return daily
        return []
    except:
        return []


def check_ai_bot_access(base_url):
    """Check robots.txt for AI bot rules and verify bots can reach the site."""
    bot_status = {}
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/robots.txt", timeout=10)
        if resp.status_code == 200:
            text = resp.text.lower()
            for bot in AI_BOTS:
                if bot.lower() in text:
                    # Check if blocked
                    import re
                    pattern = rf'user-agent:\s*{re.escape(bot.lower())}.*?(?=user-agent:|\Z)'
                    match = re.search(pattern, text, re.DOTALL)
                    if match and "disallow: /" in match.group():
                        bot_status[bot] = "blocked"
                    else:
                        bot_status[bot] = "allowed"
                else:
                    bot_status[bot] = "not_mentioned"
    except:
        pass

    return bot_status


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_data = {}
    for site_id, site_url in SITES.items():
        print(f"\n{site_id}:")

        # Bing crawl stats
        bing_daily = fetch_bing_crawl_stats(site_url)
        print(f"  Bing: {len(bing_daily)} days of crawl data")

        if bing_daily:
            total_crawled = sum(d["crawled_pages"] for d in bing_daily)
            latest = bing_daily[-1]
            print(f"  Total pages crawled: {total_crawled}")
            print(f"  Currently indexed: {latest['in_index']}")
            print(f"  Inbound links: {latest['in_links']}")

        # AI bot access
        bot_status = check_ai_bot_access(site_url)
        allowed = sum(1 for v in bot_status.values() if v == "allowed")
        blocked = sum(1 for v in bot_status.values() if v == "blocked")
        print(f"  AI bots: {allowed} allowed, {blocked} blocked")

        all_data[site_id] = {
            "site_id": site_id,
            "fetched_at": datetime.now().isoformat(),
            "bing_crawl_daily": bing_daily,
            "bing_total_crawled": sum(d["crawled_pages"] for d in bing_daily),
            "bing_indexed": bing_daily[-1]["in_index"] if bing_daily else 0,
            "bing_inlinks": bing_daily[-1]["in_links"] if bing_daily else 0,
            "ai_bot_access": bot_status,
            "ai_bots_allowed": allowed,
            "ai_bots_blocked": blocked,
        }

    output_file = os.path.join(OUTPUT_DIR, "crawl_activity.json")
    with open(output_file, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
