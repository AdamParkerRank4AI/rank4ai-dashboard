#!/usr/bin/env python3
"""Fetch Microsoft Clarity behavioural / drop-off signals per fleet site.

Clarity is already installed on every fleet site (R4, MI, MHQ, Kartapay, PC, SC).
This pulls the aggregate friction signals via Clarity's Data Export API so the
"where/why people drop off" data lands on the dashboard instead of being buried
in six separate clarity.microsoft.com logins that nobody checks.

API: GET https://www.clarity.ms/export-data/api/v1/project-live-insights
     Authorization: Bearer <project token>
     numOfDays = 1..3 ; optional dimension1=URL for worst-page breakdown
     Hard limit: 10 requests/day PER PROJECT — we spend 2/site/run (headline + URL).

Tokens (Adam generates one per project: clarity.microsoft.com → Settings →
Data Export → Generate new API token) live in ~/.clarity-tokens.json:
    { "market-invoice": "<jwt>", "cardmachines": "<jwt>", ... }
Missing tokens are reported in the output, not fatal — the tile shows a
"connect" state for those sites.
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
TOKENS_FILE = os.path.expanduser("~/.clarity-tokens.json")
API = "https://www.clarity.ms/export-data/api/v1/project-live-insights"
NUM_DAYS = 3

# site_id → Clarity project id (used only to build the deep-link to the project).
PROJECT_IDS = {
    "rank4ai": "w52s5hspjw",
    "market-invoice": "wpyvjx28bk",
    "cardmachines": "wthzys3krn",
    "kartapay": "wthz1enu3d",
    "peptideclear": "wthza9mczv",
    "seocompare": "",  # Clarity not yet provisioned on SEOCompare
}


def load_tokens() -> dict:
    if os.path.exists(TOKENS_FILE):
        try:
            with open(TOKENS_FILE) as f:
                return json.load(f)
        except Exception as e:
            print(f"WARN: could not read {TOKENS_FILE}: {e}")
    return {}


def call(token: str, dimension: str | None):
    params = f"?numOfDays={NUM_DAYS}"
    if dimension:
        params += f"&dimension1={dimension}"
    req = urllib.request.Request(
        API + params,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode())


def _num(d: dict, *keys):
    """First numeric value among candidate keys in a metric-information dict."""
    for k in keys:
        for dk, dv in d.items():
            if dk.lower() == k.lower() and dv not in (None, ""):
                try:
                    return float(dv)
                except (TypeError, ValueError):
                    pass
    return None


def parse_aggregate(payload) -> dict:
    """Flatten Clarity's metric array into one friction dict (no dimension)."""
    out = {}
    for metric in payload or []:
        name = (metric.get("metricName") or "").lower()
        info = metric.get("information") or [{}]
        row = info[0] if info else {}
        if "traffic" in name:
            out["sessions"] = _num(row, "totalSessionCount", "sessionCount")
            out["distinct_users"] = _num(row, "distinctUserCount")
            out["pages_per_session"] = _num(row, "pagesPerSessionPercentage", "pagesPerSession")
        elif "scrolldepth" in name:
            out["avg_scroll_depth"] = _num(row, "averageScrollDepth")
        elif "engagementtime" in name:
            out["active_time_s"] = _num(row, "activeTime", "totalActiveTime")
        elif "deadclick" in name:
            out["dead_clicks_pct"] = _num(row, "sessionsWithMetricPercentage", "deadClickCount")
        elif "rageclick" in name:
            out["rage_clicks_pct"] = _num(row, "sessionsWithMetricPercentage", "rageClickCount")
        elif "quickback" in name:
            out["quickback_pct"] = _num(row, "sessionsWithMetricPercentage", "quickbackClickCount")
        elif "excessivescroll" in name:
            out["excessive_scroll_pct"] = _num(row, "sessionsWithMetricPercentage")
        elif "errorclick" in name:
            out["error_clicks_pct"] = _num(row, "sessionsWithMetricPercentage")
        elif "scripterror" in name:
            out["script_errors"] = _num(row, "totalErrorCount", "errorCount")
    return out


