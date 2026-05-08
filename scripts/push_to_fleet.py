#!/usr/bin/env python3
"""
push_to_fleet.py

Read every section of dashboard live data and emit a per-site Markdown
DAILY_BRIEF.md so each fleet site's Claude session sees the full
picture (not just the Actions list).

Two write targets per site:
  1. iCloud archive: FLEET/daily/<DATE>/<SITE>.md  (history)
  2. Site repo root: <repo>/DAILY_BRIEF.md          (overwritten daily)

Also prepends a one-line index entry per site to FLEET/INBOX.md.

Skips a site if the brief is unchanged vs yesterday (avoids no-op commits
+ noisy CF Pages rebuilds).

Hooked from refresh_all.py after compute_wins.py.
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ---------- config ----------

PROJECT_DIR = Path(__file__).resolve().parent.parent
LIVE = PROJECT_DIR / "src" / "data" / "live"
SNAPSHOTS = LIVE / "rec_snapshots"

ICLOUD_FLEET = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/claude/astro/FLEET"
INBOX = ICLOUD_FLEET / "INBOX.md"

# site_id -> (display, repo_path, domain)
# Pre-launch leadgen sites are gated by clients.json `pre_launch: true` —
# brief generation is skipped for those until they go live (no point pushing
# DAILY_BRIEF.md to a noindex site). Once the flag flips to false the brief
# starts flowing automatically.
SITES = {
    "rank4ai":           ("R4",  Path.home() / "rank4ai-site",            "rank4ai.co.uk"),
    "market-invoice":    ("MI",  Path.home() / "compare-invoice-finance", "marketinvoice.co.uk"),
    "seocompare":        ("SC",  Path.home() / "compareaiseo",            "seocompare.co.uk"),
    "bestbusinessloans": ("BBL", Path.home() / "bestbusinessloans",       "bestbusinessloans.co.uk"),
    "fundbiz":           ("FB",  Path.home() / "fundbiz",                 "fundbiz.co.uk"),
    "cardmachines":      ("CT",  Path.home() / "cardmachines",            "cardmachines.co.uk"),
}


def _load_pre_launch_set():
    """Return a set of slugs flagged pre_launch:true in clients.json so
    push_to_fleet.py skips them until the flag flips."""
    try:
        with open(PROJECT_DIR / "src" / "data" / "clients.json") as f:
            data = json.load(f)
        clients = data if isinstance(data, list) else data.get("clients", [])
        return {c.get("slug") or c.get("id") for c in clients if c.get("pre_launch")}
    except Exception:
        return set()


PRE_LAUNCH = _load_pre_launch_set()

SECTION_CAP = 5           # most sections cap at top-N
STALE_DAYS = 2            # warn if a source file is older than this

TODAY = datetime.now().date()


# ---------- helpers ----------

def load_json(name):
    p = LIVE / name
    if not p.exists():
        return None, None
    try:
        with open(p) as f:
            return json.load(f), datetime.fromtimestamp(p.stat().st_mtime).date()
    except Exception:
        return None, None


def staleness_note(mtime_date, label):
    if mtime_date is None:
        return f"_{label}: source missing_"
    age = (TODAY - mtime_date).days
    if age > STALE_DAYS:
        return f"_{label}: data is {age} days old_"
    return None


def cap(lst, n=SECTION_CAP):
    return (lst or [])[:n]


def md_table(headers, rows):
    if not rows:
        return "_(none)_"
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join(["---"] * len(headers)) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


# ---------- section builders ----------

def section_actions(site_id, recs_data, recs_mtime):
    if not recs_data:
        return "_no recommendations file_", []
    site = recs_data.get(site_id, {}) if isinstance(recs_data, dict) else {}
    recs = site.get("recommendations", [])
    counts = {k: site.get(k, 0) for k in ["critical", "high", "medium", "low"]}

    # priority order
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    recs_sorted = sorted(recs, key=lambda r: order.get(r.get("priority"), 9))
    top = cap(recs_sorted)

    lines = [f"**Counts:** critical={counts['critical']} · high={counts['high']} · medium={counts['medium']} · low={counts['low']}", ""]
    for i, r in enumerate(top, 1):
        prio = (r.get("priority") or "?").upper()
        cat = r.get("category", "")
        title = r.get("title", "(untitled)")
        detail = (r.get("detail", "") or "").strip().replace("\n", " ")
        if len(detail) > 320:
            detail = detail[:317] + "..."
        lines.append(f"{i}. **[{prio}] {title}** ({cat})")
        if detail:
            lines.append(f"   {detail}")
    note = staleness_note(recs_mtime, "Actions")
    if note:
        lines.insert(0, note)
        lines.insert(1, "")
    return "\n".join(lines), top


def section_zero_click(site_id, gsc_data, gsc_mtime):
    """Page-1 queries with high impressions but zero clicks (CTR fix targets)."""
    if not gsc_data:
        return "_no GSC data_"
    site = gsc_data.get(site_id, {})
    queries = site.get("top_queries", []) or []
    # page-1 = position <= 10, with impressions >= 20 and clicks == 0
    targets = [q for q in queries if q.get("position", 99) <= 10 and q.get("impressions", 0) >= 20 and q.get("clicks", 0) == 0]
    targets.sort(key=lambda q: -q.get("impressions", 0))
    rows = [(q["query"], q["impressions"], f"{q['position']:.1f}") for q in cap(targets)]
    note = staleness_note(gsc_mtime, "GSC")
    body = md_table(["Query", "Impressions", "Avg pos"], rows)
    return (note + "\n\n" if note else "") + body


def section_climbers(site_id, gsc_data, gsc_prev_data):
    """Queries that moved up notably vs yesterday (page-2 → page-1 candidates)."""
    if not gsc_data or not gsc_prev_data:
        return "_no diff source available_"
    today_q = {q["query"]: q for q in gsc_data.get(site_id, {}).get("top_queries", []) or []}
    prev_q = {q["query"]: q for q in gsc_prev_data.get(site_id, {}).get("top_queries", []) or []}
    movers = []
    for query, t in today_q.items():
        p = prev_q.get(query)
        if not p:
            continue
        delta = p.get("position", 99) - t.get("position", 99)  # positive = improved
        if delta >= 1.0 and t.get("impressions", 0) >= 10:
            movers.append({
                "query": query,
                "from": p.get("position"),
                "to": t.get("position"),
                "delta": delta,
                "imp": t.get("impressions"),
            })
    movers.sort(key=lambda m: -m["delta"])
    rows = [(m["query"], f"{m['from']:.1f}", f"{m['to']:.1f}", f"+{m['delta']:.1f}", m["imp"]) for m in cap(movers)]
    return md_table(["Query", "From", "To", "Δ", "Imp"], rows)


def section_serp(site_id, serp_data, serp_mtime):
    """SERP positions tracked daily by DataForSEO. Show queries where we're not ranked + top 3 competitors."""
    if not serp_data:
        return "_no SERP data_"
    site = serp_data.get(site_id, {})
    results = site.get("results", []) or []
    rows = []
    for r in results:
        q = r.get("query", "")
        organic = r.get("organic", []) or []
        domain = SITES[site_id][2]
        our_pos = next((o.get("position") for o in organic if domain in (o.get("domain") or "")), None)
        ai_o = "Yes" if r.get("has_ai_overview") else "No"
        top3 = ", ".join((o.get("domain") or "").replace("www.", "") for o in organic[:3])
        pos_str = str(our_pos) if our_pos else "—"
        rows.append((q, pos_str, ai_o, top3))
    rows = rows[:SECTION_CAP * 2]  # SERP is the headline section, allow more
    note = staleness_note(serp_mtime, "SERP")
    body = md_table(["Query", "Our pos", "AI Overview", "Top 3"], rows)
    return (note + "\n\n" if note else "") + body


