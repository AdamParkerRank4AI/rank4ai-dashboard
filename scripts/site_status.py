"""Single source of truth for site lifecycle status, read from clients.json.

Fetchers import this and skip paused / pre-launch / needs-setup sites so we
don't burn API quota on sites that aren't live. clients.json `siteStatus` is
canonical; `pre_launch:true` is honoured as a fallback during migration.

Usage in a fetcher:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from site_status import skip
    for site_id, ... in SITES.items():
        if skip(site_id):
            print(f"  skip {site_id} (not live)"); continue
        ...
"""
import json
import os

_CLIENTS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "src", "data", "clients.json")
ACTIVE_STATUSES = {"live"}


def _status(c):
    s = c.get("siteStatus")
    if s:
        return s
    return "prelaunch" if c.get("pre_launch") else "live"


def load():
    try:
        with open(_CLIENTS) as f:
            return {c["id"]: _status(c) for c in json.load(f)}
    except Exception:
        return {}


_STATUS = load()


def status_of(site_id):
    # Unknown ids (e.g. sites not in clients.json) default to active.
    return _STATUS.get(site_id, "live")


def is_active(site_id):
    return status_of(site_id) in ACTIVE_STATUSES


def skip(site_id):
    return not is_active(site_id)
