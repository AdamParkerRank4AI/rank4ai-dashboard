#!/usr/bin/env python3
"""
urgent_alert.py — fires an email ONLY when there's a human-action item.

Runs every 4 hours via com.rank4ai.dashboard-urgent-alert. Reads the same
live data the dashboard reads. Silent if nothing urgent. Emails Adam when
one or more of these thresholds are crossed:

  • Auth tokens stale (ga4_token.json refresh-token revoked, returned 401/403)
  • Site down (uptime.is_up == false)
  • Clarity script missing from live HTML on any fleet site
  • GA4 tag missing from live HTML on any fleet site
  • >=1 CRITICAL recommendation per site (recommendations.json)
  • Manual indexing queue >= 20 URLs
  • Data freshness: any data file >36h old

The body lists each item with the exact command/click to resolve.
Subject = "⚠ FLEET URGENT (N items)" so it stands out from daily digest.

Dedup: keeps a state file at ~/.rank4ai_urgent_last.json with the hash of
the current alert set. If the set is unchanged from the last run, skips
the email so Adam isn't re-pinged every 4h on the same items.
"""
import hashlib
import json
import os
import smtplib
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from pathlib import Path

LIVE = Path(os.path.expanduser("~/rank4ai-dashboard/src/data/live"))
STATE_FILE = Path(os.path.expanduser("~/.rank4ai_urgent_last.json"))

TO_EMAIL = "adam@muswellrose.com"
FROM_EMAIL = os.environ.get("SMTP_USER", "adam@muswellrose.com")
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_PASS = os.environ.get("SMTP_PASS", "")

FLEET_SITES = {
    "rank4ai": "https://rank4ai.co.uk/",
    "market-invoice": "https://marketinvoice.co.uk/",
    "seocompare": "https://seocompare.co.uk/",
    "merchanthq": "https://merchanthq.co.uk/",
    "bestbusinessloans": "https://bestbusinessloans.ai/",
    "fundbiz": "https://fundbiz.co.uk/",
    "peptideclear": "https://peptideclear.co.uk/",
    "kartapay": "https://kartapay.co.uk/",
}

NOW = datetime.now(timezone.utc)


def load_json(name, default=None):
    p = LIVE / name
    if not p.exists():
        return default if default is not None else {}
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def check_auth_tokens():
    """Returns list of (site_id, why) where GSC is auth-broken."""
    out = []
    gsc = load_json("gsc.json", {})
    for site_id, data in gsc.items():
        if isinstance(data, dict) and "error" in data:
            err = str(data.get("error", ""))[:80]
            if "401" in err or "403" in err or "credentials" in err.lower():
                out.append((site_id, f"GSC fetch error: {err}"))
    # Also check the token file freshness
    token_file = Path(os.path.expanduser("~/rank4ai-dashboard/scripts/ga4_token.json"))
    if not token_file.exists():
        out.append(("FLEET", "ga4_token.json missing — run /tmp/reauth_gsc_oauth.py"))
    return out


def check_uptime():
    """Returns list of sites currently down."""
    uptime = load_json("uptime.json", {})
    out = []
    for site_id, data in uptime.items():
        if isinstance(data, dict) and data.get("is_up") is False:
            out.append((site_id, f"DOWN — last check {data.get('checked_at','?')}"))
    return out


def fetch_html(url, timeout=8):
    try:
        # -L follows redirects (R4 apex→www, etc.)
        r = subprocess.run(
            ["curl", "-sL", "--max-time", str(timeout), "-A", "Mozilla/5.0", url],
            capture_output=True, text=True, timeout=timeout + 2,
        )
        return r.stdout
    except Exception:
        return ""


def check_tracking():
    """Returns list of (site, missing_what) for Clarity/GA4 gaps in live HTML."""
    out = []
    for site_id, url in FLEET_SITES.items():
        html = fetch_html(url)
        if not html:
            continue  # uptime check handles unreachable
        if "clarity.ms/tag" not in html and "window.clarity" not in html:
            out.append((site_id, "Clarity not firing in live HTML"))
        # GA4: look for gtag.js or G- tag id pattern
        if "googletagmanager.com/gtag/js" not in html and "G-" not in html:
            out.append((site_id, "GA4 not firing in live HTML"))
    return out


def check_critical_recs():
    """Returns list of (site, count_critical) for sites with critical recs."""
    recs = load_json("recommendations.json", {})
    out = []
    for site_id, data in recs.items():
        if isinstance(data, dict):
            crit = data.get("critical", 0)
            if crit >= 1:
                out.append((site_id, f"{crit} critical recommendation(s)"))
    return out


def check_indexing_queue():
    """Returns alert if manual indexing queue is bloated."""
    queue = load_json("manual_indexing_queue.json", {})
    out = []
    total = 0
    if isinstance(queue, dict):
        # queue can be either {site: [urls]} or {urls: [...], ...}
        for v in queue.values():
            if isinstance(v, list):
                total += len(v)
            elif isinstance(v, dict) and "urls" in v:
                total += len(v.get("urls", []))
    if total >= 20:
        out.append(("FLEET", f"Manual indexing queue has {total} URLs waiting"))
    return out


def check_fleet_baseline():
    """Returns list of (site, msg) for any failed baseline checks
    (from fleet_baseline_check.py daily run)."""
    data = load_json("fleet_baseline.json", {})
    out = []
    for site_id, site_data in (data.get("sites") or {}).items():
        for cname, c in (site_data.get("checks") or {}).items():
            if not c.get("pass"):
                # Don't double-flag Clarity since it's already covered by check_tracking().
                if cname == "clarity_firing":
                    continue
                # GA4 already covered too.
                if cname == "ga4_firing":
                    continue
                out.append((site_id, f"{cname}: {c.get('detail','')}"))
    return out