def parse_worst_pages(payload, limit=5) -> list:
    """Per-URL friction rows, ranked by dead+rage click prevalence."""
    pages = {}
    for metric in payload or []:
        name = (metric.get("metricName") or "").lower()
        if "deadclick" not in name and "rageclick" not in name and "traffic" not in name:
            continue
        key = "dead" if "deadclick" in name else "rage" if "rageclick" in name else "sessions"
        for row in metric.get("information") or []:
            url = row.get("Url") or row.get("URL") or row.get("url")
            if not url:
                continue
            p = pages.setdefault(url, {"url": url})
            if key == "sessions":
                p["sessions"] = _num(row, "totalSessionCount", "sessionCount")
            else:
                p[f"{key}_clicks_pct"] = _num(row, "sessionsWithMetricPercentage")
    ranked = sorted(
        pages.values(),
        key=lambda p: (p.get("rage_clicks_pct") or 0) + (p.get("dead_clicks_pct") or 0),
        reverse=True,
    )
    return ranked[:limit]


def _norm_path(url: str) -> str:
    """Normalise a URL to a comparable path (strip host, query, fragment, www, trailing /)."""
    if not url:
        return ""
    p = url.strip()
    for pre in ("https://", "http://"):
        if p.startswith(pre):
            rest = p[len(pre):]
            p = "/" + (rest.split("/", 1)[1] if "/" in rest else "")
            break
    p = p.split("?")[0].split("#")[0]
    if p.startswith("www."):
        p = p[4:]
    if len(p) > 1 and p.endswith("/"):
        p = p[:-1]
    return p or "/"


def parse_all_pages(payload) -> dict:
    """Full per-URL metrics (not just worst): {path: {humans, scroll, active, dead, quick}}.

    Reuses the same dimension=URL payload already fetched for worst_pages, so it
    costs no extra API calls. Consumed by analyze_conversion_leaks.py.
    """
    pages = {}
    for metric in payload or []:
        name = (metric.get("metricName") or "")
        for row in metric.get("information") or []:
            url = row.get("Url") or row.get("URL") or row.get("url")
            if not url:
                continue
            p = pages.setdefault(_norm_path(url), {})
            if name == "Traffic":
                p["sessions"] = int(_num(row, "totalSessionCount", "sessionCount") or 0)
                p["bots"] = int(_num(row, "totalBotSessionCount") or 0)
            elif name == "ScrollDepth":
                p["scroll"] = round(_num(row, "averageScrollDepth") or 0, 1)
            elif name == "EngagementTime":
                p["active"] = round(_num(row, "activeTime") or 0, 1)
            elif name == "DeadClickCount":
                p["dead"] = int(_num(row, "subTotal") or 0)
            elif name == "QuickbackClick":
                p["quick"] = int(_num(row, "subTotal") or 0)
    for p in pages.values():
        p["humans"] = max(0, p.get("sessions", 0) - p.get("bots", 0))
    return pages


def main():
    tokens = load_tokens()
    fetched_at = datetime.now(timezone.utc).isoformat()
    out = {
        "fetched_at": fetched_at,
        "num_days": NUM_DAYS,
        "sites": {},
        "missing_tokens": [],
    }
    # Full per-page metrics (all pages, not just worst) for the conversion-leak join.
    pages_out = {"fetched_at": fetched_at, "num_days": NUM_DAYS, "sites": {}}

    for site_id, project_id in PROJECT_IDS.items():
        token = tokens.get(site_id)
        if not token:
            out["missing_tokens"].append(site_id)
            continue
        site = {
            "clarity_url": f"https://clarity.microsoft.com/projects/view/{project_id}/dashboard"
            if project_id else None,
        }
        try:
            site.update(parse_aggregate(call(token, None)))
        except urllib.error.HTTPError as e:
            site["error"] = f"HTTP {e.code} (token rejected or rate-limited)"
        except Exception as e:
            site["error"] = str(e)
        else:
            try:
                url_payload = call(token, "URL")  # single call, reused below
                site["worst_pages"] = parse_worst_pages(url_payload)
                pages_out["sites"][site_id] = parse_all_pages(url_payload)
            except Exception:
                site["worst_pages"] = []  # URL breakdown optional; don't fail the site
        out["sites"][site_id] = site

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "clarity.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    with open(os.path.join(OUTPUT_DIR, "clarity_pages.json"), "w") as f:
        json.dump(pages_out, f, indent=2)
    have = len(out["sites"])
    print(f"Wrote {path}: {have} site(s) fetched, "
          f"{len(out['missing_tokens'])} awaiting tokens "
          f"({', '.join(out['missing_tokens']) or 'none'})")


if __name__ == "__main__":
    main()