def section_ai_citations(site_id, citations_data, citations_mtime):
    """AI Search citation gaps — queries where competitors are cited but we're not."""
    if not citations_data:
        return "_no AI citation data_"
    site = citations_data.get(site_id, {})
    by_type = site.get("by_type", {}) or {}
    lines = [f"**Overall cited rate:** {site.get('overall_rate', 0):.1f}% ({site.get('total_cited', 0)}/{site.get('total_queries', 0)} queries)", ""]
    gaps = []
    for type_name, type_data in by_type.items():
        if type_name == "brand":
            continue
        for r in type_data.get("results", []) or []:
            if not r.get("brand_mentioned"):
                comps = r.get("competitors_mentioned", []) or []
                gaps.append({
                    "type": type_name,
                    "query": r.get("query"),
                    "competitors": comps,
                })
    rows = [(g["query"], g["type"], ", ".join(g["competitors"]) or "—") for g in cap(gaps, 8)]
    body = md_table(["Query", "Type", "Competitors cited"], rows)
    note = staleness_note(citations_mtime, "AI citations")
    return (note + "\n\n" if note else "") + "\n".join(lines) + "\n" + body


def section_competitors(site_id, comp_data):
    if not comp_data:
        return "_no competitor data_"
    site = comp_data.get(site_id, {})
    comps = site.get("competitors", []) or []
    comps.sort(key=lambda c: -(c.get("visibility_pct") or 0))
    rows = [(c["domain"], f"{(c.get('visibility_pct') or 0):.0f}%", f"{(c.get('avg_position') or 0):.1f}", c.get("appearances", 0)) for c in cap(comps)]
    our_vis = site.get("client_visibility_pct") or 0
    our_pos = site.get("client_avg_position") or 0
    header = f"**Our visibility:** {our_vis:.0f}% (avg pos {our_pos:.1f}) across {site.get('total_queries', 0)} tracked queries"
    return header + "\n\n" + md_table(["Competitor", "Visibility", "Avg pos", "Wins"], rows)


def section_audit(site_id, audit_mtime):
    """Per-site daily audit issues."""
    audit_data, _ = load_json(f"daily_audit_{site_id}.json")
    if not audit_data:
        return "_no audit data_"
    issues = audit_data.get("issues_total", 0)
    pages = audit_data.get("pages_with_issues", 0)
    flagged = audit_data.get("flagged_pages", []) or []
    note = staleness_note(audit_mtime, "Audit")
    if issues == 0:
        body = "All clean."
    else:
        rows = [(f.get("url", "?"), ", ".join(f.get("issues", []) or [])) for f in cap(flagged)]
        body = f"**{issues} issues across {pages} pages**\n\n" + md_table(["URL", "Issues"], rows)
    return (note + "\n\n" if note else "") + body


def section_trends(site_id, trends_data, trends_mtime):
    if not trends_data:
        return "_no trends data_"
    site = trends_data.get(site_id, {})
    direction = site.get("brand_direction", "?")
    avg = site.get("brand_avg", 0)
    current = site.get("brand_current", 0)
    # brand_related/keyword_related are dicts: {"rising": [...], "top": [...]}
    def names(group):
        if not isinstance(group, dict):
            return []
        items = (group.get("rising") or []) + (group.get("top") or [])
        return [i if isinstance(i, str) else i.get("query") or i.get("topic") or "" for i in items if i]

    related = names(site.get("brand_related"))
    kw_related = names(site.get("keyword_related"))
    note = staleness_note(trends_mtime, "Trends")
    lines = [
        f"**Brand interest:** current={current} · avg={avg:.1f} · trend={direction}",
        "",
    ]
    if related:
        lines.append("**Rising brand-related queries:** " + ", ".join(related[:6]))
    if kw_related:
        lines.append("**Rising keyword-related queries:** " + ", ".join(kw_related[:6]))
    return (note + "\n\n" if note else "") + "\n".join(lines)


def section_content_plans(site_id):
    plan_data, mtime = load_json(f"content_plan_{site_id}.json")
    if not plan_data:
        return "_no content plan_"
    plans = plan_data.get("plans", []) or []
    note = staleness_note(mtime, "Content plans")
    rows = [(p.get("title", "?"), p.get("filename", ""), f"{(p.get('size_bytes') or 0) / 1024:.1f} KB") for p in cap(plans, 8)]
    body = md_table(["Title", "File", "Size"], rows)
    return (note + "\n\n" if note else "") + body


def section_wins(site_id):
    """Diff today's recommendations vs yesterday's snapshot — what was resolved?"""
    today_path = SNAPSHOTS / f"recommendations_{TODAY}.json"
    yest_path = SNAPSHOTS / f"recommendations_{TODAY - timedelta(days=1)}.json"
    if not today_path.exists() or not yest_path.exists():
        return "_no snapshot diff available_"
    try:
        with open(today_path) as f:
            today = json.load(f)
        with open(yest_path) as f:
            yest = json.load(f)
    except Exception:
        return "_snapshot read error_"

    def keys(snap):
        site = snap.get(site_id, {}) if isinstance(snap, dict) else {}
        return {(r.get("title", ""), r.get("category", "")) for r in site.get("recommendations", []) or []}

    resolved = keys(yest) - keys(today)
    new = keys(today) - keys(yest)
    lines = [f"**Resolved since yesterday:** {len(resolved)} · **New today:** {len(new)}"]
    if resolved:
        lines.append("")
        lines.append("**Resolved:**")
        for t, c in list(resolved)[:5]:
            lines.append(f"- {t} ({c})")
    if new:
        lines.append("")
        lines.append("**New:**")
        for t, c in list(new)[:5]:
            lines.append(f"- {t} ({c})")
    return "\n".join(lines)


