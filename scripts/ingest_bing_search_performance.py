#!/usr/bin/env python3
"""Ingest Bing Webmaster "Search Performance" CSV exports -> bing.json traffic_stats.

The live Bing Webmaster *API* (fetch_bing.py -> bing.json) has been failing with
`Max retries exceeded ... ssl.bing.com` (network/API block), so every site shows
0 Bing clicks on the dashboard even though real Bing traffic exists. Bing's
"Search Performance" report exports fine from the UI as a per-site CSV
(Date,Clicks,Impressions,Avg. CTR), same manual-reupload pattern as the AI
Performance CSVs. This turns those CSVs into the traffic_stats shape the
dashboard already reads, WITHOUT clobbering any non-traffic keys the API left.

When the Bing API is unblocked, fetch_bing.py takes over again and this is a
belt-and-braces backfill (run it after, and it only fills traffic_stats).

CSV shape:  "Date","Clicks","Impressions","Avg. CTR"  (one row per day)
Dashboard reads:  bing[site_id].traffic_stats = [{"Clicks": n, "Impressions": n, "Date": ...}]
"""
import csv, glob, json, os
from datetime import datetime, timezone

DOWNLOADS = os.path.expanduser("~/Downloads")
OUT = os.path.expanduser("~/rank4ai-dashboard/src/data/live/bing.json")

DOMAIN_TO_ID = {
    "www.marketinvoice.co.uk": "market-invoice",
    "marketinvoice.co.uk": "market-invoice",
    "peptideclear.co.uk": "peptideclear",
    "merchanthq.co.uk": "cardmachines",
    "fundbiz.co.uk": "fundbiz",
    "adhdhelper.co.uk": "adhdhelper",
    "vettedhome.co.uk": "sortedproperty",
    "mortgageexplained.co.uk": "mortgageexplained",
    "ltdturnaround.co.uk": "company-rescue",
}


def latest_csv_per_domain():
    best = {}
    for path in glob.glob(os.path.join(DOWNLOADS, "*SearchPerformanceOverview*.csv")):
        dom = os.path.basename(path).split("_SearchPerformanceOverview")[0]
        if dom not in DOMAIN_TO_ID:
            continue
        mt = os.path.getmtime(path)
        if dom not in best or mt > best[dom][1]:
            best[dom] = (path, mt)
    return {dom: p for dom, (p, _) in best.items()}


def parse(path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            d = (r.get("Date") or "").strip()
            if not d:
                continue
            try:
                dt = datetime.strptime(d.split(" ")[0], "%m/%d/%Y").date()
            except ValueError:
                continue
            rows.append({
                "Date": dt.isoformat(),
                "Clicks": int(float(r.get("Clicks") or 0)),
                "Impressions": int(float(r.get("Impressions") or 0)),
            })
    rows.sort(key=lambda x: x["Date"])
    return rows


def main():
    data = {}
    if os.path.exists(OUT):
        try:
            data = json.load(open(OUT))
        except Exception:
            data = {}
    files = latest_csv_per_domain()
    now = datetime.now(timezone.utc).isoformat()
    for dom, path in files.items():
        sid = DOMAIN_TO_ID[dom]
        rows = parse(path)
        if not rows:
            continue
        # keep only the trailing days that actually have activity, but the
        # dashboard sums whatever is here, so give it the full exported window.
        entry = data.get(sid, {"site_id": sid})
        entry["site_url"] = entry.get("site_url") or f"https://{dom}/"
        entry["traffic_stats"] = rows
        entry["traffic_clicks_total"] = sum(r["Clicks"] for r in rows)
        entry["traffic_impressions_total"] = sum(r["Impressions"] for r in rows)
        entry["traffic_source"] = "csv_export"
        entry["traffic_fetched_at"] = now
        # drop the stale API error strings so the dashboard doesn't look broken
        for k in ("traffic_error",):
            entry.pop(k, None)
        data[sid] = entry
        print(f"  {sid}: {entry['traffic_clicks_total']} clicks / {entry['traffic_impressions_total']} imps ({os.path.basename(path)})")
    if not files:
        print("No SearchPerformanceOverview CSVs found in ~/Downloads.")
    with open(OUT, "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {OUT} ({len(files)} sites updated)")


if __name__ == "__main__":
    main()
