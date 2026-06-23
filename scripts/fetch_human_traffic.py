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
import os, json, time, urllib.request, urllib.parse, datetime

SUPABASE_URL = "https://tsscscjcxbzhicuuhter.supabase.co"
# Match fetch_leads.py: env first, then ~/.supabase-service-key file. launchd's
# environment has no SUPABASE_SERVICE_KEY, so env-only would (and did, 18-23 Jun)
# fail silently here while fetch_leads.py kept working via the file fallback —
# leaving human_traffic.json 5 days stale and the overview showing two lead numbers.
def _service_key_from_file():
    p = os.path.expanduser("~/.supabase-service-key")
    try:
        return open(p).read().strip() if os.path.exists(p) else ""
    except Exception:
        return ""

SK = os.environ.get("SUPABASE_SERVICE_KEY", "") or _service_key_from_file()
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
    """Exact row count via PostgREST Content-Range, no rows pulled.

    Returns None (NOT 0) on persistent error. A filtered count=exact over a large
    table can intermittently hit Supabase's statement timeout; the old code
    swallowed that and returned 0, which rendered as a confident "0 humans /
    100% bots" on the dashboard (it did exactly this for MarketInvoice, 23 Jun).
    Caller treats None as "unknown" and keeps the previous value rather than
    overwriting good data with a false zero.
    """
    for attempt in range(3):
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/{path}",
            headers={"apikey": SK, "Authorization": f"Bearer {SK}",
                     "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"},
            method="HEAD",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                cr = r.headers.get("Content-Range", "")  # e.g. "0-0/12345"
                tail = cr.split("/")[-1]
                return int(tail) if "/" in cr and tail.isdigit() else 0
        except Exception:
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    return None


def iso(days_ago):
    return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%dT00:00:00")


def main():
    if not SK:
        raise SystemExit("SUPABASE_SERVICE_KEY missing")
    # Previous file = fallback when a count errors out, so a transient Supabase
    # timeout keeps the last-known-good number instead of writing a false 0.
    prev_by_site = {}
    try:
        with open(OUT) as f:
            prev_by_site = (json.load(f) or {}).get("by_site", {})
    except Exception:
        pass

    since30, since7 = iso(30), iso(7)
    out = {"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "window": "30d", "by_site": {}}
    for site, table in SITES.items():
        # bot_hits table is the first-party middleware log; site column = dashboard id
        sq = urllib.parse.quote(site, safe="")
        human30 = count(f"fleet_bot_hits?site=eq.{sq}&bot_category=eq.human&created_at=gte.{since30}")
        total30 = count(f"fleet_bot_hits?site=eq.{sq}&created_at=gte.{since30}")
        human7 = count(f"fleet_bot_hits?site=eq.{sq}&bot_category=eq.human&created_at=gte.{since7}")
        human1 = count(f"fleet_bot_hits?site=eq.{sq}&bot_category=eq.human&created_at=gte.{iso(1)}")

        # If the core human/total counts errored (None), don't publish a false 0 —
        # carry forward the previous block for this site and move on.
        if human30 is None or total30 is None:
            prev = prev_by_site.get(site)
            if prev:
                out["by_site"][site] = {**prev, "stale": True}
                print(f"  {site}: count ERROR — kept previous (human30={prev.get('human_30d')})")
            else:
                print(f"  {site}: count ERROR and no previous value — skipping")
            continue

        leads30 = 0
        leads_by_source = {}
        if table:
            st = ",".join(SUBMIT_TYPES)
            leads30 = count(f"{table}?event_type=in.({st})&created_at=gte.{since30}&email=not.is.null") or 0
            # leads-by-source from our own attribution (`source` = acquisition channel;
            # falls back to own-domain/internal where first-touch didn't persist)
            try:
                req = urllib.request.Request(
                    f"{SUPABASE_URL}/rest/v1/{table}?select=source&event_type=in.({st})&created_at=gte.{since30}&email=not.is.null",
                    headers={"apikey": SK, "Authorization": f"Bearer {SK}"}, method="GET")
                with urllib.request.urlopen(req, timeout=30) as r:
                    for row in json.load(r):
                        s = (row.get("source") or "unknown").strip() or "unknown"
                        leads_by_source[s] = leads_by_source.get(s, 0) + 1
            except Exception:
                pass
        out["by_site"][site] = {
            "human_30d": human30, "total_30d": total30,
            "human_7d": human7 if human7 is not None else 0,
            "human_1d": human1 if human1 is not None else 0,
            "bot_pct": round(100 * (1 - human30 / total30)) if total30 else 0,
            "leads_30d": leads30,
            "leads_by_source": leads_by_source,
        }
        print(f"  {site}: human30={human30}  total30={total30}  bot%={out['by_site'][site]['bot_pct']}  leads30={leads30}")
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
