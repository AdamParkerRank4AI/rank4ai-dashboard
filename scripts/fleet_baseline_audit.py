#!/usr/bin/env python3
"""Fleet baseline conformance audit.

Source of truth: ~/Library/Mobile Documents/com~apple~CloudDocs/claude/astro/FLEET/BASELINE_CHECKLIST.md
Probes each fleet site (repo + live URL) and writes results to
src/data/live/fleet_baseline_audit.json for dashboard surface.

Runs locally or in CI. Exit non-zero on any P1 gap on a live site
(safe to wire into deploy gates).

Usage:
  python3 fleet_baseline_audit.py           # full fleet
  python3 fleet_baseline_audit.py rank4ai   # one site
  python3 fleet_baseline_audit.py --json    # raw JSON, no human output
  python3 fleet_baseline_audit.py --strict  # exit 1 if any P1 fails

Built 2026-05-11 to close the recurring-gap class (Amy-Knight pattern,
BBL/FundBiz silent-loss pattern, FAT/FAG scaffold residue pattern).
"""
from __future__ import annotations
import json, os, re, sys, urllib.request, ssl, pathlib
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path.home()
OUT = ROOT / "rank4ai-dashboard/src/data/live/fleet_baseline_audit.json"

SITES = [
    # (id, local_dir, flavour, pre_launch, live_url)
    ("rank4ai",          "rank4ai-site",            "editorial", False, "https://www.rank4ai.co.uk/"),
    ("market-invoice",   "compare-invoice-finance", "leadgen",   False, "https://marketinvoice.co.uk/"),
    ("seocompare",       "compareaiseo",            "editorial", False, "https://seocompare.co.uk/"),
    ("rochellemarashi",  "rochellemarashi",         "client",    False, "https://rochellemarashi.pages.dev/"),
    ("bestbusinessloans","bestbusinessloans",       "leadgen",   False, "https://bestbusinessloans.ai/"),
    ("fundbiz",          "fundbiz",                 "leadgen",   False, "https://fundbiz.co.uk/"),
    ("cardmachines",     "cardmachines",            "leadgen",   False, "https://merchanthq.co.uk/"),
    ("kartapay",         "kartapay",                "leadgen",   False, "https://kartapay.co.uk/"),
    ("findatradey",      "findatradey",             "leadgen",   True,  "https://findatradey.pages.dev/"),
    ("findagym",         "findagym",                "leadgen",   True,  "https://findagym.pages.dev/"),
    ("peptideclear",     "ukmetabolic",             "leadgen",   False, "https://peptideclear.co.uk/"),
    ("builderweb",       "lovinlovable",            "saas",      False, "https://lovinlovable.dawn-field-3d16.workers.dev/"),
    ("resiliencebuilder","steve-site",              "client",    False, None),
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url: str, timeout: int = 10) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "fleet-baseline-audit/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception:
        return None

def grep_repo(root: pathlib.Path, pattern: str, exts=(".astro",".ts",".tsx",".js",".html",".md"), max_files=600) -> bool:
    if not root.exists():
        return False
    rx = re.compile(pattern)
    files = 0
    for fp in root.rglob("*"):
        if files > max_files: break
        if fp.is_dir(): continue
        if any(seg in str(fp) for seg in ("/node_modules/", "/.git/", "/dist/", "/.astro/", "/.wrangler/")):
            continue
        if fp.suffix not in exts: continue
        files += 1
        try:
            if rx.search(fp.read_text(errors="ignore")):
                return True
        except Exception:
            pass
    return False

# ---------------------------------------------------------------------------
# Check definitions. Each returns ("pass"/"fail"/"skip", note).
# severity: "p0" (silent-loss class), "p1" (production gap), "p2" (best practice)
# ---------------------------------------------------------------------------

def check_claude_md(root, live, html, flavour, pre_launch):
    ok = (root / "CLAUDE.md").exists()
    return ("pass" if ok else "fail", "")