# ---------- v2 sections (added 2026-05-04) ----------

def section_aeo(site_id, aeo_data, aeo_mtime):
    """Top scoring gaps from the AEO scorecard."""
    if not aeo_data:
        return "_no AEO scorecard_"
    site = aeo_data.get(site_id, {})
    if not site:
        return "_no AEO data for this site_"
    note = staleness_note(aeo_mtime, "AEO scorecard")
    pct = site.get("percentage", 0)
    total = site.get("total_score", 0)
    max_s = site.get("max_score", 0)
    layers = site.get("layers", {}) or {}
    # Layers below max — sorted by gap (max - score) descending
    gaps = []
    for layer_name, payload in layers.items():
        score = payload.get("score", 0)
        layer_max = payload.get("max", 0)
        if score < layer_max:
            gap = layer_max - score
            gaps.append((layer_name, score, layer_max, gap, payload.get("notes", []) or []))
    gaps.sort(key=lambda x: -x[3])
    lines = [f"**Overall AEO score:** {total}/{max_s} ({pct}%)"]
    if gaps:
        lines.append("")
        lines.append("**Layers with gaps (largest first):**")
        for name, score, mx, gap, notes in gaps[:5]:
            lines.append(f"- **{name}**: {score}/{mx} (gap {gap})")
            for n in notes[:2]:
                lines.append(f"  - {n}")
    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_manual_indexing(site_id, miq_data, miq_mtime):
    """Top URLs to paste into GSC URL Inspection."""
    if not miq_data:
        return "_no manual indexing queue_"
    site = (miq_data.get("per_site") or {}).get(site_id, {})
    if not site:
        return "_no queue for this site_"
    note = staleness_note(miq_mtime, "Manual indexing queue")
    never = site.get("never_api_submitted", 0)
    sitemap = site.get("sitemap_url_count", 0)
    inspect = site.get("gsc_inspect_url", "")
    top = (site.get("top") or [])[:5]
    lines = [
        f"**Never-API-submitted:** {never} of {sitemap} sitemap URLs",
        f"**GSC inspect URL:** {inspect}" if inspect else "",
        "",
        "**Top 5 URLs to paste into URL Inspection:**",
    ]
    for i, item in enumerate(top, 1):
        url = item.get("url", "?") if isinstance(item, dict) else str(item)
        score = item.get("score") if isinstance(item, dict) else None
        line = f"{i}. {url}"
        if score is not None:
            line += f" (score {score})"
        lines.append(line)
    body = "\n".join([l for l in lines if l != ""])
    return (note + "\n\n" if note else "") + body