def check_freshness():
    """Returns alert per data file that's >36h stale (subset of important ones)."""
    out = []
    important = [
        "gsc.json", "ga4.json", "uptime.json", "recommendations.json",
        "ai_audit.json", "bot_hits.json",
    ]
    cutoff = NOW - timedelta(hours=36)
    for name in important:
        p = LIVE / name
        if not p.exists():
            out.append(("FLEET", f"{name} missing"))
            continue
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        if mtime < cutoff:
            age_h = (NOW - mtime).total_seconds() / 3600
            out.append(("FLEET", f"{name} stale ({age_h:.0f}h old)"))
    return out


def build_items():
    """Aggregate all checks into a flat list of (severity, site, msg, fix)."""
    items = []
    for site, msg in check_auth_tokens():
        items.append(("P0", site, msg, "Run `python3 /tmp/reauth_gsc_oauth.py` and sign in with adam@muswellrose.com"))
    for site, msg in check_uptime():
        items.append(("P0", site, msg, "Check Cloudflare Pages deploy log; restart cloudflared if needed"))
    for site, msg in check_tracking():
        items.append(("P1", site, msg, f"Open {FLEET_SITES.get(site,'')} in browser → view-source → confirm script tag → redeploy if missing"))
    for site, msg in check_critical_recs():
        items.append(("P1", site, msg, f"Open fleet-dashboard-1nt.pages.dev/agency/{site}/recommendations"))
    for site, msg in check_indexing_queue():
        items.append(("P2", site, msg, "Run `python3 ~/rank4ai-dashboard/scripts/submit_google_indexing.py`"))
    for site, msg in check_fleet_baseline():
        items.append(("P1", site, f"Baseline: {msg}", "Open BASELINE_CHECKLIST.md + the failing item; fix in the repo + redeploy. Daily check at fleet_baseline_check.py"))
    for site, msg in check_freshness():
        items.append(("P1", site, msg, "Run `python3 ~/rank4ai-dashboard/scripts/refresh_all.py` and check /tmp/rank4ai_dashboard_refresh.log"))
    return items


def fingerprint(items):
    """Stable hash of the current alert set — used to dedup repeat emails."""
    key = "|".join(sorted(f"{s}:{site}:{msg}" for s, site, msg, _ in items))
    return hashlib.sha256(key.encode()).hexdigest()


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def send_email(items):
    if not SMTP_PASS:
        print("[urgent_alert] SMTP_PASS not set — cannot send")
        return False
    n = len(items)
    subject = f"⚠ FLEET URGENT ({n} item{'s' if n != 1 else ''})"
    by_severity = {"P0": [], "P1": [], "P2": []}
    for sev, site, msg, fix in items:
        by_severity[sev].append((site, msg, fix))

    body_lines = [
        f"Rank4AI Fleet Urgent — {NOW.strftime('%Y-%m-%d %H:%M UTC')}",
        f"{n} action item{'s' if n != 1 else ''} need your attention.",
        "",
        "Dashboard: https://fleet-dashboard-1nt.pages.dev/",
        "",
    ]
    sev_labels = {"P0": "🔴 P0 — NOW", "P1": "🟠 P1 — TODAY", "P2": "🟡 P2 — THIS WEEK"}
    for sev in ("P0", "P1", "P2"):
        if not by_severity[sev]:
            continue
        body_lines.append(sev_labels[sev])
        body_lines.append("─" * 40)
        for i, (site, msg, fix) in enumerate(by_severity[sev], 1):
            body_lines.append(f"{i}. [{site}] {msg}")
            body_lines.append(f"   → {fix}")
            body_lines.append("")
        body_lines.append("")
    body_lines.append("— Fleet Monitor (silenced when nothing urgent)")
    body = "\n".join(body_lines)

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(FROM_EMAIL, SMTP_PASS)
            s.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
        print(f"[urgent_alert] Sent {n} item(s) to {TO_EMAIL}")
        return True
    except Exception as e:
        print(f"[urgent_alert] FAILED to send: {e}")
        return False


def main():
    items = build_items()
    if not items:
        print(f"[urgent_alert] No urgent items at {NOW.isoformat()} — silent")
        save_state({"last_check": NOW.isoformat(), "items": 0, "fingerprint": ""})
        return 0

    fp = fingerprint(items)
    state = load_state()
    # If --force is passed, send anyway. Otherwise dedup against last fingerprint.
    force = "--force" in sys.argv
    if not force and state.get("fingerprint") == fp:
        age_h = 0
        if "last_sent_at" in state:
            try:
                last = datetime.fromisoformat(state["last_sent_at"])
                age_h = (NOW - last).total_seconds() / 3600
            except Exception:
                pass
        # Resend even if same fingerprint after 24h, as a nag
        if age_h < 24:
            print(f"[urgent_alert] {len(items)} items, same as last alert {age_h:.1f}h ago — skipping")
            save_state({**state, "last_check": NOW.isoformat()})
            return 0

    ok = send_email(items)
    save_state({
        "last_check": NOW.isoformat(),
        "last_sent_at": NOW.isoformat() if ok else state.get("last_sent_at", ""),
        "items": len(items),
        "fingerprint": fp,
    })
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
