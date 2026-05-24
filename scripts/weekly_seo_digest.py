#!/usr/bin/env python3
"""
weekly_seo_digest.py — Saturday morning email pulling together the week's
highest-ROI SEO opportunities per site.

4 signal sources:
  - striking_distance.json   (pos 11-20, ≥30 imp, the closest wins)
  - content_decay.json       (queries that lost positions this week)
  - cannibalisation.json     (2+ pages competing for same query)
  - intent_split.json        (branded-competitor + transactional 0-click queries)

Output: HTML email to adam@muswellrose.com via Gmail SMTP, with per-site
recommendations + GSC URL Inspection deep-links for one-click verification.
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

TO_EMAIL = "adam@muswellrose.com"
FROM_EMAIL = os.environ.get("SMTP_USER", "adam@muswellrose.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "")

# Per-site GSC property for inspect deep-links
SITE_RESOURCES = {
    "rank4ai":           ("Rank4AI",           "sc-domain:rank4ai.co.uk"),
    "market-invoice":    ("Market Invoice",    "sc-domain:marketinvoice.co.uk"),
    "seocompare":        ("SEO Compare",       "sc-domain:seocompare.co.uk"),
    "bestbusinessloans": ("BestBusinessLoans", "https://bestbusinessloans.ai/"),
    "fundbiz":           ("FundBiz",           "https://fundbiz.co.uk/"),
    "cardmachines":      ("MerchantHQ",        "https://merchanthq.co.uk/"),
    "peptideclear":      ("PeptideClear",      "https://peptideclear.co.uk/"),
    "kartapay":          ("Kartapay",          "https://kartapay.co.uk/"),
}


def load(name):
    p = LIVE / name
    if not p.exists(): return {}
    try: return json.load(open(p))
    except Exception: return {}


def gsc_link(resource_id, url):
    return ("https://search.google.com/search-console/inspect"
            f"?resource_id={quote(resource_id, safe='')}"
            f"&id={quote(url, safe='')}")


def build_section_for_site(site_id, display_name, resource_id, striking, decay, cannibal, intent):
    """Return (has_content, html_section) for one site."""
    parts = []
    has_content = False

    # Striking distance
    sd = striking.get("sites", {}).get(site_id, {})
    if sd.get("count", 0) > 0:
        has_content = True
        parts.append('<h4 style="color:#10b981;margin:18px 0 6px;font-size:13px;font-weight:700">⚡ Striking distance (lift to page 1)</h4>')
        parts.append('<table cellpadding="0" cellspacing="0" style="width:100%;font:13px -apple-system,sans-serif"><tbody>')
        for q in sd.get("top", [])[:5]:
            url = f"https://{resource_id.replace('sc-domain:','')}/" if resource_id.startswith("sc-domain:") else resource_id
            inspect = gsc_link(resource_id, q.get("query", ""))
            parts.append(f"""
            <tr><td style="padding:6px 0;vertical-align:top;color:#444">
              "<b>{q.get('query','')}</b>" — pos {q.get('position',0):.0f}, {q.get('impressions',0)} imp,
              <span style="color:#10b981">+{q.get('potential_clicks_at_page_1',0)} clicks if lifted</span>
              <br><a href="{inspect}" style="color:#1a73e8;font-size:11px">Inspect query in GSC →</a>
            </td></tr>
            """)
        parts.append('</tbody></table>')

    # Cannibalisation
    cn = cannibal.get("sites", {}).get(site_id, {})
    if cn.get("count", 0) > 0:
        has_content = True
        parts.append('<h4 style="color:#dc2626;margin:18px 0 6px;font-size:13px;font-weight:700">⚠ Cannibalisation (2+ pages competing)</h4>')
        for c in cn.get("top", [])[:3]:
            parts.append(f'<div style="margin:6px 0;font:13px -apple-system,sans-serif"><b>"{c.get("query","")}"</b> — {c.get("competing_pages",0)} pages, {c.get("total_impressions",0)} imp</div>')
            parts.append('<table cellpadding="0" cellspacing="0" style="width:100%;margin-left:12px;border-left:2px solid #fee2e2;padding-left:8px;font:12px -apple-system,sans-serif"><tbody>')
            for p in c.get("pages", [])[:3]:
                parts.append(f'<tr><td style="padding:2px 0;color:#666">pos {p.get("position",0):.0f} · {p.get("page","")}</td></tr>')
            parts.append('</tbody></table>')

    # Decay
    dc = decay.get("sites", {}).get(site_id, {})
    if dc.get("total_decayed", 0) > 0:
        has_content = True
        parts.append(f'<h4 style="color:#f59e0b;margin:18px 0 6px;font-size:13px;font-weight:700">📉 Content decay (lost positions since {decay.get("compared_to","?")})</h4>')
        for cat in ["dropped_off_page_1", "position_drop", "impressions_collapse"]:
            items = dc.get(cat, [])
            if not items: continue
            label = {"dropped_off_page_1": "Fell off page 1",
                     "position_drop": "Dropped 5+ positions",
                     "impressions_collapse": "Impressions halved"}[cat]
            parts.append(f'<div style="font-size:12px;color:#666;margin:6px 0 4px"><b>{label}:</b></div>')
            for q in items[:3]:
                parts.append(f'<div style="font:12px -apple-system,sans-serif;color:#444;margin-left:8px">· "{q.get("query","")}" — pos {q.get("position_before",0):.0f} → {q.get("position_now",0):.0f}</div>')

    # Intent gaps
    it = intent.get("sites", {}).get(site_id, {})
    if it:
        b = it.get("buckets", {})
        bc = b.get("branded_competitor", {})
        tx = b.get("transactional", {})
        if bc.get("total_impressions", 0) >= 10 and bc.get("total_clicks", 0) == 0:
            has_content = True
            parts.append('<h4 style="color:#7c3aed;margin:18px 0 6px;font-size:13px;font-weight:700">🎯 Competitor queries leaking (build /alternatives/)</h4>')
            for q in bc.get("top", [])[:5]:
                parts.append(f'<div style="font:12px -apple-system,sans-serif;color:#444;margin-left:8px">· "{q.get("query","")}" — {q.get("impressions",0)} imp, pos {q.get("position",0):.0f}</div>')
        if tx.get("total_impressions", 0) >= 50 and tx.get("total_clicks", 0) == 0:
            has_content = True
            parts.append('<h4 style="color:#7c3aed;margin:18px 0 6px;font-size:13px;font-weight:700">💰 Transactional queries leaking (sharpen titles + tools)</h4>')
            for q in tx.get("top", [])[:5]:
                parts.append(f'<div style="font:12px -apple-system,sans-serif;color:#444;margin-left:8px">· "{q.get("query","")}" — {q.get("impressions",0)} imp, pos {q.get("position",0):.0f}</div>')

    if has_content:
        return True, f'<section style="margin-top:24px;border-top:1px solid #e5e7eb;padding-top:16px"><h3 style="font:700 16px -apple-system,sans-serif;margin:0 0 8px;color:#111">{display_name}</h3>' + "".join(parts) + '</section>'
    return False, ""


def main():
    striking = load("striking_distance.json")
    decay = load("content_decay.json")
    cannibal = load("cannibalisation.json")
    intent = load("intent_split.json")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sections = []
    sites_with_signal = 0
    for site_id, (display, resource) in SITE_RESOURCES.items():
        has, html = build_section_for_site(site_id, display, resource, striking, decay, cannibal, intent)
        if has:
            sections.append(html)
            sites_with_signal += 1

    if not sections:
        print("[weekly_seo_digest] No actionable signals this week — skipping email")
        return

    html_body = f"""<!doctype html>
