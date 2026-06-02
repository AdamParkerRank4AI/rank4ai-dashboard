#!/usr/bin/env python3
"""
Conversion-leak analysis.

Joins Clarity per-page behaviour (scroll, active time, traffic, dead clicks,
quickbacks) with the lead landing-page attribution we already capture in
Supabase (recent_leads[].landing_path / page_url / attr_journey), to classify
every page as:

  CONVERTER    - a landing/journey path on at least one real lead
  DEAD_WEIGHT  - real human traffic + genuine engagement, but never on a lead
                 (the page burns attention and converts nobody: CRO target)
  LEAK         - frustration signal (dead clicks / quickbacks) on a trafficked page
  BOUNCE       - instant exit (low scroll + low active time): fold/intent mismatch
  OK           - low traffic or already converting fine

Reads:
  - Full per-URL Clarity metrics. Prefers <clarity_full_dir>/clarity_<key>.json
    (raw Data-Export-API metric arrays); falls back to the dashboard's
    summarised clarity.json worst_pages.
  - Dashboard live <site>_leads.json for landing attribution.

Writes: src/data/live/conversion_leaks.json (dashboard tile reads this).

No new credentials, no new cron: it runs off data the daily dashboard refresh
already pulls. Wire it into dashboard-refresh after fetch_clarity + fetch_leads.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE = ROOT / "src" / "data" / "live"
# Optional richer per-URL source (raw Clarity API metric arrays), e.g. /tmp/clarity_*.json
CLARITY_FULL_DIR = Path(os.environ.get("CLARITY_FULL_DIR", "/tmp"))

# site_id (clients.json) -> (clarity token key, leads json filename)
SITES = {
    "market-invoice": ("market-invoice", "mi_leads.json"),
    "peptideclear": ("peptideclear", "peptideclear_leads.json"),
    "cardmachines": ("cardmachines", "cardmachines_leads.json"),
    "bestbusinessloans": ("bestbusinessloans", "bbl_leads.json"),
    "fundbiz": ("fundbiz", "fundbiz_leads.json"),
    "kartapay": ("kartapay", "kartapay_leads.json"),
}

# Thresholds (3-day Clarity window, deliberately low because fleet traffic is low)
MIN_HUMANS = 2          # ignore noise pages
ENGAGED_ACTIVE_S = 20   # "they actually read it"
ENGAGED_SCROLL = 35     # percent
BOUNCE_ACTIVE_S = 5
BOUNCE_SCROLL = 25


def _norm(path: str) -> str:
    """Normalise a URL/path to a comparable path (strip host, query, fragment, www, trailing slash)."""
    if not path:
        return ""
    p = path.strip()
    for pre in ("https://", "http://"):
        if p.startswith(pre):
            p = p[len(pre):]
            p = p.split("/", 1)[1] if "/" in p else ""
            p = "/" + p
            break
    p = p.split("?")[0].split("#")[0]
    if p.startswith("www."):
        p = p[4:]
    if len(p) > 1 and p.endswith("/"):
        p = p[:-1]
    return p or "/"


def load_clarity_full(site_id: str, key: str):
    """Return {path: {humans, scroll, active, dead, quick}} for a site.

    Primary source: the dashboard's clarity_pages.json (written by fetch_clarity,
    already normalised). Fallback: raw Clarity API metric arrays in CLARITY_FULL_DIR
    (e.g. /tmp/clarity_<key>.json) for ad-hoc runs.
    """
    prod = LIVE / "clarity_pages.json"
    if prod.exists():
        try:
            doc = json.loads(prod.read_text())
            pages = doc.get("sites", {}).get(site_id)
            if pages:
                return pages
        except Exception:
            pass
    f = CLARITY_FULL_DIR / f"clarity_{key}.json"
    if not f.exists():
        return None
    data = json.loads(f.read_text())
    pages = {}
    for m in data:
        name = m.get("metricName")
        for r in m.get("information", []):
            url = r.get("Url") or r.get("URL")
            if not url:
                continue
            p = pages.setdefault(_norm(url), {})
            if name == "Traffic":
                p["sessions"] = int(float(r.get("totalSessionCount", 0) or 0))
                p["bots"] = int(float(r.get("totalBotSessionCount", 0) or 0))
            elif name == "ScrollDepth":
                p["scroll"] = float(r.get("averageScrollDepth", 0) or 0)
            elif name == "EngagementTime":
                p["active"] = float(r.get("activeTime", 0) or 0)
            elif name == "DeadClickCount":
                p["dead"] = float(r.get("subTotal", 0) or 0)
            elif name == "QuickbackClick":
                p["quick"] = float(r.get("subTotal", 0) or 0)
    for p in pages.values():
        p["humans"] = max(0, p.get("sessions", 0) - p.get("bots", 0))
    return pages


def converting_paths(leads_file: Path):
    """Set of normalised paths that appear on any real lead's journey/landing."""
    if not leads_file.exists():
        return set(), 0
    d = json.loads(leads_file.read_text())
    paths = set()
    leads = d.get("recent_leads", [])
    for r in leads:
        for fld in ("landing_path", "page_url", "attr_first_landing_path",
                    "attr_last_path", "attr_session_first_landing"):
            v = r.get(fld)
            if v:
                paths.add(_norm(v))
        journey = r.get("attr_journey")
        if isinstance(journey, str):
            for seg in journey.replace(">", ",").split(","):
                if seg.strip():
                    paths.add(_norm(seg))
        elif isinstance(journey, list):
            for seg in journey:
                paths.add(_norm(str(seg)))
    paths.discard("")
    return paths, len(leads)


