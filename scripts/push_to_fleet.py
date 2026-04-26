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
SITES = {
    "rank4ai":        ("R4", Path.home() / "rank4ai-site",            "rank4ai.co.uk"),
    "market-invoice": ("MI", Path.home() / "compare-invoice-finance", "marketinvoice.co.uk"),
    "seocompare":     ("SC", Path.home() / "compareaiseo",            "seocompare.co.uk"),
}

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


# ---------- brief assembly ----------

def build_brief(site_id, recs_data, recs_mtime, gsc_data, gsc_mtime, gsc_prev,
                serp_data, serp_mtime, citations_data, citations_mtime,
                comp_data, audit_mtime, trends_data, trends_mtime):
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
        "## Competitor visibility",
        "",
        section_competitors(site_id, comp_data),
        "",
        "## Crawl audit (today)",
        "",
        section_audit(site_id, audit_mtime),
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

    inbox_entries = []
    print(f"push_to_fleet.py — {TODAY}")
    for site_id in SITES:
        display, _, domain = SITES[site_id]
        brief, top_actions = build_brief(
            site_id, recs_data, recs_mtime, gsc_data, gsc_mtime, gsc_prev,
            serp_data, serp_mtime, citations_data, citations_mtime,
            comp_data, audit_mtime, trends_data, trends_mtime,
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