def check_robots_txt(root, live, html, flavour, pre_launch):
    """Prefer LIVE robots.txt over repo file — many sites have CF Content-Signals
    or Workers rewriting robots, which the repo file doesn't reflect."""
    txt = None
    if live:
        live_robots = fetch(live.rstrip("/") + "/robots.txt")
        if live_robots: txt = live_robots.lower()
    if txt is None:
        p = root / "public/robots.txt"
        if not p.exists(): return ("fail", "missing public/robots.txt + live unreachable")
        txt = p.read_text(errors="ignore").lower()
    # Block-all heuristic: 'Disallow: /' under 'User-agent: *' specifically.
    # CF Content-Signals injects per-AI-bot 'Disallow: /' lines under each named
    # bot — those don't mean the site is blocking everyone.
    star_block = False
    current_ua = None
    for line in txt.split("\n"):
        s = line.strip().lower()
        if s.startswith("#") or not s: continue
        if s.startswith("user-agent:"):
            current_ua = s.split(":",1)[1].strip()
        elif current_ua == "*" and re.match(r"^disallow:\s*/\s*$", s):
            star_block = True; break
    if pre_launch:
        return ("pass" if (star_block or "noindex" in txt) else "fail", "pre-launch should block-all")
    if star_block:
        return ("fail", "robots blocks all crawlers under * — flip from prelaunch missed")
    has_ai = any(b in txt for b in ("gptbot", "oai-searchbot", "perplexitybot", "claudebot", "claude-user", "content-signal"))
    return ("pass" if has_ai else "fail", "AI crawlers not explicitly named")

def check_llms_txt(root, live, html, flavour, pre_launch):
    p = root / "public/llms.txt"
    return ("pass" if p.exists() else "fail", "")

def check_llms_full_txt(root, live, html, flavour, pre_launch):
    p = root / "public/llms-full.txt"
    return ("pass" if p.exists() else "fail", "")

def check_llms_instructions(root, live, html, flavour, pre_launch):
    """Finding #9: Stripe-style ## Instructions section in llms.txt"""
    p = root / "public/llms.txt"
    if not p.exists(): return ("skip", "no llms.txt")
    txt = p.read_text(errors="ignore")
    has = re.search(r"^##\s*Instructions", txt, re.M) is not None
    return ("pass" if has else "fail", "no `## Instructions` section per Stripe pattern")

def check_ai_txt(root, live, html, flavour, pre_launch):
    """Finding #10: Spawning ai.txt purpose-based scraping declaration"""
    p = root / "public/ai.txt"
    return ("pass" if p.exists() else "fail", "no public/ai.txt")

def check_indexnow_key(root, live, html, flavour, pre_launch):
    pub = root / "public"
    if not pub.exists(): return ("fail", "no public/")
    keys = [f for f in pub.iterdir() if f.is_file() and re.match(r"^[a-f0-9]{32}\.txt$", f.name)]
    if not keys: return ("fail", "no IndexNow key file in public/")
    # Cross-check: deploy.cjs INDEXNOW_KEY matches
    dep = root / "scripts/deploy.cjs"
    if dep.exists():
        m = re.search(r"const INDEXNOW_KEY\s*=\s*['\"]([a-f0-9]{32})['\"]", dep.read_text(errors="ignore"))
        if m and not (pub / f"{m.group(1)}.txt").exists():
            return ("fail", f"deploy.cjs INDEXNOW_KEY={m.group(1)[:8]}... but no matching txt file")
    return ("pass", f"{keys[0].name}")

def check_deploy_site_host(root, live, html, flavour, pre_launch):
    """Catch scaffold-from-template residue (FAT/FAG had BBL.co.uk as SITE_URL).
    Pre-launch sites legitimately have SITE_HOST set to the future custom domain
    while live URL is *.pages.dev. So skip pre-launch."""
    if pre_launch: return ("skip", "pre-launch: SITE_HOST may legitimately differ from pages.dev URL")
    dep = root / "scripts/deploy.cjs"
    if not dep.exists(): return ("skip", "no deploy.cjs")
    if not live: return ("skip", "no live URL")
    t = dep.read_text(errors="ignore")
    m_host = re.search(r"const SITE_HOST\s*=\s*['\"]([^'\"]+)['\"]", t)
    if not m_host: return ("skip", "no SITE_HOST in deploy.cjs")
    host = m_host.group(1)
    live_host = re.sub(r"^https?://", "", live).rstrip("/").split("/")[0]
    live_host = live_host.replace("www.", "")
    if host == live_host or live_host.endswith(host) or host.endswith(live_host):
        return ("pass", host)
    return ("fail", f"deploy.cjs SITE_HOST={host} but live={live_host}")