def classify(pg, is_converter):
    humans = pg.get("humans", 0)
    scroll = pg.get("scroll", 0)
    active = pg.get("active", 0)
    dead = pg.get("dead", 0)
    quick = pg.get("quick", 0)
    if is_converter:
        return "CONVERTER"
    if humans < MIN_HUMANS:
        return "OK"
    if dead > 0 or quick > 0:
        return "LEAK"
    if active >= ENGAGED_ACTIVE_S and scroll >= ENGAGED_SCROLL:
        return "DEAD_WEIGHT"
    if active <= BOUNCE_ACTIVE_S and scroll <= BOUNCE_SCROLL:
        return "BOUNCE"
    return "OK"


def main():
    out = {"sites": {}}
    rank = {"DEAD_WEIGHT": 0, "LEAK": 1, "BOUNCE": 2, "CONVERTER": 3, "OK": 4}
    for site_id, (key, leads_name) in SITES.items():
        pages = load_clarity_full(site_id, key)
        if not pages:
            continue
        conv, lead_count = converting_paths(LIVE / leads_name)
        rows = []
        for path, pg in pages.items():
            if pg.get("humans", 0) < MIN_HUMANS:
                continue
            cls = classify(pg, path in conv)
            rows.append({
                "path": path,
                "humans": pg.get("humans", 0),
                "scroll": round(pg.get("scroll", 0), 1),
                "active_s": round(pg.get("active", 0), 1),
                "dead_clicks": int(pg.get("dead", 0)),
                "quickbacks": int(pg.get("quick", 0)),
                "class": cls,
            })
        rows.sort(key=lambda r: (rank.get(r["class"], 9), -r["humans"]))
        out["sites"][site_id] = {
            "lead_count": lead_count,
            "converting_paths": sorted(conv),
            "pages": rows,
        }
    (LIVE / "conversion_leaks.json").write_text(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    res = main()
    # Human-readable console report
    for site, blk in res["sites"].items():
        print("\n" + "=" * 70)
        print(f"{site}  (leads on file: {blk['lead_count']})")
        print("=" * 70)
        buckets = {}
        for r in blk["pages"]:
            buckets.setdefault(r["class"], []).append(r)
        for cls in ("DEAD_WEIGHT", "LEAK", "BOUNCE", "CONVERTER"):
            rows = buckets.get(cls, [])
            if not rows:
                continue
            print(f"\n  {cls}  ({len(rows)})")
            for r in rows[:8]:
                print(f"    {r['humans']:3d}h  scroll {r['scroll']:4.0f}%  "
                      f"active {r['active_s']:4.0f}s  dead {r['dead_clicks']}  "
                      f"qb {r['quickbacks']}  {r['path'][:48]}")
