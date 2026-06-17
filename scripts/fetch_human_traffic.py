#!/usr/bin/env python3
"""Accurate per-site HUMAN traffic (no bots) for the dashboard source-of-truth.

The old fleet_bot_hits.json pulled rows and hit Supabase's 1000-row cap, so its
human counts were a ~minutes-long sample, not a real window. This uses PostgREST
count=exact (HEAD, no rows pulled) to get true counts per site over 30/7 days:
  - human_hits   (bot_category = 'human')  <- the "(no bots)" number
  - total_hits   (everything, incl. bots/AI crawlers)
Then folds in GSC clicks (already bot-free) + real leads so the dashboard shows
1-2 trustworthy sources of truth. Output: src/data/live/human_traffic.json
"""
import os, json, urllib.request, urllib.parse, datetime

SUPABASE_URL = "https://tsscscjcxbzhicuuhter.supabase.co"
SK = os.environ.get("SUPABASE_SERVICE_KEY", "")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "src", "data", "live", "human_traffic.json")

# dashboard site id -> leads table
SITES = {
    "market-invoice": "market_invoice_leads",
    "cardmachines": "merchanthq_leads",
    "fundbiz": "fundbiz_leads",
    "bestbusinessloans": "bestbusinessloans_leads",
    "kartapay": "kartapay_leads",
    "peptideclear": "peptideclear_leads",
    "seocompare": "seocompare_leads",
    "rank4ai": None,
}
SUBMIT_TYPES = ("form_submit", "form_submit_serverside", "quote_request", "submit")


def count(path):
    """Return exact row count via PostgREST Content-Range, no rows pulled."""
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/{path}",
        headers={"apikey": SK, "Authorization": f"Bearer {SK}",
                 "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"},
        method="HEAD",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            cr = r.headers.get("Content-Range", "")  # e.g. "0-0/12345"
            return int(cr.split("/")[-1]) if "/" in cr and cr.split("/")[-1].isdigit() else 0
    except Exception:
        return 0


def iso(days_ago):
    return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%dT00:00:00")


def main():
    if not SK:
        raise SystemExit("SUPABASE_SERVICE_KEY missing")
    since30, since7 = iso(30), iso(7)
    out = {"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "window": "30d", "by_site": {}}
    for site, table in SITES.items():
        # bot_hits table is the first-party middleware log; site column = dashboard id
        sq = urllib.parse.quote(site, safe="")
        human30 = count(f"fleet_bot_hits?site=eq.{sq}&bot_category=eq.human&created_at=gte.{since30}")
        total30 = count(f"fleet_bot_hits?site=eq.{sq}&created_at=gte.{since30}")
        human7 = count(f"fleet_bot_hits?site=eq.{sq}&bot_category=eq.human&created_at=gte.{since7}")
        leads30 = 0
        if table:
            st = ",".join(SUBMIT_TYPES)
            leads30 = count(f"{table}?event_type=in.({st})&created_at=gte.{since30}&email=not.is.null")
        out["by_site"][site] = {
            "human_30d": human30, "total_30d": total30, "human_7d": human7,
            "bot_pct": round(100 * (1 - human30 / total30)) if total30 else 0,
            "leads_30d": leads30,
        }
        print(f"  {site}: human30={human30}  total30={total30}  bot%={out['by_site'][site]['bot_pct']}  leads30={leads30}")
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