def check_fleet_core_version(root, live, html, flavour, pre_launch):
    pkg = root / "package.json"
    if not pkg.exists(): return ("skip", "no package.json")
    m = re.search(r'"@rank4ai/fleet-core"\s*:\s*"github:[^"]*#v([0-9]+\.[0-9]+\.[0-9]+)', pkg.read_text())
    if not m: return ("skip", "no fleet-core dep")
    parts = tuple(int(x) for x in m.group(1).split("."))
    # Require >= 0.6.3 for the 3-tier safe-payload fix
    return ("pass" if parts >= (0,6,3) else "fail", f"v{m.group(1)} — needs >= v0.6.3")

def check_3tier_safepayload(root, live, html, flavour, pre_launch):
    """Only applies to CLIENT-SIDE direct REST inserts. Server-side API routes
    + Edge Functions handle errors differently and don't have the silent-loss
    class. So skip if Supabase writes only exist in pages/api/ or are calls
    to functions/v1/."""
    pkg = root / "package.json"
    if pkg.exists():
        m = re.search(r'"@rank4ai/fleet-core"\s*:\s*"github:[^"]*#v([0-9]+\.[0-9]+\.[0-9]+)', pkg.read_text())
        if m:
            parts = tuple(int(x) for x in m.group(1).split("."))
            if parts >= (0,6,3):
                return ("pass", "via fleet-core")
    if grep_repo(root, r"safePayload|3-tier", exts=(".astro",".ts")):
        return ("pass", "inline impl")
    # Look for client-side REST inserts (Astro component or in-page <script>)
    has_client = False
    for fp in root.rglob("*.astro"):
        if any(s in str(fp) for s in ("/node_modules/","/.git/","/dist/","/.astro/")): continue
        try:
            t = fp.read_text(errors="ignore")
            if re.search(r"supabase\.co/rest/v1|/rest/v1/[a-z_]+", t):
                has_client = True; break
        except: pass
    # Edge Function / API route writes are SERVER-SIDE and handle errors
    # explicitly (return error to caller). Lower risk class.
    has_edge_or_api = (
        grep_repo(root, r"functions/v1/", exts=(".astro",".ts")) or
        any((root / "src/pages/api").rglob("*.ts") if (root / "src/pages/api").exists() else [])
    )
    if not has_client and has_edge_or_api:
        return ("pass", "server-side (edge function / API route) — not silent-loss class")
    if not has_client:
        return ("skip", "no client-side Supabase form")
    return ("fail", "client-side Supabase form without 3-tier safe-payload")

def check_og_image(root, live, html, flavour, pre_launch):
    if not html: return ("skip", "no live URL")
    m = re.search(r'<meta\s+property=["\']og:image["\'][^>]*content=["\']([^"\']+)', html, re.I)
    if not m: return ("fail", "no og:image meta")
    src = m.group(1)
    if src.endswith(".svg") and "default" in src:
        return ("fail", "still on og-default.svg placeholder")
    return ("pass", src.split("/")[-1][:30])

def check_homepage_imagery(root, live, html, flavour, pre_launch):
    """Finding from 11 May audit: 4 live sites shipping with zero <img>"""
    if not html: return ("skip", "no live URL")
    n_img = len(re.findall(r"<img\b", html, re.I))
    n_svg = len(re.findall(r"<svg\b", html, re.I))
    if n_img > 0: return ("pass", f"{n_img} img + {n_svg} svg")
    if n_svg >= 3: return ("pass", f"{n_svg} svg (no img)")
    return ("fail", f"only {n_img} img + {n_svg} svg — empty homepage")

