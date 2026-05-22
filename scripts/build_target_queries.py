#!/usr/bin/env python3
"""
build_target_queries.py — derive each site's REAL target keywords from
its own content + GSC impressions data.

No more head-term lists. The fleet sites already encode their targeting
in URL patterns (/vs/, /best/, /alternatives/, /providers/, /industries/,
/compare/, /cheapest/, /how-to/), page titles, and H1s. GSC tells us
which of those queries Google actually associates with each site.

Output → src/data/live/target_queries.json
{
  "<site_id>": {
    "from_content": [  # derived from crawl_<site>.json
      {"query": "best invoice finance UK", "source": "/best/", "path": "/best/...", "h1": "..."},
      ...
    ],
    "from_gsc": [  # derived from gsc.json top_queries
      {"query": "...", "impressions": 451, "position": 28.0, "non_branded": true},
      ...
    ],
    "merged_top": [...]  # dedupe + rank: GSC-evidenced first, then content
  }
}
"""
import json
import os
import re
from pathlib import Path

LIVE = Path(os.path.expanduser("~/rank4ai-dashboard/src/data/live"))

# URL path patterns the fleet uses for target-query pages.
# Slug → query reconstruction strategy varies by pattern.
TARGET_PATH_PATTERNS = [
    "/best/", "/vs/", "/alternatives/", "/cheapest/", "/compare/",
    "/providers/", "/industries/", "/services/", "/how-to/",
    "/who-is/", "/what-is/", "/guides/", "/reviews/",
]


def slug_to_phrase(slug: str) -> str:
    """Convert a URL slug to a search-phrase form."""
    s = slug.strip("/").split("/")[-1]
    s = re.sub(r"-vs-", " vs ", s)
    s = re.sub(r"-", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_branded(query: str, brand_tokens) -> bool:
    norm = re.sub(r"[^a-z0-9]", "", query.lower())
    return any(t and t in norm for t in brand_tokens)


def brand_tokens_for(site_id: str, domain: str) -> list:
    base = re.sub(r"\.(co\.uk|com|ai|uk|org)$", "", domain.lower())
    return list({base.replace("-", "").replace(".", ""), site_id.replace("-", "")})


def derive_from_crawl(crawl: dict) -> list:
    """Pull a target-query candidate from each page that matches a
    target path pattern. Use title/h1 as the canonical query phrase
    (cleaner than reconstructing from slug)."""
    pages = crawl.get("pages", [])
    out = []
    seen = set()
    for p in pages:
        path = p.get("path", "")
        if not any(pat in path for pat in TARGET_PATH_PATTERNS):
            continue
        # Title is usually the cleanest target phrase
        title = (p.get("title") or "").strip()
        h1 = (p.get("h1") or "").strip()
        # Strip common site-suffixes ("| Site Name")
        for sep in (" | ", " — ", " - ", " · "):
            if sep in title:
                title = title.split(sep)[0].strip()
        # Truncate at colon-segments that often mark a sub-claim
        primary = title or h1 or slug_to_phrase(path)
        if not primary:
            continue
        key = re.sub(r"\s+", " ", primary.lower())
        if key in seen:
            continue
        seen.add(key)
        # Which pattern bucket
        bucket = next((pat for pat in TARGET_PATH_PATTERNS if pat in path), "/other/")
        out.append({
            "query": primary,
            "pattern": bucket,
            "path": path,
            "h1": h1,
            "word_count": p.get("word_count", 0),
        })
    return out


def is_noise_query(text: str) -> bool:
    """Filter out research/operator queries that aren't real targeting signals."""
    if not text or len(text) > 90:
        return True
    if "-site:" in text or "site:" in text or '"' in text:
        return True
    if text.count(" ") > 10:  # 11+ word queries are usually conversational, not target intent
        return True
    return False


def derive_from_gsc(gsc_data: dict, brand_tokens) -> list:
    """Take GSC top_queries (already imp-ordered), filter to non-branded
    and impressions >= 10. These are queries Google ALREADY associates
    with the site."""
    queries = gsc_data.get("top_queries", []) or []
    out = []
    for q in queries:
        text = q.get("query", "")
        if q.get("impressions", 0) < 10:
            continue
        if is_noise_query(text):
            continue
        out.append({
            "query": text,
            "impressions": q.get("impressions", 0),
            "clicks": q.get("clicks", 0),
            "ctr": q.get("ctr", 0),
            "position": q.get("position", 0),
            "branded": is_branded(text, brand_tokens),
        })
    return out


def merge_top(from_content: list, from_gsc: list) -> list:
    """Build a single ranked list. GSC-evidenced queries first (highest
    impressions), then content-derived non-branded that GSC doesn't see
    yet (= ranking opportunities)."""
    seen = set()
    merged = []
    # 1. GSC-evidenced non-branded
    for g in sorted(from_gsc, key=lambda x: -x.get("impressions", 0)):
        if g.get("branded"):
            continue
        norm = re.sub(r"[^a-z0-9 ]", "", g["query"].lower())
        if norm in seen:
            continue
        seen.add(norm)
        merged.append({
            "query": g["query"],
            "source": "gsc",
            "impressions": g.get("impressions", 0),
            "position": g.get("position", 0),
            "clicks": g.get("clicks", 0),
        })
    # 2. Content-derived (gaps Google doesn't see yet)
    for c in from_content:
        norm = re.sub(r"[^a-z0-9 ]", "", c["query"].lower())
        if norm in seen:
            continue
        seen.add(norm)
        merged.append({
            "query": c["query"],
            "source": "content",
            "pattern": c["pattern"],
            "path": c["path"],
            "impressions": 0,
            "position": 0,
        })
    return merged


def main():
    # Sites known to the dashboard
    crawl_files = sorted(LIVE.glob("crawl_*.json"))
    sites = []
    for f in crawl_files:
        m = re.match(r"crawl_(.+)\.json$", f.name)
        if m:
            sites.append(m.group(1))

    gsc_all = json.load(open(LIVE / "gsc.json")) if (LIVE / "gsc.json").exists() else {}
    # GSC keys use "market-invoice" form. Crawl uses same.

    out = {}
    for site_id in sites:
        try:
            crawl = json.load(open(LIVE / f"crawl_{site_id}.json"))
        except Exception:
            continue
        domain = crawl.get("domain", "")
        bt = brand_tokens_for(site_id, domain)

        from_content = derive_from_crawl(crawl)
        gsc_site = gsc_all.get(site_id, {})
        # Try alt keys for the few legacy mismatches
        if not gsc_site:
            for alt in [site_id.replace("-", ""), site_id.replace("_", "-")]:
                if alt in gsc_all:
                    gsc_site = gsc_all[alt]
                    break
        from_gsc = derive_from_gsc(gsc_site, bt)
        merged = merge_top(from_content, from_gsc)

        out[site_id] = {
            "domain": domain,
            "brand_tokens": bt,
            "from_content_total": len(from_content),
            "from_gsc_total": len(from_gsc),
            "merged_top": merged[:60],
            "by_pattern": {},
        }
        # Group content-derived by pattern, for the UI
        for c in from_content:
            pat = c["pattern"]
            out[site_id]["by_pattern"].setdefault(pat, []).append(c)

    output = LIVE / "target_queries.json"
    with open(output, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote → {output}")
    print()
    for site_id, v in out.items():
        print(f"  {site_id:20s}  content={v['from_content_total']:4d}  gsc={v['from_gsc_total']:4d}  merged={len(v['merged_top'])}")


if __name__ == "__main__":
    main()
