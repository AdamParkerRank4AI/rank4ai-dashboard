"""Single source of truth for fetcher site rosters.

Every fetcher used to hardcode its own SITES = {id: url} dict, so they drifted
(check_uptime had 9 sites, fetch_crawl_activity 6, run_ai_audit just 3) and the
newer fleet sites were in NONE of them — they showed as empty dashboard rows with
no overview / pages / recommendations. This reads the live fleet straight from
clients.json so a new live site is picked up everywhere automatically.

Usage in a fetcher (additive — keeps any tuned www/non-www URLs already hardcoded):
    import fleet_sites
    SITES = fleet_sites.merge(SITES)            # add any missing live sites
"""
import json
import os

_CLIENTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "data", "clients.json")


def live_fleet():
    """Return {site_id: https-url} for every live site in clients.json."""
    out = {}
    try:
        clients = json.load(open(_CLIENTS))
    except Exception:
        return out
    for c in clients:
        if c.get("siteStatus") != "live":
            continue
        dom = c.get("liveDomain") or c.get("domain")
        if not dom:
            continue
        if not str(dom).startswith("http"):
            dom = "https://" + dom
        out[c["id"]] = dom
    return out


def all_fetchable():
    """Return {site_id: https-url} for EVERY client that has a real host domain,
    regardless of siteStatus (live / paused / needs / prelaunch). Adam (29 Jun 2026):
    'wire everything in as we don't know when it will start to move' — so the board
    has a row ready the moment a site gets traffic, no manual roster edit needed.
    Excludes: clients with no domain (e.g. printgauge, invoicefinance) and path-only
    entries that aren't standalone sites (e.g. 49k.co.uk/legal-leadgen)."""
    out = {}
    try:
        clients = json.load(open(_CLIENTS))
    except Exception:
        return out
    for c in clients:
        dom = c.get("liveDomain") or c.get("domain")
        if not dom:
            continue
        host = str(dom).replace("https://", "").replace("http://", "")
        if "/" in host:          # path-only entry (e.g. 49k.co.uk/legal-leadgen) — not a site
            continue
        if not str(dom).startswith("http"):
            dom = "https://" + dom
        out[c["id"]] = dom
    return out


def merge(existing, include_all=True):
    """Add any missing fleet sites to `existing` (keeps existing URLs). Default
    include_all=True wires EVERY site with a real domain (any status); pass
    include_all=False for live-only."""
    merged = dict(existing or {})
    source = all_fetchable() if include_all else live_fleet()
    for sid, url in source.items():
        merged.setdefault(sid, url)
    return merged