def section_bot_activity(site_id, bot_data, bot_mtime):
    """7-day rolling AI/search bot hits per platform."""
    if not bot_data:
        return "_no bot data_"
    site = bot_data.get(site_id, {})
    days = site.get("days", []) or []
    if not days:
        return "_no recent bot hits recorded_"
    note = staleness_note(bot_mtime, "Bot hits")
    # Last 7 days
    recent = days[-7:] if len(days) > 7 else days
    by_name_total = {}
    total = 0
    for d in recent:
        bn = d.get("by_name", {}) or {}
        for name, count in bn.items():
            by_name_total[name] = by_name_total.get(name, 0) + count
            total += count
    top_bots = sorted(by_name_total.items(), key=lambda x: -x[1])[:8]
    lines = [f"**7-day total:** {total} hits across {len(recent)} day(s)"]
    if top_bots:
        lines.append("")
        rows = [(name, count) for name, count in top_bots]
        lines.append(md_table(["Bot", "Hits"], rows))
    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_pagespeed(site_id, ps_data, ps_mtime):
    """Mobile perf + CLS callouts for the homepage."""
    if not ps_data:
        return "_no PageSpeed data_"
    site = ps_data.get(site_id, {})
    if not site:
        return "_no PageSpeed for this site_"
    note = staleness_note(ps_mtime, "PageSpeed")
    avg = site.get("avg_scores", {}) or {}
    pages = site.get("pages", []) or []
    lines = [
        f"**Avg scores (mobile):** perf={avg.get('performance', '?')} · a11y={avg.get('accessibility', '?')} · seo={avg.get('seo', '?')} · best-practices={avg.get('best-practices', '?')}"
    ]
    cls_flags = []
    for p in pages[:5]:
        cwv = p.get("cwv", {}) or p.get("metrics", {}) or {}
        cls = cwv.get("cls") or cwv.get("CLS")
        if cls is not None:
            try:
                if float(cls) > 0.1:
                    cls_flags.append((p.get("url", "?"), cls))
            except Exception:
                pass
    if cls_flags:
        lines.append("")
        lines.append("**CLS warnings (>0.1):**")
        for url, cls in cls_flags[:3]:
            lines.append(f"- {url} → CLS {cls}")
    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_entity_status(site_id, kg_data, kg_mtime):
    """Wikidata/KG lookup result. Surfaces TASKS #16 blocker visibility."""
    if not kg_data:
        return "_no entity status data_"
    site = kg_data.get(site_id, {})
    if not site:
        return "_no entity check for this site_"
    note = staleness_note(kg_mtime, "Entity status")
    is_known = site.get("is_known_entity", False)
    best = site.get("best_match")
    queries = site.get("queries", []) or []
    lines = [f"**Known to Google Knowledge Graph:** {'✅ Yes' if is_known else '❌ No'}"]
    if best:
        lines.append(f"**Best match:** {best.get('name', '?')} (score {best.get('score', '?')})")
    error_count = sum(1 for q in queries if q.get("error"))
    if error_count:
        lines.append(f"**KG API errors:** {error_count} of {len(queries)} probes (likely rate limit)")
    if not is_known:
        lines.append("")
        lines.append("**Action:** Wikidata + Wikipedia stub authorship (TASKS #16 / #102) — single biggest unblocker for AI citation rate.")
    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_drift(site_id, drift_data, drift_mtime):
    """Pages where dashboard-tracked facts (BoE rate, founder, entity) drifted."""
    if not drift_data:
        return "_no drift report_"
    site = (drift_data.get("per_site") or {}).get(site_id, {})
    if not site:
        return "_no drift data for this site_"
    note = staleness_note(drift_mtime, "Drift")
    drift_count = site.get("drift_count", 0)
    pages = site.get("pages_scanned", 0)
    findings = site.get("findings") or []
    lines = [f"**Drift count:** {drift_count} of {len(findings)} assertions across {pages} pages"]
    drifted = [f for f in findings if f.get("drift_detected")]
    weak = [f for f in findings if not f.get("drift_detected") and f.get("coverage_pct", 100) < 80 and f.get("missing_pages")]
    if drifted:
        lines.append("")
        lines.append("**⚠ Drift detected:**")
        for f in drifted[:5]:
            lines.append(f"- **{f.get('label')}** expected `{f.get('expected')}` — {f.get('coverage_pct', 0):.0f}% coverage")
            for url in (f.get("missing_pages") or [])[:3]:
                lines.append(f"  - missing on {url}")
    if weak:
        lines.append("")
        lines.append("**Coverage gaps (no drift, but assertion missing on some pages):**")
        for f in weak[:3]:
            lines.append(f"- **{f.get('label')}** ({f.get('coverage_pct', 0):.0f}%) — {f.get('expected')}")
            for url in (f.get("missing_pages") or [])[:2]:
                lines.append(f"  - {url}")
    if not drifted and not weak:
        lines.append("All tracked assertions hold.")
    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_content_freshness(site_id, cf_data, cf_mtime):
    """Stale pages and refresh pile."""
    if not cf_data:
        return "_no content freshness data_"
    site = cf_data.get(site_id, {})
    if not site:
        return "_no freshness for this site_"
    note = staleness_note(cf_mtime, "Content freshness")
    total = site.get("total_pages", 0)
    dated = site.get("with_dates", 0)
    fresh_30 = site.get("fresh_30d", 0)
    stale = site.get("stale_12mo", 0)
    median = site.get("median_age_days", 0)
    lines = [
        f"**{dated}/{total} pages dated** · fresh ≤30d: {fresh_30} · stale >12mo: {stale} · median age: {median}d"
    ]
    refresh = site.get("refresh_pile") or site.get("oldest_pages") or []
    if refresh:
        lines.append("")
        lines.append("**Top 5 oldest dated pages (refresh candidates):**")
        for p in refresh[:5]:
            url = p.get("url") or p.get("path", "?")
            age = p.get("age_days", "?")
            lm = p.get("last_modified", "?")
            wc = p.get("word_count", "?")
            lines.append(f"- {url} — {age}d old (last_modified {lm}, {wc} words)")
    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_entity_coherence(site_id, ec_data, ec_mtime):
    """sameAs link health — broken / bot-blocked profile URLs."""
    if not ec_data:
        return "_no entity coherence data_"
    site = ec_data.get(site_id, {})
    if not site:
        return "_no coherence for this site_"
    note = staleness_note(ec_mtime, "Entity coherence")
    summ = site.get("summary") or {}
    total = summ.get("total", 0)
    ok = summ.get("ok", 0)
    broken = summ.get("broken", 0)
    blocked = summ.get("bot_blocked", 0)
    score = summ.get("score", 0)
    lines = [
        f"**sameAs health:** {ok}/{total} OK ({score}%) · broken: {broken} · bot-blocked (informational): {blocked}"
    ]
    bd = site.get("broken_detail") or []
    if bd:
        lines.append("")
        lines.append("**Broken sameAs links:**")
        for b in bd[:5]:
            url = b.get("url", "?") if isinstance(b, dict) else str(b)
            ent = b.get("entity_name", "?") if isinstance(b, dict) else ""
            err = b.get("error", "?") if isinstance(b, dict) else ""
            lines.append(f"- {ent}: {url} — {err}")
    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_llms_validation(site_id, lv_data, lv_mtime):
    """llms.txt validator score + missing checks."""
    if not lv_data:
        return "_no llms.txt validation_"
    site = lv_data.get(site_id, {})
    if not site:
        return "_no validation for this site_"
    note = staleness_note(lv_mtime, "llms.txt validation")
    txt = site.get("llms_txt") or {}
    full = site.get("llms_full_txt") or {}
    accessible = txt.get("accessible", False)
    score = txt.get("score", 0)
    missing = txt.get("missing") or []
    lines = [
        f"**llms.txt:** {'✅ accessible' if accessible else '❌ inaccessible'} · score {score}/100"
    ]
    if isinstance(full, dict) and full.get("accessible") is not None:
        lines.append(f"**llms-full.txt:** {'✅ accessible' if full.get('accessible') else '❌ missing'}")
    if missing:
        lines.append("")
        lines.append("**Failed checks:**")
        for m in missing[:6]:
            lines.append(f"- {m}")
    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_ai_overview(site_id, ao_data, ao_mtime):
    """AI Overview triggers and our citation status."""
    if not ao_data:
        return "_no AI Overview data_"
    site = ao_data.get(site_id, {})
    if not site:
        return "_no AIO data for this site_"
    note = staleness_note(ao_mtime, "AI Overview")
    total = site.get("total_queries", 0)
    detected = site.get("ai_overviews_detected", 0)
    if detected == 0:
        return (note + "\n\n" if note else "") + f"_AI Overviews not detected on any of {total} tracked queries (UK B2B niche pattern, not a bug)._"
    domain = SITES[site_id][2]
    results = site.get("results") or []
    cited_in = []
    not_cited_in = []
    for r in results:
        if not r.get("has_ai_overview"):
            continue
        ao = r.get("ai_overview") or {}
        sources = ao.get("sources") or ao.get("references") or []
        cited = any(domain in (s.get("domain") or s.get("url") or "") for s in sources if isinstance(s, dict))
        target = cited_in if cited else not_cited_in
        target.append(r.get("query"))
    lines = [f"**{detected}/{total} queries trigger AI Overviews** · we're cited in {len(cited_in)}, missed on {len(not_cited_in)}"]
    if not_cited_in:
        lines.append("")
        lines.append("**Top missed AIO queries (citation opportunity):**")
        for q in not_cited_in[:5]:
            lines.append(f"- {q}")
    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_bing_queries(site_id, bing_data, bing_mtime):
    """Top Bing-specific queries (different intent surface vs Google)."""
    if not bing_data:
        return "_no Bing data_"
    site = bing_data.get(site_id, {})
    if not site:
        return "_no Bing for this site_"
    note = staleness_note(bing_mtime, "Bing")
    queries = site.get("top_queries") or []
    if not queries:
        return (note + "\n\n" if note else "") + "_Bing data not populated (low-authority site, ~0 impressions — expected, not a bug)._"
    queries_sorted = sorted(queries, key=lambda q: -(q.get("Impressions", 0) or 0))
    rows = []
    for q in queries_sorted[:SECTION_CAP]:
        rows.append((
            q.get("Query", "?"),
            q.get("Impressions", 0),
            q.get("Clicks", 0),
            q.get("AvgImpressionPosition", "?"),
        ))
    body = md_table(["Query", "Imp", "Clicks", "Avg pos"], rows)
    return (note + "\n\n" if note else "") + body


