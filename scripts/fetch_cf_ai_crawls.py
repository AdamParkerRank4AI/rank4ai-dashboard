#!/usr/bin/env python3
"""Fetch AI crawler traffic from Cloudflare's GraphQL Analytics API.

Cloudflare's edge sees EVERY request before it hits origin, so this is
the true-count source for AI bot traffic. Richer and more accurate than
the bot_hits.json collected via our own Worker.

Requires token permission: Account Analytics:Read + Zone Analytics:Read.

Writes src/data/live/cf_ai_crawls.json:
  {
    "fetched_at": "...",
    "per_site": {
      "rank4ai": {
        "days": [{"date": "2026-04-17", "bot": "GPTBot", "count": 123, "paths": {...}}, ...],
        "totals_by_bot": {"GPTBot": 845, "ClaudeBot": 203, ...},
        "totals_by_day": {"2026-04-17": 1234, ...},
        "total_30d": 9876
      }
    }
  }
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

LIVE = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
OUTPUT = os.path.join(LIVE, "cf_ai_crawls.json")

ZONES = {
    "rank4ai":        {"zone": "0f96cd18076e983f2ead742c0b454836", "token_env": "CF_TOKEN_RANK4AI"},
    "market-invoice": {"zone": "a087fb8362314266147dcbf72cec5932", "token_env": "CF_TOKEN_RANK4AI"},
    "seocompare":     {"zone": "464d0139c2f9c598664ec89a731a3e87", "token_env": "CF_TOKEN_MUSWELLROSE"},
}

AI_BOT_PATTERNS = [
    ("GPTBot",          r"GPTBot"),
    ("ChatGPT-User",    r"ChatGPT-User"),
    ("OAI-SearchBot",   r"OAI-SearchBot"),
    ("ClaudeBot",       r"ClaudeBot|Claude-Web|anthropic-ai"),
    ("PerplexityBot",   r"PerplexityBot|Perplexity-User"),
    ("Google-Extended", r"Google-Extended"),
    ("Googlebot",       r"Googlebot"),
    ("Bingbot",         r"Bingbot|BingPreview"),
    ("Applebot",        r"Applebot"),
    ("Bytespider",      r"Bytespider"),
    ("Amazonbot",       r"Amazonbot"),
    ("CCBot",           r"CCBot"),
    ("Meta-ExternalAgent", r"Meta-ExternalAgent|FacebookExternalHit|meta-externalagent"),
    ("MistralAI-User",  r"MistralAI"),
    ("cohere-ai",       r"cohere-ai"),
    ("YouBot",          r"YouBot"),
    ("DuckDuckBot",     r"DuckDuckBot|DuckAssistBot"),
]

GRAPHQL_URL = "https://api.cloudflare.com/client/v4/graphql"

QUERY = """
query($zone: String!, $start: Date!, $end: Date!) {
  viewer {
    zones(filter: {zoneTag: $zone}) {
      httpRequestsAdaptiveGroups(
        limit: 10000
        filter: {date_geq: $start, date_leq: $end}
      ) {
        dimensions { date userAgent }
        count
      }
    }
  }
}
"""

LOOKBACK_DAYS = 14


def classify_bot(ua):
    if not ua:
        return None
    for name, pattern in AI_BOT_PATTERNS:
        if re.search(pattern, ua, re.IGNORECASE):
            return name
    return None


def gql(token, zone, start, end):
    payload = json.dumps({
        "query": QUERY,
        "variables": {"zone": zone, "start": start, "end": end},
    }).encode()
    req = Request(
        GRAPHQL_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def fetch_zone(site_id, zone_id, token):
    end = datetime.utcnow().date()
    groups = []
    first_error = None

    # Free plan caps each query at 1 day; loop through last N days
    for i in range(LOOKBACK_DAYS):
        day = end - timedelta(days=i)
        day_str = day.isoformat()
        try:
            data = gql(token, zone_id, day_str, day_str)
        except HTTPError as e:
            body = e.read().decode(errors="ignore")[:200]
            if first_error is None:
                first_error = f"HTTP {e.code}: {body}"
            continue
        except URLError as e:
            if first_error is None:
                first_error = f"URL error: {e.reason}"
            continue

        if data.get("errors"):
            msgs = [e.get("message", "?") for e in data["errors"]]
            if first_error is None:
                first_error = "; ".join(msgs)[:400]
            continue

        zones = data.get("data", {}).get("viewer", {}).get("zones", [])
        if zones:
            groups.extend(zones[0].get("httpRequestsAdaptiveGroups", []))

    if not groups and first_error:
        return {"error": first_error}

    days = []
    totals_by_bot = {}
    totals_by_day = {}
    paths_by_bot = {}

    # Aggregate: bot × date → count
    by_bot_date = {}
    for g in groups:
        dims = g.get("dimensions", {})
        ua = dims.get("userAgent", "")
        date = dims.get("date", "")
        count = g.get("count", 0)

        bot = classify_bot(ua)
        if not bot:
            continue

        totals_by_bot[bot] = totals_by_bot.get(bot, 0) + count
        totals_by_day[date] = totals_by_day.get(date, 0) + count
        by_bot_date.setdefault(bot, {})
        by_bot_date[bot][date] = by_bot_date[bot].get(date, 0) + count

    # Build per-day series per bot (for charts)
    per_day = []
    all_dates = sorted(totals_by_day.keys())
    for date in all_dates:
        row = {"date": date}
        for bot in totals_by_bot:
            row[bot] = by_bot_date.get(bot, {}).get(date, 0)
        row["_total"] = totals_by_day.get(date, 0)
        per_day.append(row)

    return {
        "lookback_days": LOOKBACK_DAYS,
        "per_day": per_day,
        "totals_by_bot": dict(sorted(totals_by_bot.items(), key=lambda kv: -kv[1])),
        "totals_by_day": dict(sorted(totals_by_day.items())),
        "total_period": sum(totals_by_bot.values()),
        "unique_bots": len(totals_by_bot),
    }


def main():
    os.makedirs(LIVE, exist_ok=True)
    result = {"fetched_at": datetime.utcnow().isoformat() + "Z", "per_site": {}}

    for site_id, cfg in ZONES.items():
        token = os.environ.get(cfg["token_env"])
        if not token:
            print(f"  {site_id}: {cfg['token_env']} not set — skipping")
            result["per_site"][site_id] = {"error": f"{cfg['token_env']} env var missing"}
            continue

        print(f"  {site_id}: fetching…")
        data = fetch_zone(site_id, cfg["zone"], token)
        if "error" in data:
            print(f"    ✗ {data['error'][:150]}")
        else:
            print(f"    ✓ {data['total_period']} AI bot hits across {data['unique_bots']} bots (last {LOOKBACK_DAYS}d)")
            for bot, n in list(data["totals_by_bot"].items())[:5]:
                print(f"      {bot}: {n}")
        result["per_site"][site_id] = data

    with open(OUTPUT, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved → {OUTPUT}")


if __name__ == "__main__":
    main()
