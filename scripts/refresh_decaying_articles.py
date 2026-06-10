#!/usr/bin/env python3
"""
refresh_decaying_articles.py — weekly "refresh the top/decaying pages" drafter.

The auto-publisher only ever publishes NEW content. This is the missing other
half: it finds the pages most WORTH refreshing per site and drafts a review
brief for each (what's stale + specific suggested updates), for a human to
approve. It NEVER edits or publishes — output is draft-for-review only, mirror
of fleet_embeddings.py.

Inputs (all already produced by the dashboard pipeline — no new fetching):
  - gsc.json            -> top_pages (traffic + position)  = "worth the effort"
  - content_decay.json  -> queries/pages losing position   = "slipping now"
  - content_freshness.json -> oldest_pages (age + word_count) = "stale"

Scoring per page = traffic (log clicks+impr) + decay flag + age. Top N per site
get a Claude-drafted refresh brief built from the LIVE page text.

Output:
  iCloud/claude/Audits/content-refresh/<site>_<YYYY-MM-DD>.md   (human review)
  iCloud/claude/Audits/content-refresh/<site>_<YYYY-MM-DD>.json

Usage:
  python3 refresh_decaying_articles.py            # all sites with GSC data
  python3 refresh_decaying_articles.py rank4ai    # one site
  python3 refresh_decaying_articles.py --top 8    # candidates per site (default 5)

Keys: anthropic_api_key from ~/.llm_keys.json (or ANTHROPIC_API_KEY env).
"""
import os, sys, json, re, math, time, argparse
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

HOME = Path.home()
LIVE = HOME / "rank4ai-dashboard/src/data/live"
OUT = HOME / "Library/Mobile Documents/com~apple~CloudDocs/claude/Audits/content-refresh"
OUT.mkdir(parents=True, exist_ok=True)
MODEL = "claude-sonnet-4-6"
TODAY = None  # set in main() from arg to keep runs reproducible / resumable


def load(name):
    p = LIVE / name
    return json.load(open(p)) if p.exists() else {}


def anthropic_key():
    k = os.environ.get("ANTHROPIC_API_KEY")
    if k:
        return k
    return json.load(open(HOME / ".llm_keys.json")).get("anthropic_api_key")


def _sites_block(d):
    return d.get("sites", d) if isinstance(d, dict) else {}


def candidates(site_id, top_n):
    """Merge traffic + decay + freshness into one scored, de-duped page list."""
    gsc = _sites_block(load("gsc.json")).get(site_id, {})
    decay = _sites_block(load("content_decay.json")).get(site_id, {})
    fresh = _sites_block(load("content_freshness.json")).get(site_id, {})

    pages = {}   # path -> record

    def rec(path):
        path = "/" + path.strip("/") + "/" if path.strip("/") else "/"
        return pages.setdefault(path, {
            "path": path, "clicks": 0, "impressions": 0, "position": None,
            "decay": [], "age_days": None, "word_count": None, "h1": None,
        })

    for p in gsc.get("top_pages", []):
        path = urlparse(p.get("page", "")).path or "/"
        r = rec(path)
        r["clicks"] = max(r["clicks"], p.get("clicks", 0) or 0)
        r["impressions"] = max(r["impressions"], p.get("impressions", 0) or 0)
        if p.get("position"):
            r["position"] = p["position"]

    # decay signals are query-level with a page reference
    for kind, items in decay.items():
        if not isinstance(items, list):
            continue
        for it in items:
            page = it.get("page") or it.get("url")
            if not page:
                continue
            r = rec(urlparse(page).path or "/")
            r["decay"].append({"kind": kind, "query": it.get("query", "")})

    for p in fresh.get("oldest_pages", []):
        r = rec(p.get("path") or urlparse(p.get("url", "")).path or "/")
        r["age_days"] = p.get("age_days")
        r["word_count"] = p.get("word_count")
        r["h1"] = p.get("h1")

    # score: traffic worth the effort + currently slipping + getting old
    for r in pages.values():
        traffic = math.log10(1 + r["clicks"] * 5 + r["impressions"])
        decay_w = 2.0 * len(r["decay"])
        age_w = (r["age_days"] / 120.0) if r["age_days"] else 0
        r["score"] = round(traffic + decay_w + age_w, 2)

    ranked = sorted(pages.values(), key=lambda r: -r["score"])
    # only bother with pages that have SOME traffic or a decay signal
    ranked = [r for r in ranked if r["clicks"] or r["impressions"] or r["decay"]]
    return ranked[:top_n]