def section_new_pages(site_id, np_data, np_mtime):
    """Recently shipped — count + breakdown by category."""
    if not np_data:
        return "_no new-pages data_"
    site = np_data.get(site_id, {})
    if not site:
        return "_no new pages tracked_"
    note = staleness_note(np_mtime, "New pages")
    count = site.get("new_pages_count", 0)
    bc = site.get("by_category") or {}
    lines = [f"**Total new vs baseline:** {count} pages"]
    if bc:
        rows = sorted([(k, v.get("count", 0) if isinstance(v, dict) else v) for k, v in bc.items()], key=lambda x: -x[1])
        lines.append("")
        lines.append(md_table(["Category", "Count"], rows[:8]))
    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_gsc_drilldown(site_id, gd_data, gd_mtime):
    """GSC Coverage Drilldown XLSX exports — actionable issue breakdown."""
    if not gd_data:
        return "_no GSC drilldown imports — export from Search Console → Indexing → Pages → Why pages aren't indexed → click an issue → Export, then run scripts/ingest_gsc_drilldown.py_"
    site = gd_data.get(site_id, {})
    if not site or not site.get("issues"):
        return "_no GSC drilldown for this site — export from Search Console_"
    note = staleness_note(gd_mtime, "GSC drilldown")
    issues = site.get("issues") or {}

    # Classify: actionable vs intentional
    ACTION_REQUIRED = {"Not found (404)", "Soft 404", "Duplicate without user-selected canonical", "Blocked due to other 4xx issue", "Server errors (5xx)"}
    CONTENT_GATE = {"Crawled - currently not indexed", "Discovered - currently not indexed"}
    INTENTIONAL = {"Excluded by ‘noindex’ tag", "Excluded by 'noindex' tag", "Page with redirect", "Alternate page with proper canonical tag"}

    action_total = sum(d["url_count"] for k, d in issues.items() if k in ACTION_REQUIRED)
    content_total = sum(d["url_count"] for k, d in issues.items() if k in CONTENT_GATE)
    intentional_total = sum(d["url_count"] for k, d in issues.items() if k in INTENTIONAL)

    lines = [
        f"**{action_total} URLs need a fix · {content_total} URLs blocked by content quality · {intentional_total} URLs intentionally excluded**",
    ]

    # Issue table
    rows = []
    for label, d in sorted(issues.items(), key=lambda x: -x[1]["url_count"]):
        bucket = "fix" if label in ACTION_REQUIRED else ("content" if label in CONTENT_GATE else "intentional")
        rows.append((label, d["url_count"], d["exported_at"], bucket))
    lines.append("")
    lines.append(md_table(["Issue", "URLs", "Last export", "Bucket"], rows))

    # Surface actionable URLs explicitly
    for label in ["Not found (404)", "Soft 404", "Duplicate without user-selected canonical", "Blocked due to other 4xx issue"]:
        d = issues.get(label)
        if not d:
            continue
        urls = d.get("urls") or []
        if not urls:
            continue
        lines.append("")
        lines.append(f"**🔴 {label} ({len(urls)}) — fix or redirect:**")
        for u in urls[:15]:
            url = u.get("url") if isinstance(u, dict) else u
            last = u.get("last_crawled", "?") if isinstance(u, dict) else "?"
            lines.append(f"- {url} _(last crawled {last})_")
        if len(urls) > 15:
            lines.append(f"  …and {len(urls) - 15} more")

    # Top "Discovered not indexed" — these are the priority Request-Indexing candidates
    d = issues.get("Discovered - currently not indexed") or issues.get("Discovered – currently not indexed")
    if d and d.get("urls"):
        urls = d["urls"]
        lines.append("")
        lines.append(f"**📌 'Discovered – currently not indexed' ({len(urls)}) — top 10 to Request Indexing manually:**")
        for u in urls[:10]:
            url = u.get("url") if isinstance(u, dict) else u
            lines.append(f"- {url}")

    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_indexing_status(site_id, is_data, is_mtime):
    """Google's URL Inspection API view: indexed / not-indexed / 404 / redirect / blocked."""
    if not is_data:
        return "_no GSC URL Inspection data — run scripts/fetch_url_inspection.py_"
    site = (is_data.get("per_site") or {}).get(site_id, {})
    if not site:
        return "_no inspection data for this site_"
    if site.get("error"):
        return f"_inspection failed: {site['error']}_"
    note = staleness_note(is_mtime, "URL Inspection")
    indexed = site.get("indexed_count", 0)
    not_idx = site.get("not_indexed_count", 0)
    unknown = site.get("unknown_to_google_count", 0)
    broken = site.get("broken_404_count", 0)
    redirects = site.get("redirects_count", 0)
    blocked = site.get("blocked_count", 0)
    inspected = site.get("total_inspected", 0)
    in_sitemap = site.get("total_in_sitemap", 0)
    sample = site.get("sample_capped", False)
    rate = round(indexed / inspected * 100, 1) if inspected else 0
    lines = [
        f"**Inspected {inspected}/{in_sitemap} sitemap URLs** {'(capped at daily quota — full coverage in 1-2 days)' if sample else ''}",
        f"**Index rate:** {indexed} indexed ({rate}%) · {not_idx} not indexed · **{unknown} unknown to Google** · {broken} 404 · {redirects} redirects · {blocked} blocked",
    ]
    if unknown:
        lines.append("")
        lines.append(f"**🚨 {unknown} URLs Google has NEVER seen** — these are in your sitemap but Google has no record of them. Discovery problem, not indexing problem. Top 10 to manually request indexing for:")
        for u in (site.get("unknown_urls") or [])[:10]:
            lines.append(f"- {u}")
        if unknown > 10:
            lines.append(f"  …and {unknown - 10} more unknown")
    by_state = site.get("by_coverage_state") or {}
    if by_state:
        lines.append("")
        lines.append("**Coverage state breakdown:**")
        for state, count in sorted(by_state.items(), key=lambda x: -x[1]):
            lines.append(f"- {state}: {count}")
    broken_urls = site.get("broken_404_urls") or []
    if broken_urls:
        lines.append("")
        lines.append(f"**🔴 Broken (404) URLs Google has on file ({len(broken_urls)}):**")
        for u in broken_urls[:10]:
            lines.append(f"- {u}")
        if len(broken_urls) > 10:
            lines.append(f"  …and {len(broken_urls) - 10} more")
    not_idx_urls = site.get("not_indexed_urls") or []
    if not_idx_urls:
        lines.append("")
        lines.append("**Not-indexed URLs (top 10 — paste into URL Inspection → Request Indexing):**")
        for item in not_idx_urls[:10]:
            url = item.get("url", "?") if isinstance(item, dict) else item
            state = item.get("state", "") if isinstance(item, dict) else ""
            lines.append(f"- {url} _({state})_")
    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_indexing_health(site_id, ih_data, ih_mtime):
    """Per-URL ground-truth indexing rollup (today + 7d) + GSC coverage if available."""
    if not ih_data:
        return "_no indexing health data_"
    site = (ih_data.get("per_site") or {}).get(site_id, {})
    if not site:
        return "_no indexing health for this site_"
    note = staleness_note(ih_mtime, "Indexing health")
    today = site.get("today") or {}
    last_7d = site.get("last_7d") or {}
    status = site.get("status", "?")
    flag = {"healthy": "✅", "warning": "⚠", "error": "❌"}.get(status, "?")
    today_rate = today.get("success_rate")
    rate_str = f"{today_rate}%" if today_rate is not None else "—"
    lines = [
        f"**API submissions today:** {today.get('ok', 0)}/{today.get('submitted', 0)} returned 200 · 7d {last_7d.get('ok', 0)}/{last_7d.get('submitted', 0)}",
        "_⚠ Caveat: Indexing API publish() returning 200 does NOT mean Google indexed the page. The API is officially restricted to JobPosting + BroadcastEvent schema. For other URLs the call is accepted but `urlNotifications.getMetadata` returns 404, suggesting Google does not preserve the request. Treat this as a weak free signal, not a guaranteed indexing trigger. Real indexing status is in the URL Inspection section above._"
    ]
    for reason in (site.get("status_reasons") or []):
        lines.append(f"- ⚠ {reason}")
    cov = site.get("gsc_coverage")
    if cov:
        idx = cov.get("indexed", 0)
        nidx = cov.get("not_indexed", 0)
        rate = cov.get("index_rate", 0)
        lines.append("")
        lines.append(f"**GSC coverage:** {idx} indexed / {nidx} not indexed ({rate}% index rate)")
        issues = cov.get("issues") or {}
        if issues:
            top_issues = sorted(issues.items(), key=lambda x: -x[1])[:3]
            for itype, count in top_issues:
                lines.append(f"  - {itype}: {count}")
    else:
        lines.append("")
        lines.append("_GSC coverage data not available (needs manual XLSX export from Search Console — only present for R4 today)._")
    last_sub = site.get("last_submission_at")
    if last_sub:
        lines.append(f"\n**Last submission:** {last_sub}")
    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_thin_pages_broken(site_id):
    """Per-page thin (<300 words) + broken (status>=400) + orphan + issue counts from crawl_<site>.json."""
    crawl, mtime = load_json(f"crawl_{site_id}.json")
    if not crawl:
        return "_no crawl data_"
    note = staleness_note(mtime, "Crawl")
    pages = crawl.get("pages") or []
    issues = crawl.get("issues") or []
    orphans = crawl.get("orphans") or []
    thin = [p for p in pages if 0 < (p.get("word_count") or 0) < 300]
    broken = [p for p in pages if (p.get("status") or 200) >= 400]
    issue_types = {}
    for i in issues:
        t = i.get("type", "?")
        issue_types[t] = issue_types.get(t, 0) + 1
    issue_summary = " · ".join(f"{t}: {n}" for t, n in sorted(issue_types.items(), key=lambda x: -x[1])[:5])
    lines = [
        f"**Crawl:** {len(pages)} pages · {len(issues)} issues · {len(thin)} thin (<300w) · {len(broken)} broken (status≥400) · {len(orphans)} orphans"
    ]
    if issue_summary:
        lines.append(f"**Issue types:** {issue_summary}")
    if thin:
        lines.append("")
        lines.append("**Thinnest 5 pages (refresh or merge):**")
        for p in sorted(thin, key=lambda x: x.get("word_count") or 0)[:5]:
            lines.append(f"- {p.get('url','?')} — {p.get('word_count',0)} words")
    if broken:
        lines.append("")
        lines.append("**Broken pages (status≥400):**")
        for p in broken[:5]:
            lines.append(f"- {p.get('url','?')} — status {p.get('status')}")
    if orphans:
        lines.append("")
        lines.append(f"**Orphans:** {len(orphans)} page(s) with no inbound internal links")
        for o in orphans[:3]:
            url = o.get("url", "?") if isinstance(o, dict) else str(o)
            lines.append(f"- {url}")
    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_ga4_traffic(site_id, ga4_data, ga4_mtime):
    """Traffic overview + top sources from GA4."""
    if not ga4_data:
        return "_no GA4 data_"
    site = ga4_data.get(site_id, {})
    if not site:
        return "_no GA4 for this site_"
    note = staleness_note(ga4_mtime, "GA4")
    overview = site.get("overview") or {}
    sources = site.get("sources") or []
    top_pages = site.get("top_pages") or []
    period = site.get("period") or "?"
    lines = [
        f"**Period:** {period}",
        f"**Users:** {overview.get('active_users', '?')} · **Sessions:** {overview.get('sessions', '?')} · **Pageviews:** {overview.get('pageviews', '?')} · **Bounce:** {overview.get('bounce_rate', '?')}%",
    ]
    if sources:
        lines.append("")
        lines.append("**Top channels:**")
        srows = sorted(sources, key=lambda s: -(s.get("sessions") or 0))[:5]
        rows = [(s.get("channel", "?"), s.get("sessions", 0), s.get("users", 0)) for s in srows]
        lines.append(md_table(["Channel", "Sessions", "Users"], rows))
    if top_pages:
        lines.append("")
        lines.append("**Top 5 pages by pageviews:**")
        prows = sorted(top_pages, key=lambda p: -(p.get("pageviews") or 0))[:5]
        for p in prows:
            lines.append(f"- {p.get('path','?')} — {p.get('pageviews',0)} views")
    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_audit_history(site_id, ah_data, ah_mtime):
    """14-day audit issue trend from daily_audit_history.json."""
    if not ah_data:
        return "_no audit history_"
    site = ah_data.get(site_id) or []
    if not site:
        return "_no history for this site_"
    note = staleness_note(ah_mtime, "Audit history")
    recent = site[-14:] if len(site) > 14 else site
    if not recent:
        return (note + "\n\n" if note else "") + "_no entries_"
    first = recent[0]
    last = recent[-1]
    delta_issues = (last.get("issues_total", 0) or 0) - (first.get("issues_total", 0) or 0)
    arrow = "↓" if delta_issues < 0 else ("↑" if delta_issues > 0 else "→")
    lines = [
        f"**{len(recent)}-day window:** {first.get('date','?')} → {last.get('date','?')}",
        f"**Issues:** {first.get('issues_total', 0)} → {last.get('issues_total', 0)} ({arrow}{abs(delta_issues)})",
        f"**Pages with issues:** {first.get('pages_with_issues', 0)} → {last.get('pages_with_issues', 0)}",
    ]
    spikes = [d for d in recent if (d.get("issues_total") or 0) > 0]
    if spikes:
        lines.append("")
        lines.append("**Days with non-zero issues:**")
        for d in spikes[-5:]:
            lines.append(f"- {d.get('date','?')}: {d.get('issues_total',0)} issues across {d.get('pages_with_issues',0)} pages")
    body = "\n".join(lines)
    return (note + "\n\n" if note else "") + body