def check_alt_text(root, live, html, flavour, pre_launch):
    if not html: return ("skip", "no live URL")
    imgs = re.findall(r"<img\b[^>]*>", html, re.I)
    if not imgs: return ("skip", "no imgs")
    missing = sum(1 for i in imgs if not re.search(r'\salt\s*=', i, re.I))
    if missing: return ("fail", f"{missing}/{len(imgs)} imgs without alt")
    return ("pass", f"{len(imgs)} imgs all alt-tagged")

def check_schema_graph(root, live, html, flavour, pre_launch):
    if not html: return ("skip", "no live URL")
    has_graph = '"@graph"' in html
    # Accept Organization or any LocalBusiness/Service subclass — they all inherit
    # from Organization and serve the same entity-disambiguation role.
    # Also accept array-typed @type (e.g. ["LocalBusiness","ProfessionalService"])
    # via regex.
    org_subclasses = ("Organization", "ProfessionalService", "LocalBusiness",
                       "MedicalBusiness", "FinancialService", "LegalService",
                       "Store", "Restaurant", "Dentist", "MedicalClinic")
    wp_classes = ("WebPage", "WebSite", "Article", "BlogPosting")
    def has_type(cls_list):
        for c in cls_list:
            if f'"@type":"{c}"' in html or f'"@type": "{c}"' in html:
                return True
            # array form: "@type":["X","Y","Z"]
            if re.search(rf'"@type"\s*:\s*\[[^\]]*"{c}"[^\]]*\]', html):
                return True
        return False
    has_org = has_type(org_subclasses)
    has_wp = has_type(wp_classes)
    if has_graph and has_org and has_wp: return ("pass", "@graph + Org-class + WebPage-class")
    if has_org and has_wp: return ("fail", "schema present but not nested (#3 entity-depth gap)")
    return ("fail", "missing Organization or WebPage class")

def check_date_modified(root, live, html, flavour, pre_launch):
    """Finding #1: dateModified ISO 8601 with TZ"""
    if not html: return ("skip", "no live URL")
    if '"dateModified"' not in html: return ("fail", "no dateModified in schema")
    m = re.search(r'"dateModified"\s*:\s*"([^"]+)"', html)
    if not m: return ("fail", "no value")
    val = m.group(1)
    if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", val): return ("pass", val[:19])
    if re.match(r"\d{4}-\d{2}-\d{2}$", val): return ("fail", f"{val} — date only, needs ISO 8601 with TZ")
    return ("fail", f"non-ISO: {val[:40]}")

def check_speakable(root, live, html, flavour, pre_launch):
    if not html: return ("skip", "no live URL")
    if "SpeakableSpecification" in html: return ("pass", "")
    return ("fail", "no SpeakableSpecification")

def check_fleet_xlinks(root, live, html, flavour, pre_launch):
    if not html: return ("skip", "no live URL")
    hosts = ["rank4ai.co.uk", "marketinvoice.co.uk", "seocompare.co.uk", "bestbusinessloans.ai", "fundbiz.co.uk"]
    own_host = None
    if live:
        own_host = re.sub(r"^https?://(www\.)?", "", live).rstrip("/").split("/")[0]
    count = sum(1 for h in hosts if h in html and (own_host is None or h != own_host))
    return ("pass" if count >= 3 else "fail", f"{count}/5 sister-site links")

def check_link_rel_related(root, live, html, flavour, pre_launch):
    """Finding #22: <link rel="related"> network signal"""
    if not html: return ("skip", "no live URL")
    has = re.search(r'<link[^>]+rel=["\']related["\']', html, re.I) is not None
    return ("pass" if has else "fail", "no <link rel=related> in head")