def fetch_page(url):
    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": "rank4ai-refresh/1.0"})
        if resp.status_code != 200:
            return None, None
        soup = BeautifulSoup(resp.text, "html.parser")
        title = (soup.title.string if soup.title else "") or ""
        main = soup.find("main") or soup.body or soup
        for tag in main(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = re.sub(r"\n{3,}", "\n\n", main.get_text("\n", strip=True))
        return title.strip(), text[:8000]
    except Exception:
        return None, None


def draft_brief(client, domain, rec, title, text):
    signals = []
    if rec["decay"]:
        qs = ", ".join(sorted({d["query"] for d in rec["decay"] if d["query"]})[:5])
        signals.append(f"Losing position in Google for: {qs}")
    if rec["age_days"]:
        signals.append(f"Last modified {rec['age_days']} days ago ({rec.get('word_count') or '?'} words)")
    if rec["clicks"] or rec["impressions"]:
        signals.append(f"GSC: {rec['clicks']} clicks / {rec['impressions']} impressions"
                       + (f", avg pos {rec['position']:.0f}" if rec.get("position") else ""))
    prompt = f"""You are reviewing an existing live page on {domain} to decide how to REFRESH it (not rewrite from scratch, not republish automatically). A human will approve your suggestions.

Page: https://{domain}{rec['path']}
Title: {title}
Why it surfaced: {'; '.join(signals)}

Live page text (truncated):
\"\"\"
{text}
\"\"\"

Give a tight refresh brief in markdown with these sections:
- **Verdict** (one line: Refresh / Light touch / Leave)
- **Stale signals** (specific: outdated years, figures, "as of" dates, named tools/competitors, anything that reads old — quote the exact phrase)
- **Suggested updates** (3-6 concrete bullets a writer can action; be specific, no fluff)
- **New angle** (one idea to regain the slipping query, if relevant)
Keep it under 200 words. No em dashes. If the page looks current and fine, say so and stop."""
    try:
        msg = client.messages.create(
            model=MODEL, max_tokens=700,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        return f"_(brief generation failed: {e})_"


def run_site(client, site_id, domain, top_n):
    cands = candidates(site_id, top_n)
    if not cands:
        print(f"  {site_id}: no refresh candidates")
        return None
    print(f"  {site_id}: {len(cands)} candidates")
    items = []
    for rec in cands:
        url = f"https://{domain}{rec['path']}"
        title, text = fetch_page(url)
        if not text:
            print(f"     skip (unfetchable) {rec['path']}")
            continue
        brief = draft_brief(client, domain, rec, title, text)
        items.append({**rec, "url": url, "title": title, "brief": brief})
        print(f"     drafted {rec['path']} (score {rec['score']})")
        time.sleep(1)
    # write report
    md = [f"# Content refresh queue — {site_id} ({TODAY})", ""]
    md.append("Draft-for-review. Nothing here is published. Pages ranked by "
              "traffic + decay + age.\n")
    for it in items:
        md += [f"## {it['title'] or it['path']}", f"`{it['url']}`  ·  score {it['score']}", "", it["brief"], "", "---", ""]
    (OUT / f"{site_id}_{TODAY}.md").write_text("\n".join(md))
    json.dump({"site": site_id, "date": TODAY, "items": items},
              open(OUT / f"{site_id}_{TODAY}.json", "w"), indent=2)
    return len(items)


def main():
    global TODAY
    ap = argparse.ArgumentParser()
    ap.add_argument("sites", nargs="*")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--date", default=None, help="YYYY-MM-DD stamp (default: derived once at start)")
    a = ap.parse_args()

    # Date is passed in (cron supplies it) so output filenames are stable; fall
    # back to a fixed label if absent (avoids Date.now-style nondeterminism).
    TODAY = a.date or os.environ.get("REFRESH_DATE") or "latest"

    clients = json.load(open(HOME / "rank4ai-dashboard/src/data/clients.json"))
    if isinstance(clients, dict):
        clients = clients.get("clients", list(clients.values()))
    dom = {c["id"]: c["domain"] for c in clients if c.get("id") and c.get("domain")}

    gsc_sites = list(_sites_block(load("gsc.json")).keys())
    targets = a.sites or [s for s in gsc_sites if s in dom]

    client = __import__("anthropic").Anthropic(api_key=anthropic_key())
    total = 0
    for site_id in targets:
        if site_id not in dom:
            print(f"  unknown site {site_id}"); continue
        n = run_site(client, site_id, dom[site_id].split("/")[0], a.top)
        total += n or 0
    print(f"\nDone: {total} refresh briefs across {len(targets)} sites -> {OUT}")


if __name__ == "__main__":
    main()
