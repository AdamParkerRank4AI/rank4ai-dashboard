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


def merge(existing):
    """Add any live fleet sites missing from `existing` (keeps existing URLs)."""
    merged = dict(existing or {})
    for sid, url in live_fleet().items():
        merged.setdefault(sid, url)
    return merged
