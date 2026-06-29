#!/usr/bin/env python3
"""
Read fleet site source directly and emit crawl_<slug>.json with the same
shape Site Manager + Site Tree + Internal Links + Page Compliance expect.

Replaces external crawling for sites we own. The source is the truth:
- Page count = static src/pages/*.astro + dynamic-route data entries
- Schema = BaseLayout imports SchemaGraph (per-site boolean → applied to all pages)
- Word counts = parsed from dist/*.html when available (falls back to source estimate)
- dateModified = lastReviewed in data files / last git commit per file
- Topic clusters = top-level dirs under src/pages/

Runs in seconds. Always in sync — re-run whenever you want fresh dashboard data.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_DIR = Path(os.path.expanduser("~/rank4ai-dashboard/src/data/live"))

# slug -> { repo, domain (live), preview }
FLEET = {
    "bestbusinessloans": {
        "repo": "~/bestbusinessloans",
        "domain": "bestbusinessloans.pages.dev",
        "live": "bestbusinessloans.ai",
    },
    "fundbiz": {
        "repo": "~/fundbiz",
        "domain": "fundbiz.pages.dev",
        "live": "fundbiz.co.uk",
    },
    "cardmachines": {
        "repo": "~/cardmachines",
        "domain": "cardmachines.pages.dev",
        "live": "cardmachines.co.uk",
    },
    "market-invoice": {
        "repo": "~/compare-invoice-finance",
        "domain": "marketinvoice.co.uk",
        "live": "marketinvoice.co.uk",
    },
    "seocompare": {
        "repo": "~/compareaiseo",
        "domain": "seocompare.co.uk",
        "live": "seocompare.co.uk",
    },
    "rank4ai": {
        "repo": "~/rank4ai-site",
        "domain": "www.rank4ai.co.uk",
        "live": "www.rank4ai.co.uk",
    },
    "builderweb": {
        "repo": "~/builderweb-marketing",
        "domain": "builderweb.online",
        "live": "builderweb.online",
    },
    "peptideclear": {
        "repo": "~/ukmetabolic",
        "domain": "peptideclear.co.uk",
        "live": "peptideclear.co.uk",
    },
    "findatradey": {
        "repo": "~/findatradey",
        "domain": "findatradey.pages.dev",
        "live": "findatradey.co.uk",
    },
    "findagym": {
        "repo": "~/findagym",
        "domain": "findagym.pages.dev",
        "live": "findagym.co.uk",
    },
    "takecardpayments": {
        "repo": "~/takecardpayments",
        "domain": "takecardpayments.co.uk",
        "live": "takecardpayments.co.uk",
    },
    "mortgageexplained": {
        "repo": "~/mortgageexplained",
        "domain": "mortgageexplained.co.uk",
        "live": "mortgageexplained.co.uk",
    },
}

WORD_RE = re.compile(r"\b\w+\b")
HREF_RE = re.compile(r'href=["\'](/[^"\'#]*)["\']')
SCHEMA_SCRIPT_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL,
)
META_DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', re.IGNORECASE
)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL | re.IGNORECASE)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL | re.IGNORECASE)
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html or "")


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def site_url_from_config(repo: Path) -> str | None:
    cfg = repo / "astro.config.mjs"
    if not cfg.exists():
        return None
    m = re.search(r"site:\s*['\"]([^'\"]+)", cfg.read_text())
    return m.group(1).rstrip("/") if m else None


def has_schema_graph(repo: Path) -> bool:
    for layout in (repo / "src/layouts").rglob("*.astro"):
        text = layout.read_text(errors="ignore")
        if "SchemaGraph" in text or "@graph" in text:
            return True
    return False


def topic_cluster_from_path(path: str) -> str:
    """First path segment after leading slash. '/best/x' -> 'best'."""
    parts = [p for p in path.split("/") if p]
    return parts[0] if parts else "home"


def page_record_from_html(url: str, path: str, html: str) -> dict:
    body = strip_tags(html)
    schemas = []
    for block in SCHEMA_SCRIPT_RE.findall(html):
        try:
            obj = json.loads(block.strip())
            if isinstance(obj, dict):
                if "@graph" in obj:
                    for n in obj["@graph"]:
                        t = n.get("@type")
                        if t:
                            schemas.append(t if isinstance(t, str) else " ".join(t))
                elif obj.get("@type"):
                    t = obj["@type"]
                    schemas.append(t if isinstance(t, str) else " ".join(t))
        except Exception:
            pass

    title_m = TITLE_RE.search(html)
    h1_m = H1_RE.search(html)
    desc_m = META_DESC_RE.search(html)
    internal_links = list(set(HREF_RE.findall(html)))

    return {
        "url": url,
        "path": path,
        "title": (title_m.group(1).strip() if title_m else "")[:200],
        "h1": (strip_tags(h1_m.group(1)).strip() if h1_m else "")[:200],
        "meta_desc": (desc_m.group(1) if desc_m else "")[:300],
        "word_count": count_words(body),
        "status": 200,
        "schemas": schemas,
        "internal_links_out": len(internal_links),
        "external_links_out": len(re.findall(r'href=["\']https?://', html)) - len(internal_links),
        "canonical": url,
        "response_time_ms": 0,  # source-of-truth, no network probe
        "image_count": len(re.findall(r"<img\b", html)),
        "images_with_alt": len(re.findall(r'<img[^>]+alt=["\'][^"\']+', html)),
        "video_count": len(re.findall(r"<video\b", html)),
        "has_multimodal": "<video" in html or "<audio" in html,
        "has_comparison_table": "comparison-table" in html.lower() or "<table" in html.lower(),
        "table_count": len(re.findall(r"<table\b", html)),
        "list_count": len(re.findall(r"<(?:ul|ol)\b", html)),
        "question_h2s": len(re.findall(r"<h2[^>]*>[^<]*\?", html, re.IGNORECASE)),
        "h2_count": len(re.findall(r"<h2\b", html)),
        "last_modified": (DATE_RE.search(html).group(0) if DATE_RE.search(html) else None),
        "has_answer_capsule": "answer-capsule" in html or "summary-card" in html or "ai-comprehension" in html.lower(),
        "has_og_tags": 'property="og:' in html,
        "has_author": "author" in html.lower() and ("byline" in html.lower() or "rel=\"author\"" in html.lower() or "Mackman" in html or "Adam Parker" in html),
        "has_definition": "<dl" in html or "definition" in html.lower(),
        "has_cta": "cta" in html.lower() or "get-quotes" in html or "eligibility-checker" in html or "apply" in html.lower(),
        "has_breadcrumbs": "breadcrumb" in html.lower(),
        "has_viewport": 'name="viewport"' in html,
        "internal_links_in": 0,  # filled in below
        "depth": max(0, path.count("/") - 1),
        "internal_links_list": internal_links,  # used to compute incoming, removed before write
    }


def load_sitemap_urls(dist_dir: Path) -> set[str] | None:
    """Read built sitemap-*.xml from dist/ to get the canonical indexable URL
    set. Returns None if no sitemap found (caller falls back to all dist/*.html).
    Honours the astro.config.mjs sitemap filter — pages excluded from the
    sitemap (admin, preview, redirect targets) are excluded from the dashboard
    view too. That way 'pages' in the dashboard = 'pages Google should index'."""
    if not dist_dir.exists():
        return None
    sitemap_urls: set[str] = set()
    for sm in dist_dir.glob("sitemap-*.xml"):
        try:
            text = sm.read_text(errors="ignore")
        except Exception:
            continue
        for match in re.finditer(r"<loc>([^<]+)</loc>", text):
            url = match.group(1).strip()
            # Normalise — strip trailing slash variants are kept as-is from sitemap
            sitemap_urls.add(url.split("#")[0].split("?")[0])
    return sitemap_urls or None


def collect_dist_pages(dist_dir: Path, site_url: str) -> list[dict]:
    if not dist_dir.exists():
        return []
    sitemap_urls = load_sitemap_urls(dist_dir)
    pages = []
    for html_file in dist_dir.rglob("*.html"):
        rel = html_file.relative_to(dist_dir)
        path = "/" + str(rel.parent).replace("\\", "/").strip("/") + "/"
        if rel.name != "index.html":
            path = "/" + str(rel.with_suffix("")).replace("\\", "/").strip("/") + "/"
        if path == "//":
            path = "/"
        url = site_url + path
        # Honour sitemap filter: if site has a sitemap and this URL isn't in it,
        # skip — it's an admin / preview / redirect-target page that shouldn't
        # be in the dashboard's 'indexable pages' view.
        if sitemap_urls is not None:
            if url not in sitemap_urls and url.rstrip("/") not in sitemap_urls and url + "/" not in sitemap_urls:
                continue
        try:
            html = html_file.read_text(errors="ignore")
        except Exception:
            continue
        pages.append(page_record_from_html(url, path, html))
    return pages


def build_tree(pages: list[dict]) -> dict:
    root = {"name": "/", "path": "/", "children": {}}
    for p in pages:
        parts = [s for s in p["path"].split("/") if s]
        node = root
        cur = ""
        for part in parts:
            cur += "/" + part
            ch = node["children"].setdefault(part, {"name": part, "path": cur + "/", "children": {}})
            node = ch
    # Convert children dicts to lists
    def finalize(node):
        node["children"] = [finalize(v) for v in node["children"].values()]
        return node
    return finalize(root)


def build_topic_clusters(pages: list[dict]) -> dict:
    clusters = defaultdict(lambda: {"hub": "", "page_count": 0})
    for p in pages:
        c = topic_cluster_from_path(p["path"])
        if c == "home":
            continue
        clusters[c]["hub"] = f"/{c}/"
        clusters[c]["page_count"] += 1
    return dict(clusters)


def term_consistency(pages: list[dict], top: int = 15) -> dict:
    counter = defaultdict(int)
    for p in pages:
        for w in WORD_RE.findall((p.get("title", "") + " " + p.get("h1", "") + " " + p.get("meta_desc", "")).lower()):
            if len(w) > 3 and w not in {"with", "from", "this", "that", "your", "have", "what", "when", "where", "which", "their", "them"}:
                counter[w] += 1
    return dict(sorted(counter.items(), key=lambda x: -x[1])[:top])


def content_freshness(pages: list[dict]) -> dict:
    today = datetime.now(timezone.utc).date()
    fresh_30 = fresh_90 = stale = with_dates = 0
    for p in pages:
        d = p.get("last_modified")
        if not d:
            continue
        with_dates += 1
        try:
            dt = datetime.strptime(d, "%Y-%m-%d").date()
            age = (today - dt).days
            if age <= 30:
                fresh_30 += 1
            elif age <= 90:
                fresh_90 += 1
            else:
                stale += 1
        except Exception:
            pass
    return {
        "pages_with_dates": with_dates,
        "fresh_30_days": fresh_30,
        "fresh_90_days": fresh_90,
        "stale": stale,
    }


def crawler_access_from_robots(repo: Path) -> dict:
    robots = repo / "public/robots.txt"
    if not robots.exists():
        return {bot: True for bot in ["GPTBot", "ClaudeBot", "PerplexityBot", "Googlebot", "Bingbot"]}
    text = robots.read_text()
    blocked_all = bool(re.search(r"^\s*User-agent:\s*\*\s*\n\s*Disallow:\s*/\s*$", text, re.MULTILINE))
    if blocked_all:
        return {bot: False for bot in ["GPTBot", "ClaudeBot", "PerplexityBot", "Googlebot", "Bingbot"]}
    return {bot: True for bot in ["GPTBot", "ClaudeBot", "PerplexityBot", "Googlebot", "Bingbot"]}


def positive_signals(pages: list[dict]) -> list[dict]:
    signals = []
    for p in pages[:200]:
        score = 0
        notes = []
        if p["has_og_tags"]:
            score += 1; notes.append("OG")
        if p["schemas"]:
            score += 1; notes.append(f"Schema:{len(p['schemas'])}")
        if p["has_author"]:
            score += 1; notes.append("Author")
        if p["word_count"] >= 300:
            score += 1; notes.append("Substantive")
        if p["has_breadcrumbs"]:
            score += 1; notes.append("Breadcrumbs")
        if score >= 3:
            signals.append({"path": p["path"], "score": score, "signals": notes})
    return signals


def read_site(slug: str, conf: dict) -> dict:
    repo = Path(os.path.expanduser(conf["repo"]))
    site_url = site_url_from_config(repo) or f"https://{conf['domain']}"

    dist = repo / "dist"
    pages = collect_dist_pages(dist, site_url)

    # Compute incoming links from outgoing-link sets
    by_path = {p["path"]: p for p in pages}
    for p in pages:
        for href in p.get("internal_links_list", []):
            href_norm = href if href.endswith("/") else href + "/"
            if href_norm in by_path:
                by_path[href_norm]["internal_links_in"] += 1
    for p in pages:
        p.pop("internal_links_list", None)

    # Build link list
    links = []
    for p in pages:
        for href in re.findall(r'href=["\'](/[^"\'#]*)["\']', "\n".join(p["title"] for p in [p])):
            pass  # already counted
    # rebuild link list from pages output dirs
    for html_file in dist.rglob("*.html"):
        try:
            html = html_file.read_text(errors="ignore")
        except Exception:
            continue
        rel = html_file.relative_to(dist)
        from_path = "/" + (str(rel.parent).strip("/") + "/" if rel.name == "index.html" else str(rel.with_suffix("")).strip("/") + "/")
        from_path = from_path.replace("//", "/")
        from_url = site_url + from_path
        for href in HREF_RE.findall(html):
            to = href if href.startswith("http") else site_url + href
            links.append({"from": from_url, "to": to, "type": "internal"})
        if len(links) > 5000:
            break

    issues = []
    for p in pages:
        if not p["title"]:
            issues.append({"url": p["url"], "type": "missing_title", "detail": "Empty <title>"})
        if not p["meta_desc"]:
            issues.append({"url": p["url"], "type": "missing_meta_desc", "detail": "No meta description"})
    issues = issues[:50]

    orphans = [{"path": p["path"], "url": p["url"]} for p in pages if p["internal_links_in"] == 0 and p["path"] != "/"]

    schemas_present = has_schema_graph(repo) or any(p["schemas"] for p in pages)

    return {
        "site_id": slug,
        "domain": conf["domain"],
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "source": "fleet-source-reader",
        "pages_crawled": len(pages),
        "total_issues": len(issues),
        "orphan_pages": len(orphans),
        "avg_depth": (sum(p["depth"] for p in pages) / len(pages)) if pages else 0,
        "avg_word_count": int(sum(p["word_count"] for p in pages) / len(pages)) if pages else 0,
        "pages_with_schema": sum(1 for p in pages if p["schemas"]) if schemas_present else 0,
        "pages_with_multimodal": sum(1 for p in pages if p["has_multimodal"]),
        "pages_with_comparison_table": sum(1 for p in pages if p["has_comparison_table"]),
        "pages_with_video": sum(1 for p in pages if p["video_count"] > 0),
        "pages_over_2000_words": sum(1 for p in pages if p["word_count"] > 2000),
        "images_missing_alt": sum(p["image_count"] - p["images_with_alt"] for p in pages),
        "pages_with_date": sum(1 for p in pages if p["last_modified"]),
        "crawler_access": crawler_access_from_robots(repo),
        "social_links": {},
        "topic_clusters": build_topic_clusters(pages),
        "topic_cluster_count": len(build_topic_clusters(pages)),
        "term_consistency": term_consistency(pages),
        "content_freshness": content_freshness(pages),
        "redirect_stubs": 0,
        "pages": pages,
        "links": links[:5000],
        "issues": issues,
        "orphans": orphans[:50],
        "tree": build_tree(pages),
        "positive_signals": positive_signals(pages),
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = []
    for slug, conf in FLEET.items():
        try:
            data = read_site(slug, conf)
            out = OUTPUT_DIR / f"crawl_{slug}.json"
            out.write_text(json.dumps(data, indent=2))
            summary.append((slug, data["pages_crawled"], data["pages_with_schema"], data["avg_word_count"]))
            print(f"  {slug:24s} {data['pages_crawled']:4d} pages | schema {data['pages_with_schema']:4d} | avg {data['avg_word_count']:4d} words")
        except Exception as e:
            print(f"  {slug}: ERROR {e}")
    print(f"\n  → wrote {len(summary)} site JSONs to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
