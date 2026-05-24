#!/usr/bin/env python3
"""
daily_top_linkers.py — every morning, find the top 5 pages per site by
outgoing internal links, submit them to Google Indexing API, and email
Adam a summary.

The logic: pages with the most outgoing internal links act as "trust hubs"
in the link graph. Submitting them for re-index gives Google's crawler a
fresh entry point that surfaces every page they link to. Re-indexing the
top linkers is the most efficient way to push trust + discovery into the
fleet's long tail.

Runs daily via launchd. Reads crawl_<site>.json (already updated by
read_fleet_source.py earlier in the cron chain).
"""
import json
import os
import smtplib
import sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from urllib.parse import quote

LIVE = Path(os.path.expanduser("~/rank4ai-dashboard/src/data/live"))
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

# Reuse the existing Google Indexing API submitter
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_FILE = Path(os.path.expanduser("~/rank4ai-dashboard/scripts/ga4_token.json"))
TOP_N = 5

# Each site's friendly name + crawl key + GSC resource_id (URL-encoded form
# that the deep-link expects). sc-domain properties → "sc-domain:host", and
# URL-prefix properties → the full URL.
SITES = [
    ("rank4ai",           "Rank4AI",           "sc-domain:rank4ai.co.uk"),
    ("market-invoice",    "Market Invoice",    "sc-domain:marketinvoice.co.uk"),
    ("seocompare",        "SEO Compare",       "sc-domain:seocompare.co.uk"),
    ("bestbusinessloans", "BestBusinessLoans", "https://bestbusinessloans.ai/"),
    ("fundbiz",           "FundBiz",           "https://fundbiz.co.uk/"),
    ("cardmachines",      "MerchantHQ",        "https://merchanthq.co.uk/"),
    ("peptideclear",      "PeptideClear",      "https://peptideclear.co.uk/"),
    ("kartapay",          "Kartapay",          "https://kartapay.co.uk/"),
]


def gsc_inspect_link(resource_id, url):
    """Deep-link to GSC URL Inspection with the URL pre-filled in the
    search bar. Click → opens GSC straight on the inspect screen for
    that URL, no copy-paste needed."""
    return (
        "https://search.google.com/search-console/inspect"
        f"?resource_id={quote(resource_id, safe='')}"
        f"&id={quote(url, safe='')}"
    )


def bing_inspect_link(host, url):
    """Bing Webmaster URL Inspection deep-link (separate property)."""
    return (
        "https://www.bing.com/webmasters/url-inspection"
        f"?siteUrl={quote(host, safe='')}"
        f"&url={quote(url, safe='')}"
    )

