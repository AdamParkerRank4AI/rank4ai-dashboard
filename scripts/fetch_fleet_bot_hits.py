#!/usr/bin/env python3
"""
Fetch fleet AI-bot intelligence from the Supabase `fleet_bot_hits` table
(populated by the per-site Cloudflare Pages middleware logger, 30 May 2026).

Answers: which AI crawlers actually fetch our sites and our AI files
(/llms.txt, /ai.txt, /ai-instructions, /mcp), what they look like (ASN/org,
country, TLS, HTTP protocol) and how they behave. Reads with the service_role
key (anon SELECT is blocked by RLS). Writes an aggregated summary to
src/data/live/fleet_bot_hits.json for FleetBotHitsTile.astro.
"""
import json
import os
from collections import defaultdict
from datetime import datetime, timezone, timedelta

import requests

SUPABASE_URL = "https://tsscscjcxbzhicuuhter.supabase.co"
WINDOW_DAYS = 30
ROW_CAP = 20000

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(PROJECT_DIR, "src", "data", "live", "fleet_bot_hits.json")


def service_key():
    k = os.environ.get("SUPABASE_SERVICE_KEY")
    if k:
        return k
    p = os.path.expanduser("~/.supabase-service-key")
    if os.path.exists(p):
        return open(p).read().strip()
    return ""


def fetch_rows(key):
    since = (datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    cols = ("site,bot_name,bot_category,is_ai_bot,is_ai_asset,path,method,"
            "asn,asn_org,country,city,tls_version,http_protocol,user_agent,created_at")
    url = (f"{SUPABASE_URL}/rest/v1/fleet_bot_hits?select={cols}"
           f"&created_at=gte.{since}&order=created_at.desc&limit={ROW_CAP}")
    r = requests.get(url, headers={
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }, timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    key = service_key()
    if not key:
        print("No service key; writing empty file.")
        rows = []
    else:
        try:
            rows = fetch_rows(key)
        except Exception as e:
            print(f"Fetch error: {e}")
            rows = []

    by_bot = defaultdict(lambda: {
        "hits": 0, "asset_hits": 0, "sites": set(), "category": None,
        "first_seen": None, "last_seen": None, "asn_org": None, "country": None,
    })
    by_site = defaultdict(lambda: {"hits": 0, "ai_bot_hits": 0, "asset_hits": 0, "human_hits": 0, "bots": defaultdict(int)})
    asset_readers = defaultdict(lambda: defaultdict(int))
    cat_totals = defaultdict(int)
    ai_bot_hits = 0
    asset_hits_total = 0
    human_hits_total = 0

    for row in rows:
        name = row.get("bot_name") or "Unknown / unmatched"
        site = row.get("site") or "?"
        cat = row.get("bot_category") or "other"
        ts = row.get("created_at")

        # First-party human page views (logged by the middleware, server-side,
        # cookie-independent). Counted on their own; never mixed into the bot
        # intelligence (by_bot / categories / ai_bot_hits).
        if cat == "human":
            by_site[site]["human_hits"] += 1
            human_hits_total += 1
            continue
        is_asset = bool(row.get("is_ai_asset"))
        is_ai = bool(row.get("is_ai_bot"))

        b = by_bot[name]
        b["hits"] += 1
        b["category"] = cat
        b["sites"].add(site)
        if b["first_seen"] is None or (ts and ts < b["first_seen"]):
            b["first_seen"] = ts
        if b["last_seen"] is None or (ts and ts > b["last_seen"]):
            b["last_seen"] = ts
        if row.get("asn_org") and not b["asn_org"]:
            b["asn_org"] = row.get("asn_org")
        if row.get("country") and not b["country"]:
            b["country"] = row.get("country")

        s = by_site[site]
        s["hits"] += 1
        s["bots"][name] += 1
        if is_ai:
            s["ai_bot_hits"] += 1
            ai_bot_hits += 1
        if is_asset:
            s["asset_hits"] += 1
            b["asset_hits"] += 1
            asset_hits_total += 1
            asset_readers[row.get("path") or "?"][name] += 1
        cat_totals[cat] += 1

    by_bot_list = sorted(
        [{
            "bot": n, "category": v["category"], "hits": v["hits"],
            "asset_hits": v["asset_hits"], "sites": sorted(v["sites"]),
            "site_count": len(v["sites"]), "first_seen": v["first_seen"],
            "last_seen": v["last_seen"], "asn_org": v["asn_org"], "country": v["country"],
        } for n, v in by_bot.items()],
        key=lambda x: x["hits"], reverse=True,
    )

    by_site_list = sorted(
        [{
            "site": s, "hits": v["hits"], "ai_bot_hits": v["ai_bot_hits"],
            "asset_hits": v["asset_hits"], "human_hits": v["human_hits"],
            "top_bot": max(v["bots"].items(), key=lambda kv: kv[1])[0] if v["bots"] else None,
        } for s, v in by_site.items()],
        key=lambda x: x["hits"], reverse=True,
    )

    asset_readers_list = sorted(
        [{
            "path": p, "total": sum(bots.values()),
            "bots": dict(sorted(bots.items(), key=lambda kv: kv[1], reverse=True)),
        } for p, bots in asset_readers.items()],
        key=lambda x: x["total"], reverse=True,
    )

    recent = [{
        "site": r.get("site"), "bot_name": r.get("bot_name"),
        "category": r.get("bot_category"), "path": r.get("path"),
        "method": r.get("method"), "asn_org": r.get("asn_org"),
        "country": r.get("country"), "tls": r.get("tls_version"),
        "protocol": r.get("http_protocol"), "created_at": r.get("created_at"),
    } for r in rows[:30]]

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_days": WINDOW_DAYS,
        "fleet_totals": {
            "hits": len(rows) - human_hits_total,
            "ai_bot_hits": ai_bot_hits,
            "asset_hits": asset_hits_total,
            "human_hits": human_hits_total,
            "distinct_bots": len(by_bot),
        },
        "by_category": dict(sorted(cat_totals.items(), key=lambda kv: kv[1], reverse=True)),
        "by_bot": by_bot_list,
        "by_site": by_site_list,
        "ai_asset_readers": asset_readers_list,
        "recent": recent,
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Saved {len(rows)} rows aggregated to {OUTPUT_FILE} "
          f"({len(by_bot)} bots, {asset_hits_total} AI-asset hits)")


if __name__ == "__main__":
    main()