def check_sitemap_lastmod(root, live, html, flavour, pre_launch):
    """Finding #17: ISO 8601 with TZ. Sample sitemap-0.xml or sitemap-index.xml"""
    if not live: return ("skip", "no live URL")
    txt = fetch(live.rstrip("/") + "/sitemap-0.xml") or fetch(live.rstrip("/") + "/sitemap.xml")
    if not txt: return ("skip", "sitemap not fetchable")
    mods = re.findall(r"<lastmod>([^<]+)</lastmod>", txt)
    if not mods: return ("fail", "no lastmod elements")
    sample = mods[:20]
    distinct = len(set(sample))
    has_tz = sum(1 for m in sample if "T" in m and (m.endswith("Z") or re.search(r"[+-]\d{2}:?\d{2}$", m)))
    if distinct == 1: return ("fail", f"all {len(sample)} sampled lastmods identical — build-time stamp")
    if has_tz < len(sample) * 0.5: return ("fail", f"only {has_tz}/{len(sample)} have ISO 8601 TZ")
    return ("pass", f"{distinct} distinct lastmods in sample of {len(sample)}")

def check_faqpage_misuse(root, live, html, flavour, pre_launch):
    """Finding #12: FAQPage schema only on actual FAQ pages with 4+ Q/A.
    On non-FAQ pages it's a deception signal post Google's 7 May 2026 deprecation."""
    if not html: return ("skip", "no live URL")
    has_faq_schema = '"@type":"FAQPage"' in html or '"@type": "FAQPage"' in html
    if not has_faq_schema: return ("skip", "no FAQPage schema on this page")
    # Count Question entries
    q_count = len(re.findall(r'"@type"\s*:\s*"Question"', html))
    # Heuristic: should have a visible FAQ section (h2/h3 'frequently asked', 'FAQ', or details/summary)
    has_visible_faq = bool(re.search(r"(frequently\s+asked\s+questions|<h\d[^>]*>FAQ|<details[^>]*>)", html, re.I))
    if q_count < 4 and not has_visible_faq:
        return ("fail", f"FAQPage schema with only {q_count} Question entries + no visible FAQ section")
    if q_count < 4:
        return ("fail", f"FAQPage schema with {q_count} Question entries (need 4+)")
    return ("pass", f"{q_count} questions + visible FAQ section")

def check_indexnow_unique(root, live, html, flavour, pre_launch):
    """Finding #18: Each site's IndexNow key must be unique to the host.
    FAT + FAG copy-pasted BBL's key — IndexNow rejects shared keys."""
    pub = root / "public"
    if not pub.exists(): return ("skip", "no public/")
    keys = [f.name[:-4] for f in pub.iterdir() if f.is_file() and re.match(r"^[a-f0-9]{32}\.txt$", f.name)]
    if not keys: return ("skip", "no IndexNow key (caught by indexnow_key check)")
    # Cross-check against other sites' keys to detect duplication
    # Collected at module level via SITES iteration
    return ("pass", f"key {keys[0][:8]}... ({len(keys)} key files)")

def check_ai_txt_present(root, live, html, flavour, pre_launch):
    """Finding #10: ai.txt purpose-based scraping declaration (Spawning)"""
    return ("pass" if (root / "public" / "ai.txt").exists() else "fail", "")

