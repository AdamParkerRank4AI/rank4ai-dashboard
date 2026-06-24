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
    cols = ("site,bot_name,bot_category,is_ai_bot,is_ai_asset,path,method,referer,"
            "asn,asn_org,country,city,tls_version,http_protocol,user_agent,created_at")
    url = (f"{SUPABASE_URL}/rest/v1/fleet_bot_hits?select={cols}"
           f"&created_at=gte.{since}&order=created_at.desc&limit={ROW_CAP}")
    r = requests.get(url, headers={
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }, timeout=30)
    r.raise_for_status()
    return r.json()


# Human visits arriving FROM an AI assistant (real referral traffic, i.e. the
# "clicks from ChatGPT" Adam wants). Matched on the referer host.
AI_REFERRERS = [
    ("chatgpt.com", "ChatGPT"), ("chat.openai.com", "ChatGPT"), ("openai.com", "ChatGPT"),
    ("perplexity.ai", "Perplexity"),
    ("gemini.google.com", "Gemini"), ("bard.google.com", "Gemini"),
    ("copilot.microsoft.com", "Copilot"), ("bing.com/chat", "Copilot"),
    ("claude.ai", "Claude"),
    ("you.com", "You.com"), ("poe.com", "Poe"), ("phind.com", "Phind"),
    ("duckduckgo.com/?q", "DuckAssist"),
]


def classify_ai_referer(referer: str):
    if not referer:
        return None
    r = referer.lower()
    for needle, name in AI_REFERRERS:
        if needle in r:
            return name
    return None


# ── AI-citation detector (mirrors ~/fleet-tools/ai-citation-watch.py) ────────
# An 'ai-user' hit (ChatGPT-User / Perplexity-User / Claude-User) = a human asked
# an AI a question and the AI fetched OUR page live to answer it — i.e. we were
# just cited. Verify against the operator's network so spoofed UAs (~5-8% of AI
# bot traffic) don't count: own-network org = VERIFIED, the cloud the operator
# egresses from = PLAUSIBLE (still genuine), anything else = SPOOF (ignored).
CITATION_OPERATORS = {
    "openai":     (["OPENAI"],     ["MICROSOFT", "AZURE"]),
    "anthropic":  (["ANTHROPIC"],  ["AMAZON", "AWS"]),
    "perplexity": (["PERPLEXITY"], ["GOOGLE", "AMAZON", "AWS"]),
    "mistral":    (["MISTRAL"],    ["OVH", "SCALEWAY", "AMAZON"]),
}

def citation_operator(bot_name, ua):
    s = f"{bot_name or ''} {ua or ''}".lower()
    if "perplexity" in s: return "perplexity"
    if "claude" in s or "anthropic" in s: return "anthropic"
    if "chatgpt" in s or "oai-" in s or "gptbot" in s or "openai" in s: return "openai"
    if "mistral" in s: return "mistral"
    return None

def citation_verdict(bot_name, ua, asn_org):
    op = citation_operator(bot_name, ua)
    if not op:
        return ("unknown", None)
    own, cloud = CITATION_OPERATORS[op]
    o = (asn_org or "").upper()
    if any(x in o for x in own):
        return ("verified", op)
    if any(x in o for x in cloud):
        return ("plausible", op)
    return ("spoof?", op)

