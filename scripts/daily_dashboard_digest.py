#!/usr/bin/env python3
"""
daily_dashboard_digest.py — daily review of the fleet dashboard.

Runs after the morning data refresh. Reads live data, computes signal
deltas vs the previous day, builds a markdown + HTML digest, emails it
to Adam, and writes a copy to ~/control-panel/daily_dashboard_digest/.

Surfaces:
  - GSC indexed-page delta per site (today vs yesterday)
  - Indexing API submissions in last 24h
  - New drift items / title-lint issues / freshness alerts
  - Top 5 actionable recommendations across the fleet
  - Stale fetchers (any data file >36h old)

Adam asked "the dashboard must be updated AND reviewed every day"
(20 May 2026). Update side runs via com.rank4ai.dashboard-refresh.
This script is the review side.
"""
import json
import os
import smtplib
import sys
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

LIVE = Path(os.path.expanduser('~/rank4ai-dashboard/src/data/live'))
ARCHIVE = Path(os.path.expanduser('~/control-panel/daily_dashboard_digest'))
ARCHIVE.mkdir(parents=True, exist_ok=True)

TO_EMAIL = "adam@muswellrose.com"
FROM_EMAIL = os.environ.get("SMTP_USER", "adam@muswellrose.com")
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_PASS = os.environ.get("SMTP_PASS", "")

NOW = datetime.now(timezone.utc)
TODAY = NOW.date().isoformat()


def load_json(name, default=None):
    p = LIVE / name
    if not p.exists():
        return default if default is not None else {}
    try:
        with open(p) as f:
            return json.load(f)
    except Exception as e:
        return default if default is not None else {}


def section_indexed_delta():
    history = load_json('gsc_indexed_history.json', {})
    rows = history.get('per_site_history', {})
    lines = ["## Pages indexed — today vs yesterday"]
    if not rows:
        lines.append("_No history yet (first day of capture)._\n")
        return "\n".join(lines)

    table = ["| Site | Indexed | Δ vs prev |", "|---|---:|---:|"]
    for site_id, entries in rows.items():
        if not entries:
            continue
        cur = entries[-1]
        cur_indexed = cur.get('indexed', 0)
        cur_submitted = cur.get('submitted', 0)
        if len(entries) >= 2:
            prev = entries[-2].get('indexed', 0)
            delta = cur_indexed - prev
            delta_str = f"{'+' if delta >= 0 else ''}{delta}"
        else:
            delta_str = "—"
        table.append(f"| {site_id} | {cur_indexed}/{cur_submitted} | {delta_str} |")
    lines.append("\n".join(table))
    return "\n".join(lines) + "\n"


def section_indexing_submissions():
    log = load_json('google_indexing_log.json', {})
    lines = ["## Google Indexing API — last 24h"]
    yesterday = (NOW - timedelta(hours=24)).isoformat()
    rows = []
    for site_id, payload in log.items():
        subs = (payload or {}).get('submissions', [])
        last_24h = [s for s in subs if (s.get('submitted_at') or '') >= yesterday]
        ok = sum(1 for s in last_24h if s.get('status') == 'ok')
        err = sum(1 for s in last_24h if s.get('status') == 'error')
        if last_24h:
            rows.append((site_id, ok, err))
    if not rows:
        lines.append("_No submissions in last 24h._")
        return "\n".join(lines) + "\n"
    rows.sort(key=lambda r: -r[1])
    table = ["| Site | OK | Errors |", "|---|---:|---:|"]
    for site_id, ok, err in rows:
        flag = " ⚠️" if err > 0 and ok == 0 else ""
        table.append(f"| {site_id} | {ok} | {err}{flag} |")
    lines.append("\n".join(table))
    return "\n".join(lines) + "\n"


def section_data_freshness():
    fresh = load_json('data_freshness.json', {})
    lines = ["## Stale fetchers"]
    stale = []
    for name, payload in (fresh.get('per_file') or {}).items():
        if not isinstance(payload, dict):
            continue
        age_h = payload.get('age_hours')
        max_h = payload.get('max_age_hours')
        if age_h is None or max_h is None:
            continue
        if age_h > max_h:
            stale.append((name, age_h, max_h))
    if not stale:
        lines.append("_All fetchers within freshness windows._")
        return "\n".join(lines) + "\n"
    stale.sort(key=lambda x: -x[1])
    for name, age, mx in stale[:10]:
        lines.append(f"- `{name}` — {age:.1f}h (max {mx}h)")
    return "\n".join(lines) + "\n"


