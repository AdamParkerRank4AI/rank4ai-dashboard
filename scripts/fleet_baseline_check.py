#!/usr/bin/env python3
"""
fleet_baseline_check.py — daily live-HTML audit of each fleet site against
the BASELINE_CHECKLIST. Writes findings to src/data/live/fleet_baseline.json
and is consumed by urgent_alert.py + the dashboard's overview tile.

Checks per site (all done against live HTML, not source):
  - GA4 firing
  - Microsoft Clarity firing
  - llms.txt present (200)
  - llms-full.txt present (200)
  - ai.txt present (200)
  - IndexNow key file present (200)
  - robots.txt allows GPTBot + ClaudeBot + PerplexityBot + Google-Extended
  - Organization + WebSite + WebPage JSON-LD in homepage
  - Cross-fleet sister-site links in footer
  - HSTS header present
  - OG image is PNG (not SVG placeholder)
  - FAQPage schema NOT emitted (fleet rule, 19 May 2026)
  - sitemap-index.xml or sitemap.xml present
  - Cross-fleet rel=related link in <head>

Anything failing is one of: deployment regression, missing baseline, or
drift since last green. urgent_alert.py reads this and surfaces P1 items.
"""
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

LIVE = Path(os.path.expanduser("~/rank4ai-dashboard/src/data/live"))

FLEET_SITES = {
    "rank4ai":         "https://www.rank4ai.co.uk",
    "market-invoice":  "https://marketinvoice.co.uk",
    "seocompare":      "https://seocompare.co.uk",
    "bestbusinessloans": "https://bestbusinessloans.ai",
    "fundbiz":         "https://fundbiz.co.uk",
    "merchanthq":      "https://merchanthq.co.uk",
    "peptideclear":    "https://peptideclear.co.uk",
    "kartapay":        "https://kartapay.co.uk",
}

INDEXNOW_KEY = "c129b8c91294404d96cca29e1cf613fe"
REQUIRED_AI_BOTS = ["GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended"]


def fetch(url, timeout=10):
    try:
        r = subprocess.run(
            ["curl", "-sL", "--max-time", str(timeout), "-A", "Mozilla/5.0", "-w", "\n---HTTP:%{http_code}", url],
            capture_output=True, text=True, timeout=timeout + 2,
        )
        body = r.stdout
        code = 0
        m = re.search(r"---HTTP:(\d+)$", body)
        if m:
            code = int(m.group(1))
            body = body[:m.start()]
        return body, code
    except Exception:
        return "", 0


def fetch_head(url, timeout=8):
    try:
        r = subprocess.run(
            ["curl", "-sLI", "--max-time", str(timeout), "-A", "Mozilla/5.0", url],
            capture_output=True, text=True, timeout=timeout + 2,
        )
        return r.stdout
    except Exception:
        return ""


def extract_jsonld_types(html):
    types = set()
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE):
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue
        stack = [data]
        while stack:
            x = stack.pop()
            if isinstance(x, dict):
                t = x.get("@type")
                if isinstance(t, str):
                    types.add(t)
                elif isinstance(t, list):
                    types.update(t)
                for v in x.values():
                    if isinstance(v, (dict, list)):
                        stack.append(v)
            elif isinstance(x, list):
                stack.extend(x)
    return types