def fetch_ai_user_rows(key):
    """Dedicated pull of ai-user rows (a real citation = an AI fetched us live for
    a user). Separate from the mixed fetch because Supabase hard-caps each page at
    1000 rows and ai-user would otherwise be crowded out by crawler volume.
    Returns (most_recent_rows[:1000], true_total_in_window)."""
    if not key:
        return [], 0
    since = (datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    cols = "site,bot_name,bot_category,path,asn,asn_org,country,user_agent,created_at"
    url = (f"{SUPABASE_URL}/rest/v1/fleet_bot_hits?select={cols}"
           f"&bot_category=eq.ai-user&created_at=gte.{since}&order=created_at.desc&limit=1000")
    try:
        r = requests.get(url, headers={
            "apikey": key, "Authorization": f"Bearer {key}",
            "Prefer": "count=exact",  # returns true total in Content-Range
        }, timeout=30)
        r.raise_for_status()
        total = len(r.json())
        cr = r.headers.get("Content-Range", "")  # e.g. "0-999/4823"
        if "/" in cr and cr.split("/")[-1].isdigit():
            total = int(cr.split("/")[-1])
        return r.json(), total
    except Exception as e:
        print(f"ai-user fetch error: {e}")
        return [], 0


def build_ai_citations(key):
    """Aggregate verified 'we were just cited' ai-user fetches from the window."""
    rows, true_total = fetch_ai_user_rows(key)
    now = datetime.now(timezone.utc)
    def parse_ts(ts):
        try:
            return datetime.fromisoformat((ts or "").replace("Z", "+00:00"))
        except Exception:
            return None
    by_site = defaultdict(lambda: {"count": 0, "c24": 0, "c7": 0, "c30": 0, "last_seen": None, "engines": defaultdict(int)})
    pages = defaultdict(lambda: {"count": 0, "last_seen": None, "bot": None, "site": None, "path": None})
    recent, total, spoofed, fresh, total_7d = [], 0, 0, 0, 0
    for r in rows:
        if (r.get("bot_category") or "") != "ai-user":
            continue
        verdict, eng = citation_verdict(r.get("bot_name"), r.get("user_agent"), r.get("asn_org"))
        if verdict == "spoof?":
            spoofed += 1
            continue
        if verdict == "unknown":
            continue
        total += 1
        site = r.get("site") or "?"
        pth = r.get("path") or "/"
        ts = r.get("created_at")
        cs = by_site[site]
        cs["count"] += 1
        cs["engines"][eng or "?"] += 1
        if not cs["last_seen"] or (ts and ts > cs["last_seen"]):
            cs["last_seen"] = ts
        cp = pages[(site, pth)]
        cp["count"] += 1
        cp["site"], cp["path"], cp["bot"] = site, pth, r.get("bot_name")
        if not cp["last_seen"] or (ts and ts > cp["last_seen"]):
            cp["last_seen"] = ts
        dt = parse_ts(ts)
        is_fresh = bool(dt and (now - dt) <= timedelta(hours=24))
        # Per-site rolling windows (24h / 7d / 30d). c30 == the full window count.
        age = (now - dt) if dt else None
        cs["c30"] += 1
        if age is not None and age <= timedelta(days=7):
            cs["c7"] += 1
            total_7d += 1
        if age is not None and age <= timedelta(hours=24):
            cs["c24"] += 1
        if is_fresh:
            fresh += 1
        if len(recent) < 30:  # rows are created_at.desc, so this is the newest
            recent.append({"site": site, "path": pth, "bot": r.get("bot_name"),
                           "engine": eng, "asn_org": r.get("asn_org"),
                           "created_at": ts, "verdict": verdict, "fresh": is_fresh})
    return {
        "total": total, "spoofed": spoofed, "fresh_24h": fresh, "total_7d": total_7d,
        "window_total_raw": true_total, "sampled": len(rows),
        "capped": true_total > len(rows),
        "by_site": sorted([{"site": s, "count": v["count"],
                            "count_24h": v["c24"], "count_7d": v["c7"], "count_30d": v["c30"],
                            "last_seen": v["last_seen"],
                            "engines": dict(v["engines"])} for s, v in by_site.items()],
                           key=lambda x: -x["count"]),
        "top_pages": sorted([{"site": v["site"], "path": v["path"], "count": v["count"],
                              "last_seen": v["last_seen"], "bot": v["bot"]} for v in pages.values()],
                            key=lambda x: -x["count"])[:20],
        "recent": recent,
    }


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
    by_site = defaultdict(lambda: {"hits": 0, "ai_bot_hits": 0, "asset_hits": 0, "human_hits": 0,
                                   "ai_referral_hits": 0, "ai_referrers": defaultdict(int), "bots": defaultdict(int)})
    asset_readers = defaultdict(lambda: defaultdict(int))
    cat_totals = defaultdict(int)
    ai_bot_hits = 0
    asset_hits_total = 0
    human_hits_total = 0
    ai_referral_total = 0
    ai_referrers_fleet = defaultdict(int)

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
            ai_src = classify_ai_referer(row.get("referer"))
            if ai_src:
                by_site[site]["ai_referral_hits"] += 1
                by_site[site]["ai_referrers"][ai_src] += 1
                ai_referral_total += 1
                ai_referrers_fleet[ai_src] += 1
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
            "ai_referral_hits": v["ai_referral_hits"],
            "ai_referrers": dict(sorted(v["ai_referrers"].items(), key=lambda kv: kv[1], reverse=True)),
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
            "ai_referral_hits": ai_referral_total,
            "distinct_bots": len(by_bot),
        },
        "ai_referrers": dict(sorted(ai_referrers_fleet.items(), key=lambda kv: kv[1], reverse=True)),
        "by_category": dict(sorted(cat_totals.items(), key=lambda kv: kv[1], reverse=True)),
        "by_bot": by_bot_list,
        "by_site": by_site_list,
        "ai_asset_readers": asset_readers_list,
        "ai_citations": build_ai_citations(key),
        "recent": recent,
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Saved {len(rows)} rows aggregated to {OUTPUT_FILE} "
          f"({len(by_bot)} bots, {asset_hits_total} AI-asset hits)")


if __name__ == "__main__":
    main()