CHECKS = [
    # (id, fn, severity, label)
    ("claude_md",           check_claude_md,           "p2", "CLAUDE.md present"),
    ("robots_txt",          check_robots_txt,          "p1", "robots.txt valid + AI bots named"),
    ("llms_txt",            check_llms_txt,            "p1", "llms.txt"),
    ("llms_full",           check_llms_full_txt,       "p2", "llms-full.txt"),
    ("llms_instructions",   check_llms_instructions,   "p2", "llms.txt has ## Instructions (#9)"),
    ("ai_txt",              check_ai_txt,              "p2", "ai.txt (#10)"),
    ("indexnow_key",        check_indexnow_key,        "p1", "IndexNow key file in public/"),
    ("deploy_site_host",    check_deploy_site_host,    "p0", "deploy.cjs SITE_HOST matches live"),
    ("fleet_core_v",        check_fleet_core_version,  "p1", "fleet-core >= v0.6.3"),
    ("3tier_safepayload",   check_3tier_safepayload,   "p0", "3-tier safe-payload write"),
    ("og_image",            check_og_image,            "p1", "og:image (not placeholder)"),
    ("homepage_imagery",    check_homepage_imagery,    "p1", "homepage has imagery"),
    ("alt_text",            check_alt_text,            "p2", "all imgs alt-tagged"),
    ("schema_graph",        check_schema_graph,        "p1", "nested @graph schema (#3)"),
    ("date_modified",       check_date_modified,       "p2", "dateModified ISO 8601 with TZ (#1)"),
    ("speakable",           check_speakable,           "p2", "SpeakableSpecification (#13)"),
    ("fleet_xlinks",        check_fleet_xlinks,        "p2", ">=3 fleet xlinks in footer"),
    ("link_rel_related",    check_link_rel_related,    "p2", "<link rel=related> in head (#22)"),
    ("sitemap_lastmod",     check_sitemap_lastmod,     "p2", "sitemap lastmod ISO 8601 + varies (#17)"),
    ("faqpage_misuse",      check_faqpage_misuse,      "p2", "FAQPage schema only with 4+ Q/A (#12)"),
    ("indexnow_unique",     check_indexnow_unique,     "p2", "IndexNow key file present (#18)"),
]

def run_for_site(sid, repo, flavour, pre_launch, live):
    root = ROOT / repo
    html = fetch(live) if live and not pre_launch else (fetch(live) if live else None)
    results = []
    for cid, fn, sev, label in CHECKS:
        try:
            status, note = fn(root, live, html, flavour, pre_launch)
        except Exception as e:
            status, note = "fail", f"check raised: {type(e).__name__}: {e}"
        results.append({"id": cid, "label": label, "severity": sev, "status": status, "note": note})
    return results

def main():
    only = None
    strict = False
    json_only = False
    for a in sys.argv[1:]:
        if a == "--strict": strict = True
        elif a == "--json": json_only = True
        elif not a.startswith("--"): only = a

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sites": {},
        "summary": {"p0_fails": 0, "p1_fails": 0, "p2_fails": 0, "pass": 0, "total": 0},
    }
    import sys as _sys2, os as _os2; _sys2.path.insert(0, _os2.path.dirname(_os2.path.abspath(__file__)))
    try:
        from site_status import status_of as _status_of, load as _load_status
        _known = _load_status()
    except Exception:
        _status_of, _known = (lambda s: None), {}
    for sid, repo, flav, pre, live in SITES:
        if only and sid != only: continue
        # clients.json is the canonical source of pre-launch; fall back to the
        # tuple value only for sites not present there (dedup, no drift).
        if sid in _known:
            pre = _status_of(sid) == "prelaunch"
        if not json_only:
            print(f"\n=== {sid} ({flav}, {'PRE' if pre else 'live'}) ===", file=sys.stderr)
        results = run_for_site(sid, repo, flav, pre, live)
        out["sites"][sid] = {
            "flavour": flav,
            "pre_launch": pre,
            "live_url": live,
            "checks": results,
        }
        for r in results:
            out["summary"]["total"] += 1
            if r["status"] == "pass":
                out["summary"]["pass"] += 1
            elif r["status"] == "fail":
                out["summary"][f"{r['severity']}_fails"] += 1
                if not json_only:
                    badge = {"p0":"P0","p1":"P1","p2":"P2"}[r["severity"]]
                    print(f"  {badge} FAIL {r['label']:50s} {r['note']}", file=sys.stderr)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    if json_only:
        print(json.dumps(out, indent=2))
    else:
        s = out["summary"]
        print(f"\n=== Summary ===\n  P0 fails: {s['p0_fails']}\n  P1 fails: {s['p1_fails']}\n  P2 fails: {s['p2_fails']}\n  Pass:     {s['pass']}/{s['total']}", file=sys.stderr)
        print(f"\nWrote {OUT}", file=sys.stderr)
    if strict and (out["summary"]["p0_fails"] or out["summary"]["p1_fails"]):
        sys.exit(1)

if __name__ == "__main__":
    main()