def section_citation_gaps_by_type(site_id, cbt_data, cbt_mtime):
    """Top 3 query-type clusters with 0% or near-zero citation rate."""
    if not cbt_data:
        return "_no citations-by-type data_"
    site = cbt_data.get(site_id, {})
    if not site:
        return "_no citation-by-type for this site_"
    note = staleness_note(cbt_mtime, "Citations by type")
    by_type = site.get("by_type", {}) or {}
    rows = []
    for type_name, payload in by_type.items():
        rate = payload.get("rate", 0)
        queries = payload.get("queries", 0)
        cited = payload.get("cited", 0)
        rows.append((type_name, rate, cited, queries))
    rows.sort(key=lambda x: x[1])  # ascending by rate (worst first)
    table_rows = [(name, f"{rate}%", f"{cited}/{queries}") for name, rate, cited, queries in rows[:5]]
    body = "**Worst-performing query-type clusters:**\n\n" + md_table(["Type", "Cite rate", "Cited"], table_rows)
    return (note + "\n\n" if note else "") + body


# ---------- brief assembly ----------

def build_brief(site_id, recs_data, recs_mtime, gsc_data, gsc_mtime, gsc_prev,
                serp_data, serp_mtime, citations_data, citations_mtime,
                comp_data, audit_mtime, trends_data, trends_mtime,
                aeo_data, aeo_mtime, miq_data, miq_mtime,
                bot_data, bot_mtime, ps_data, ps_mtime,
                kg_data, kg_mtime, cbt_data, cbt_mtime,
                drift_data, drift_mtime, cf_data, cf_mtime,
                ec_data, ec_mtime, lv_data, lv_mtime,
                ao_data, ao_mtime, bing_data, bing_mtime,
                np_data, np_mtime, ga4_data, ga4_mtime,
                ah_data, ah_mtime, ih_data, ih_mtime,
                is_data, is_mtime, gd_data, gd_mtime):
    display, _, domain = SITES[site_id]
    actions_md, top_actions = section_actions(site_id, recs_data, recs_mtime)
    parts = [
        f"# {display} ({domain}) — Daily brief — {TODAY}",
        "",
        "_Auto-generated by `push_to_fleet.py` from dashboard live data. Do not hand-edit._",
        "",
        "## Top Actions",
        "",
        actions_md,
        "",
        "## Drift detector (assertions tracked vs page content)",
        "",
        section_drift(site_id, drift_data, drift_mtime),
        "",
        "## Entity status (Wikidata / Google Knowledge Graph)",
        "",
        section_entity_status(site_id, kg_data, kg_mtime),
        "",
        "## Entity coherence (sameAs link health)",
        "",
        section_entity_coherence(site_id, ec_data, ec_mtime),
        "",
        "## llms.txt validator",
        "",
        section_llms_validation(site_id, lv_data, lv_mtime),
        "",
        "## Content freshness (refresh pile)",
        "",
        section_content_freshness(site_id, cf_data, cf_mtime),
        "",
        "## AEO scorecard gaps",
        "",
        section_aeo(site_id, aeo_data, aeo_mtime),
        "",
        "## GSC Coverage drilldown (per-issue URL lists from XLSX exports)",
        "",
        section_gsc_drilldown(site_id, gd_data, gd_mtime),
        "",
        "## Indexing status (Google's view via URL Inspection API)",
        "",
        section_indexing_status(site_id, is_data, is_mtime),
        "",
        "## Indexing API submissions (weak signal, see caveat)",
        "",
        section_indexing_health(site_id, ih_data, ih_mtime),
        "",
        "## Manual indexing queue (paste into GSC URL Inspection)",
        "",
        section_manual_indexing(site_id, miq_data, miq_mtime),
        "",
        "## AI Overview triggers + citation status",
        "",
        section_ai_overview(site_id, ao_data, ao_mtime),
        "",
        "## Bing top queries",
        "",
        section_bing_queries(site_id, bing_data, bing_mtime),
        "",
        "## New pages since baseline",
        "",
        section_new_pages(site_id, np_data, np_mtime),
        "",
        "## Page-1 zero-click queries (CTR fix targets)",
        "",
        section_zero_click(site_id, gsc_data, gsc_mtime),
        "",
        "## Climbers (improved position vs yesterday)",
        "",
        section_climbers(site_id, gsc_data, gsc_prev),
        "",
        "## SERP tracking (DataForSEO daily, Google UK)",
        "",
        section_serp(site_id, serp_data, serp_mtime),
        "",
        "## AI Search citation gaps",
        "",
        section_ai_citations(site_id, citations_data, citations_mtime),
        "",
        "## Citation gaps by query-type cluster",
        "",
        section_citation_gaps_by_type(site_id, cbt_data, cbt_mtime),
        "",
        "## Competitor visibility",
        "",
        section_competitors(site_id, comp_data),
        "",
        "## AI/search bot activity (last 7 days)",
        "",
        section_bot_activity(site_id, bot_data, bot_mtime),
        "",
        "## PageSpeed (mobile)",
        "",
        section_pagespeed(site_id, ps_data, ps_mtime),
        "",
        "## Crawl audit (today)",
        "",
        section_audit(site_id, audit_mtime),
        "",
        "## Crawl: thin pages, broken pages, orphans",
        "",
        section_thin_pages_broken(site_id),
        "",
        "## Audit history (last 14 days)",
        "",
        section_audit_history(site_id, ah_data, ah_mtime),
        "",
        "## GA4 traffic",
        "",
        section_ga4_traffic(site_id, ga4_data, ga4_mtime),
        "",
        "## Trends (Google Trends GB, 3mo)",
        "",
        section_trends(site_id, trends_data, trends_mtime),
        "",
        "## Content plans on file",
        "",
        section_content_plans(site_id),
        "",
        "## Wins (resolved since yesterday)",
        "",
        section_wins(site_id),
        "",
        "---",
        "",
        f"_Generated {datetime.now().isoformat(timespec='seconds')}_",
    ]
    return "\n".join(parts), top_actions