TO_EMAIL = "adam@muswellrose.com"
FROM_EMAIL = os.environ.get("SMTP_USER", "adam@muswellrose.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "")


def get_creds():
    with open(TOKEN_FILE) as f:
        t = json.load(f)
    creds = Credentials(
        token=t["token"],
        refresh_token=t["refresh_token"],
        token_uri=t["token_uri"],
        client_id=t["client_id"],
        client_secret=t["client_secret"],
        scopes=t.get("scopes", []),
    )
    if creds.expired or not creds.valid:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
    return creds


def top_linkers(site_key, n=TOP_N):
    p = LIVE / f"crawl_{site_key}.json"
    if not p.exists():
        return []
    try:
        d = json.load(open(p))
    except Exception:
        return []
    pages = d.get("pages", [])
    # Exclude index pages, search, tag pages from the top — they're already
    # well-linked AND less useful for fresh indexing
    EXCLUDED = ("/search", "/tag/", "/page/", "/feed", "/sitemap", "/404", "/api/")
    candidates = [p for p in pages if not any(x in p.get("path", "") for x in EXCLUDED)]
    candidates.sort(key=lambda p: -p.get("internal_links_out", 0))
    return candidates[:n]


def submit_to_google(creds, urls):
    """Submit URLs to Google Indexing API. Returns (ok_count, errors)."""
    svc = build("indexing", "v3", credentials=creds, cache_discovery=False)
    ok = 0
    errors = []
    for u in urls:
        try:
            svc.urlNotifications().publish(body={"url": u, "type": "URL_UPDATED"}).execute()
            ok += 1
        except Exception as e:
            errors.append(f"{u}: {str(e)[:120]}")
    return ok, errors


def build_email_bodies(report, total_submitted, total_errors):
    """Returns (plain_text, html). HTML version has clickable GSC/Bing inspect
    deep-links per URL so Adam can one-click into the search bar prefilled."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ── PLAIN TEXT ──
    plain = [
        f"Daily Top Linkers — {today}",
        "",
        f"Submitted {total_submitted} URLs across the fleet to Google's Indexing API.",
        f"{'(' + str(total_errors) + ' errors)' if total_errors else 'No errors.'}",
        "",
        "Top 5 most-internally-linked pages per site. Re-indexing these hubs",
        "gives Google a fresh entry to every page they link to.",
        "",
    ]
    for site_name, items, resource_id, host in report:
        if not items:
            plain.append(f"━ {site_name}: no crawl data")
            plain.append("")
            continue
        plain.append(f"━ {site_name}")
        for p in items:
            url = p.get("url", "")
            out = p.get("internal_links_out", 0)
            title = (p.get("title") or "").split(" | ")[0][:70]
            plain.append(f"  {out:>3} links | {url}")
            plain.append(f"            {title}")
            plain.append(f"            GSC inspect: {gsc_inspect_link(resource_id, url)}")
        plain.append("")
    plain.append("— rank4ai-dashboard / daily_top_linkers.py")
    plain_text = "\n".join(plain)

    # ── HTML ──
    rows = []
    for site_name, items, resource_id, host in report:
        if not items:
            rows.append(f'<h3 style="font:600 14px -apple-system,system-ui,sans-serif;color:#888;margin:18px 0 4px">{site_name}</h3><p style="color:#999;font:13px -apple-system,system-ui,sans-serif">no crawl data</p>')
            continue
        rows.append(f'<h3 style="font:700 15px -apple-system,system-ui,sans-serif;color:#111;margin:24px 0 6px;border-top:1px solid #eee;padding-top:14px">{site_name}</h3>')
        rows.append('<table cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;font:13px -apple-system,system-ui,sans-serif">')
        for p in items:
            url = p.get("url", "")
            out = p.get("internal_links_out", 0)
            title = (p.get("title") or "").split(" | ")[0][:80]
            gsc = gsc_inspect_link(resource_id, url)
            bing = bing_inspect_link(host, url)
            rows.append(f"""
            <tr>
              <td style="padding:8px 10px 8px 0;vertical-align:top;width:60px;color:#10b981;font-weight:600;font-variant-numeric:tabular-nums">{out}</td>
              <td style="padding:8px 0;vertical-align:top">
                <a href="{url}" style="color:#1d4ed8;text-decoration:none;font-weight:600;word-break:break-all">{url}</a>
                <div style="color:#666;margin-top:2px;font-size:12px">{title}</div>
                <div style="margin-top:4px">
                  <a href="{gsc}" style="display:inline-block;background:#1a73e8;color:#fff;text-decoration:none;font-size:11px;font-weight:600;padding:4px 10px;border-radius:4px;margin-right:6px">Open in GSC →</a>
                  <a href="{bing}" style="display:inline-block;background:#0078d4;color:#fff;text-decoration:none;font-size:11px;font-weight:600;padding:4px 10px;border-radius:4px">Open in Bing →</a>
                </div>
              </td>
            </tr>
            """)
        rows.append('</table>')

    html = f"""<!doctype html>
<html>
<body style="margin:0;padding:24px;background:#f7f7f7;font:14px -apple-system,system-ui,sans-serif;color:#222">
  <div style="max-width:720px;margin:0 auto;background:#fff;padding:28px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">
    <h1 style="font:700 22px -apple-system,system-ui,sans-serif;margin:0 0 4px;color:#111">Daily Top Linkers</h1>
    <p style="color:#888;font-size:13px;margin:0 0 18px">{today} · {total_submitted} URLs submitted to Google's Indexing API{(', ' + str(total_errors) + ' errors') if total_errors else ''}</p>
    <p style="color:#444;font-size:13px;line-height:1.5;margin:0 0 12px">
      Top 5 most-internally-linked pages per site. Each one is a "trust hub" — re-indexing it gives Google a fresh entry to every page it links to. Click <b>Open in GSC</b> to inspect a URL with the search bar pre-filled.
    </p>
    {''.join(rows)}
    <p style="color:#999;font-size:11px;margin-top:24px;border-top:1px solid #eee;padding-top:12px">
      rank4ai-dashboard / daily_top_linkers.py · runs daily 09:15 via launchd
    </p>
  </div>
</body>
</html>"""
    return plain_text, html


def send_email(plain_text, html, total_submitted):
    if not SMTP_PASS:
        print("[daily_top_linkers] SMTP_PASS not set — printing report instead:")
        print(plain_text)
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Fleet daily top-linkers ({total_submitted} URLs submitted)"
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html, "html"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(FROM_EMAIL, SMTP_PASS)
            s.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
        print(f"[daily_top_linkers] Email sent ({total_submitted} URLs)")
        return True
    except Exception as e:
        print(f"[daily_top_linkers] Email failed: {e}")
        return False


def main():
    dry = "--dry" in sys.argv
    report = []
    all_urls = []
    for key, name, resource_id in SITES:
        items = top_linkers(key)
        # Host for Bing inspect link (origin only)
        host = resource_id if resource_id.startswith("http") else f"https://{resource_id.replace('sc-domain:', '')}/"
        report.append((name, items, resource_id, host))
        for p in items:
            url = p.get("url")
            if url:
                all_urls.append(url)

    total_submitted = 0
    errors = []
    if not dry:
        try:
            creds = get_creds()
            total_submitted, errors = submit_to_google(creds, all_urls)
        except Exception as e:
            errors = [f"creds: {str(e)[:200]}"]

    plain_text, html = build_email_bodies(report, total_submitted, len(errors))
    if dry:
        print("[dry] Would submit (plain text preview):")
        print(plain_text)
        return 0
    send_email(plain_text, html, total_submitted)
    # Persist a JSON record for the dashboard
    out_path = LIVE / "top_linkers.json"
    with open(out_path, "w") as f:
        json.dump({
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "submitted": total_submitted,
            "errors": errors,
            "sites": {
                name: [
                    {
                        "url": p["url"],
                        "path": p.get("path"),
                        "internal_links_out": p.get("internal_links_out", 0),
                        "title": (p.get("title") or "").split(" | ")[0][:80],
                        "gsc_inspect": gsc_inspect_link(resource_id, p["url"]),
                    }
                    for p in items
                ]
                for name, items, resource_id, _host in report
            },
        }, f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
