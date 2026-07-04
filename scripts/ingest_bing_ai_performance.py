#!/usr/bin/env python3
"""Ingest Bing Webmaster "AI Performance" CSV exports → bing_ai_citations.json.

Bing's AI Performance report (real Microsoft Copilot + ChatGPT citations, because
ChatGPT web search rides Bing) is UI-only — Microsoft has NOT shipped an API for it
yet (confirmed 24 Jun 2026, it's on their roadmap). So Adam re-downloads the per-site
"AIPerformanceOverviewStats" CSVs into ~/Downloads weekly (Monday email reminder via
bing_ai_reupload_reminder.py), and this turns them into a dashboard feed.

When Microsoft ships the API, swap the CSV read for an API pull — the output shape
(bing_ai_citations.json) stays the same so the dashboard tile doesn't change.

CSV shape:  "Date","Citations","Cited Pages"  (one row per day)
"""
import csv, glob, json, os, re
from datetime import datetime, timedelta, timezone

DOWNLOADS = os.path.expanduser("~/Downloads")
OUT = os.path.expanduser("~/rank4ai-dashboard/src/data/live/bing_ai_citations.json")

# CSV filename domain -> dashboard site id
DOMAIN_TO_ID = {
    "www.marketinvoice.co.uk": "market-invoice",
    "marketinvoice.co.uk": "market-invoice",
    "peptideclear.co.uk": "peptideclear",
    "merchanthq.co.uk": "cardmachines",
    "kartapay.co.uk": "kartapay",
    "bestbusinessloans.ai": "bestbusinessloans",
    "fundbiz.co.uk": "fundbiz",
    "ltdturnaround.co.uk": "company-rescue",
}


def latest_csv_per_domain():
    """Newest AIPerformanceOverviewStats CSV in ~/Downloads per domain (by mtime)."""
    best = {}
    for path in glob.glob(os.path.join(DOWNLOADS, "*AIPerformanceOverviewStats*.csv")):
        fname = os.path.basename(path)
        dom = fname.split("_AIPerformanceOverviewStats")[0]
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
                "date": dt.isoformat(),
                "citations": int(float(r.get("Citations") or 0)),
                "cited_pages": int(float(r.get("Cited Pages") or 0)),
            })
    rows.sort(key=lambda x: x["date"])
    return rows


def window_sum(rows, days):
    cutoff = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()
    return sum(r["citations"] for r in rows if r["date"] >= cutoff)


def main():
    out = {"generated_at": datetime.now(timezone.utc).isoformat(), "source": "Bing Webmaster AI Performance (manual CSV export)", "by_site": {}}
    files = latest_csv_per_domain()
    for dom, path in files.items():
        sid = DOMAIN_TO_ID[dom]
        rows = parse(path)
        if not rows:
            continue
        # date stamped in filename (e.g. _6_24_2026) for staleness display
        m = re.search(r"_(\d{1,2})_(\d{1,2})_(\d{4})\.csv$", os.path.basename(path))
        fdate = f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}" if m else None
        out["by_site"][sid] = {
            "domain": dom,
            "citations_7d": window_sum(rows, 7),
            "citations_30d": window_sum(rows, 30),
            "citations_90d": window_sum(rows, 90),
            "citations_total": sum(r["citations"] for r in rows),
            "cited_pages_latest": next((r["cited_pages"] for r in reversed(rows) if r["cited_pages"]), 0),
            "daily": rows[-90:],
            "export_date": fdate,
        }
        print(f"  {sid}: {out['by_site'][sid]['citations_30d']} citations (30d), file {os.path.basename(path)}")
    if not out["by_site"]:
        print("No AI Performance CSVs found in ~/Downloads — nothing to ingest.")
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {OUT} ({len(out['by_site'])} sites)")


if __name__ == "__main__":
    main()