def write_brief(site_id, brief_md, top_actions):
    display, repo, _ = SITES[site_id]

    # 1. iCloud archive
    archive_dir = ICLOUD_FLEET / "daily" / str(TODAY)
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"{display}.md"
    archive_path.write_text(brief_md)

    # 2. Repo root — only write if changed (avoid no-op commits)
    repo_path = repo / "DAILY_BRIEF.md"
    if not repo.exists():
        return archive_path, None, "repo missing"
    existing = repo_path.read_text() if repo_path.exists() else ""
    # Strip the trailing timestamp line from both before comparing,
    # so timestamp-only diffs don't trigger a commit.
    def strip_ts(s):
        return "\n".join(s.split("\n")[:-2]) if s else ""
    if strip_ts(existing) == strip_ts(brief_md):
        return archive_path, repo_path, "unchanged"
    repo_path.write_text(brief_md)
    return archive_path, repo_path, "updated"


def update_inbox(entries):
    """Prepend a one-line index entry per site under a dated heading."""
    if not INBOX.exists():
        return
    existing = INBOX.read_text()
    header = f"\n## Daily push — {TODAY}\n\n"
    body = "\n".join(entries) + "\n"
    block = header + body
    # Avoid duplicate prepend if already pushed today
    if f"## Daily push — {TODAY}" in existing:
        # Replace today's block in place
        lines = existing.split("\n")
        out = []
        skipping = False
        for i, line in enumerate(lines):
            if line.strip() == f"## Daily push — {TODAY}":
                skipping = True
                continue
            if skipping and line.startswith("## "):
                skipping = False
            if not skipping:
                out.append(line)
        existing = "\n".join(out)
    # Find first '## ' heading and prepend before it; fallback prepend at top
    if "\n## " in existing:
        idx = existing.index("\n## ")
        new = existing[:idx] + block + existing[idx:]
    else:
        new = block + existing
    INBOX.write_text(new)