def section_critical_recs():
    recs = load_json('recommendations.json', {})
    by_site = recs.get('per_site') or recs
    items = []
    for site, payload in (by_site.items() if isinstance(by_site, dict) else []):
        if not isinstance(payload, dict):
            continue
        for r in (payload.get('recommendations') or [])[:8]:
            if isinstance(r, dict) and (r.get('severity') or '').lower() in ('critical', 'high'):
                items.append({
                    'site': site,
                    'sev': r.get('severity'),
                    'title': r.get('title') or r.get('issue') or '',
                    'fix': r.get('fix') or r.get('action') or '',
                })
    lines = ["## Top critical/high recommendations"]
    if not items:
        lines.append("_No critical/high recommendations surfaced._")
        return "\n".join(lines) + "\n"
    items.sort(key=lambda i: 0 if i['sev'] == 'critical' else 1)
    for i in items[:10]:
        lines.append(f"- **{i['site']}** ({i['sev']}): {i['title']} — _{i['fix']}_")
    return "\n".join(lines) + "\n"


def section_indexing_health():
    h = load_json('indexing_health.json', {})
    per = h.get('per_site', {})
    lines = ["## Indexing health snapshot"]
    if not per:
        lines.append("_No indexing data._")
        return "\n".join(lines) + "\n"
    table = ["| Site | Today | 7d | Lifetime | Status |", "|---|---:|---:|---:|---|"]
    for site_id, s in per.items():
        today = (s.get('today') or {}).get('submitted', 0)
        seven = (s.get('last_7d') or {}).get('submitted', 0)
        lifetime = s.get('total_ever_submitted') or 0
        sitemap_size = s.get('sitemap_url_count') or 0
        status = s.get('status') or '?'
        table.append(f"| {site_id} | {today} | {seven} | {lifetime}/{sitemap_size} | {status} |")
    lines.append("\n".join(table))
    return "\n".join(lines) + "\n"


def build_digest():
    sections = [
        f"# Fleet Dashboard Daily Digest — {TODAY}",
        f"_Generated {NOW.isoformat()}_\n",
        section_indexed_delta(),
        section_indexing_submissions(),
        section_indexing_health(),
        section_data_freshness(),
        section_critical_recs(),
        "---",
        "Live: https://fleet-dashboard-1nt.pages.dev/ · https://rank4ai-dashboard.pages.dev/",
    ]
    return "\n".join(sections)


def md_to_html(md):
    """Trivial md → html for the email body. Tables + headings only."""
    import re
    lines = md.split("\n")
    out = []
    in_table = False
    for line in lines:
        if line.startswith('# '):
            out.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith('## '):
            out.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith('|'):
            if not in_table:
                out.append("<table style='border-collapse:collapse;font-family:monospace;font-size:13px'>")
                in_table = True
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if all(set(c) <= set('-: ') for c in cells):
                continue  # separator row
            tag = 'th' if not out or '<th' not in out[-1] else 'td'
            cells_html = ''.join(f"<{tag} style='padding:4px 10px;border:1px solid #ddd'>{c}</{tag}>" for c in cells)
            out.append(f"<tr>{cells_html}</tr>")
        else:
            if in_table:
                out.append("</table>")
                in_table = False
            if line.strip() == '---':
                out.append("<hr>")
            elif line.startswith('- '):
                out.append(f"<div style='margin:4px 0'>• {line[2:]}</div>")
            elif line.startswith('_') and line.endswith('_'):
                out.append(f"<p style='color:#888;font-style:italic'>{line[1:-1]}</p>")
            elif line.strip():
                out.append(f"<p>{line}</p>")
    if in_table:
        out.append("</table>")
    # bold + italic
    html = "\n".join(out)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'(?<!\*)\*(.+?)\*(?!\*)', r'<em>\1</em>', html)
    html = re.sub(r'`(.+?)`', r"<code style='background:#f4f4f4;padding:1px 4px;border-radius:3px'>\1</code>", html)
    return f"<html><body style='font-family:-apple-system,sans-serif;max-width:780px'>{html}</body></html>"


def send_email(md, html):
    if not SMTP_PASS:
        print("SMTP_PASS not set — skipping email; digest saved to disk only.")
        return False
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Fleet dashboard digest — {TODAY}"
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    msg.attach(MIMEText(md, 'plain'))
    msg.attach(MIMEText(html, 'html'))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(FROM_EMAIL, SMTP_PASS)
            smtp.send_message(msg)
        print(f"Email sent to {TO_EMAIL}")
        return True
    except Exception as e:
        print(f"SMTP failed: {e}")
        return False


def main():
    md = build_digest()
    html = md_to_html(md)

    # Always archive
    archive_path = ARCHIVE / f"digest_{TODAY}.md"
    archive_path.write_text(md)
    print(f"Archived: {archive_path}")

    send_email(md, html)


if __name__ == '__main__':
    main()