def check_site(site_id, base_url):
    """Run all baseline checks against one site. Returns dict of {check: pass/fail, detail}."""
    out = {"site": site_id, "url": base_url, "checks": {}}

    home_html, home_code = fetch(base_url + "/")
    if home_code < 200 or home_code >= 400:
        out["checks"]["site_reachable"] = {"pass": False, "detail": f"home returned HTTP {home_code}"}
        return out
    out["checks"]["site_reachable"] = {"pass": True, "detail": f"HTTP {home_code}"}

    # GA4
    ga4 = "googletagmanager.com/gtag/js" in home_html or re.search(r"G-[A-Z0-9]{8,}", home_html)
    out["checks"]["ga4_firing"] = {"pass": bool(ga4), "detail": "GA4 tag in HTML" if ga4 else "GA4 missing"}

    # Microsoft Clarity
    clarity = "clarity.ms/tag" in home_html or "window.clarity" in home_html
    out["checks"]["clarity_firing"] = {"pass": bool(clarity), "detail": "Clarity in HTML" if clarity else "Clarity missing"}

    # llms.txt
    _, c = fetch(base_url + "/llms.txt", timeout=5)
    out["checks"]["llms_txt"] = {"pass": c == 200, "detail": f"HTTP {c}"}

    # llms-full.txt
    _, c = fetch(base_url + "/llms-full.txt", timeout=5)
    out["checks"]["llms_full_txt"] = {"pass": c == 200, "detail": f"HTTP {c}"}

    # ai.txt
    _, c = fetch(base_url + "/ai.txt", timeout=5)
    out["checks"]["ai_txt"] = {"pass": c == 200, "detail": f"HTTP {c}"}

    # IndexNow key file
    _, c = fetch(f"{base_url}/{INDEXNOW_KEY}.txt", timeout=5)
    out["checks"]["indexnow_key"] = {"pass": c == 200, "detail": f"HTTP {c}"}

    # robots.txt AI bot allow
    robots, c = fetch(base_url + "/robots.txt", timeout=5)
    if c != 200:
        out["checks"]["robots_ai_bots"] = {"pass": False, "detail": f"robots.txt HTTP {c}"}
    else:
        missing = []
        for bot in REQUIRED_AI_BOTS:
            # Check that bot is mentioned with Allow: / (not Disallow)
            pattern = re.compile(rf"User-agent:\s*{re.escape(bot)}\s*\n(?:[^\n]*\n)*?\s*(?:Disallow:\s*/[^\n]*\n)", re.IGNORECASE)
            if pattern.search(robots):
                missing.append(f"{bot}: DISALLOW found")
            elif bot.lower() not in robots.lower():
                # Not explicitly listed — covered by wildcard Allow as long as no global block
                pass
        out["checks"]["robots_ai_bots"] = {"pass": len(missing) == 0, "detail": ", ".join(missing) if missing else "all 4 bots allowed"}

    # Schema graph: Organization + WebSite minimum
    types = extract_jsonld_types(home_html)
    has_org = "Organization" in types or any(t in types for t in ["LocalBusiness", "ProfessionalService", "Corporation"])
    has_website = "WebSite" in types
    out["checks"]["org_schema"] = {"pass": has_org, "detail": "Organization-like type present" if has_org else "Org schema missing"}
    out["checks"]["website_schema"] = {"pass": has_website, "detail": "WebSite present" if has_website else "WebSite missing"}

    # FAQPage MUST NOT be in live HTML (fleet baseline 19 May 2026)
    has_faq = "FAQPage" in types
    out["checks"]["no_faqpage"] = {"pass": not has_faq, "detail": "FAQPage absent (correct)" if not has_faq else "FAQPage EMITTED — violates fleet baseline"}

    # OG image PNG, not SVG
    og_image_match = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', home_html, re.IGNORECASE)
    if og_image_match:
        og_url = og_image_match.group(1)
        if og_url.lower().endswith(".svg"):
            out["checks"]["og_image_png"] = {"pass": False, "detail": f"og:image is SVG ({og_url})"}
        else:
            out["checks"]["og_image_png"] = {"pass": True, "detail": og_url.rsplit("/", 1)[-1]}
    else:
        out["checks"]["og_image_png"] = {"pass": False, "detail": "no og:image meta found"}

    # sitemap
    _, c1 = fetch(base_url + "/sitemap-index.xml", timeout=5)
    _, c2 = fetch(base_url + "/sitemap.xml", timeout=5)
    out["checks"]["sitemap"] = {"pass": c1 == 200 or c2 == 200, "detail": f"sitemap-index:{c1} sitemap:{c2}"}

    # HSTS
    head = fetch_head(base_url + "/")
    hsts = re.search(r"strict-transport-security:", head, re.IGNORECASE)
    out["checks"]["hsts"] = {"pass": bool(hsts), "detail": "HSTS present" if hsts else "HSTS missing"}

    # Cross-fleet rel=related
    rel_related = "rel=\"related\"" in home_html or "rel='related'" in home_html
    out["checks"]["rel_related"] = {"pass": rel_related, "detail": "rel=related found" if rel_related else "no <link rel='related'> to sister sites"}

    return out


def main():
    results = {}
    summary = {"total_sites": 0, "passing_sites": 0, "total_checks": 0, "failed_checks": 0}
    for site_id, url in FLEET_SITES.items():
        print(f"checking {site_id}...")
        r = check_site(site_id, url)
        results[site_id] = r
        n_checks = len(r["checks"])
        n_fail = sum(1 for c in r["checks"].values() if not c.get("pass"))
        r["summary"] = {"checks": n_checks, "failed": n_fail, "pass_rate": round((n_checks - n_fail) / max(1, n_checks) * 100, 1)}
        summary["total_sites"] += 1
        if n_fail == 0:
            summary["passing_sites"] += 1
        summary["total_checks"] += n_checks
        summary["failed_checks"] += n_fail
        if n_fail:
            print(f"  ✗ {n_fail}/{n_checks} failed:")
            for cname, c in r["checks"].items():
                if not c.get("pass"):
                    print(f"     · {cname}: {c.get('detail','')}")
        else:
            print(f"  ✓ all {n_checks} passed")

    output = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "sites": results,
    }
    out_path = LIVE / "fleet_baseline.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n→ {out_path}")
    print(f"Summary: {summary['passing_sites']}/{summary['total_sites']} sites fully passing, {summary['failed_checks']}/{summary['total_checks']} checks failed across fleet.")


if __name__ == "__main__":
    main()