<html><body style="margin:0;padding:24px;background:#f7f7f7;font:14px -apple-system,sans-serif;color:#222">
<div style="max-width:720px;margin:0 auto;background:#fff;padding:28px;border-radius:8px">
<h1 style="font:700 22px -apple-system,sans-serif;margin:0 0 6px;color:#111">Weekly SEO digest — {today}</h1>
<p style="color:#666;font-size:13px;margin:0 0 4px">{sites_with_signal} site(s) with actionable signals</p>
<p style="color:#444;font-size:13px;line-height:1.5;margin:8px 0 0">
  Four detectors run weekly:
  <span style="color:#10b981">⚡ Striking distance</span> (lift page-2 to page-1),
  <span style="color:#dc2626">⚠ Cannibalisation</span> (2+ pages competing),
  <span style="color:#f59e0b">📉 Decay</span> (lost positions),
  <span style="color:#7c3aed">🎯 Intent gaps</span> (competitor / transactional queries leaking).
</p>
{''.join(sections)}
<p style="color:#999;font-size:11px;margin-top:24px;border-top:1px solid #eee;padding-top:12px">
  rank4ai-dashboard / weekly_seo_digest.py · runs Saturdays 09:00 via launchd
</p>
</div></body></html>"""

    plain = f"Weekly SEO digest — {today}\n{sites_with_signal} site(s) with signal\nSee HTML version for clickable GSC inspect links."

    if not SMTP_PASS:
        print("[weekly_seo_digest] SMTP_PASS not set — printing instead")
        print(plain)
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Weekly SEO digest — {today} ({sites_with_signal} sites)"
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(FROM_EMAIL, SMTP_PASS)
            s.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
        print(f"[weekly_seo_digest] Sent: {sites_with_signal} sites")
    except Exception as e:
        print(f"[weekly_seo_digest] FAILED: {e}")


if __name__ == "__main__":
    main()