def main(dry_run=False):
    recs_data, recs_mtime = load_json("recommendations.json")
    gsc_data, gsc_mtime = load_json("gsc.json")
    gsc_prev, _ = load_json("gsc_previous.json")
    serp_data, serp_mtime = load_json("serp_data.json")
    citations_data, citations_mtime = load_json("citations_by_type.json")
    comp_data, _ = load_json("competitor_serp.json")
    trends_data, trends_mtime = load_json("google_trends.json")
    # audit mtime is per-site, sample one to get a reading
    _, audit_mtime = load_json("daily_audit_rank4ai.json")
    # v2 sources (added 2026-05-04)
    aeo_data, aeo_mtime = load_json("aeo_scorecard.json")
    miq_data, miq_mtime = load_json("manual_indexing_queue.json")
    bot_data, bot_mtime = load_json("bot_hits.json")
    ps_data, ps_mtime = load_json("pagespeed.json")
    kg_data, kg_mtime = load_json("knowledge_graph.json")
    cbt_data, cbt_mtime = load_json("citations_by_type.json")
    # v3 sources (added 2026-05-05)
    drift_data, drift_mtime = load_json("drift_report.json")
    cf_data, cf_mtime = load_json("content_freshness.json")
    ec_data, ec_mtime = load_json("entity_coherence.json")
    lv_data, lv_mtime = load_json("llms_validation.json")
    ao_data, ao_mtime = load_json("ai_overview_serp.json")
    bing_data, bing_mtime = load_json("bing.json")
    np_data, np_mtime = load_json("new_pages.json")
    ga4_data, ga4_mtime = load_json("ga4.json")
    ah_data, ah_mtime = load_json("daily_audit_history.json")
    ih_data, ih_mtime = load_json("indexing_health.json")
    is_data, is_mtime = load_json("indexing_status.json")
    gd_data, gd_mtime = load_json("gsc_coverage_drilldown.json")

    inbox_entries = []
    print(f"push_to_fleet.py — {TODAY}")
    for site_id in SITES:
        if site_id in PRE_LAUNCH:
            print(f"  skip {site_id} (pre_launch:true in clients.json)")
            continue
        display, _, domain = SITES[site_id]
        brief, top_actions = build_brief(
            site_id, recs_data, recs_mtime, gsc_data, gsc_mtime, gsc_prev,
            serp_data, serp_mtime, citations_data, citations_mtime,
            comp_data, audit_mtime, trends_data, trends_mtime,
            aeo_data, aeo_mtime, miq_data, miq_mtime,
            bot_data, bot_mtime, ps_data, ps_mtime,
            kg_data, kg_mtime, cbt_data, cbt_mtime,
            drift_data, drift_mtime, cf_data, cf_mtime,
            ec_data, ec_mtime, lv_data, lv_mtime,
            ao_data, ao_mtime, bing_data, bing_mtime,
            np_data, np_mtime, ga4_data, ga4_mtime,
            ah_data, ah_mtime, ih_data, ih_mtime,
            is_data, is_mtime, gd_data, gd_mtime,
        )
        if dry_run:
            out_dir = Path("/tmp/fleet_dry_run")
            out_dir.mkdir(parents=True, exist_ok=True)
            out = out_dir / f"{display}.md"
            out.write_text(brief)
            print(f"  {display} ({domain}) → {out}  ({len(brief)} bytes)")
            continue
        archive, repo_file, status = write_brief(site_id, brief, top_actions)
        print(f"  {display} → archive={archive.name} repo={status}")
        n_actions = len(top_actions)
        rel = archive.relative_to(ICLOUD_FLEET)
        inbox_entries.append(f"- [{display} brief]({rel}) — {n_actions} top actions")

    if not dry_run and inbox_entries:
        update_inbox(inbox_entries)
        print(f"  INBOX updated: {len(inbox_entries)} entries")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
