#!/usr/bin/env python3
"""
Crawl client sites and extract SEO data.
Outputs JSON for the dashboard: pages, links, issues, site tree.
"""

import json
import os
import sys
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
from collections import defaultdict, Counter
import re

import requests
from bs4 import BeautifulSoup

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")

SITES = {
    "rank4ai": {
        "url": "https://www.rank4ai.co.uk",
        "max_pages": 300,
        "sitemap": "https://www.rank4ai.co.uk/sitemap-0.xml",
    },
    "market-invoice": {
        "url": "https://www.marketinvoice.co.uk",
        "max_pages": 300,
        "sitemap": "https://marketinvoice.co.uk/sitemap-0.xml",
    },
    "seocompare": {
        "url": "https://www.seocompare.co.uk",
        "max_pages": 300,
    },
}

HEADERS = {
    "User-Agent": "Rank4AI-Dashboard-Crawler/1.0 (+https://rank4ai.co.uk)"
}


def crawl_site(site_id, config):
    base_url = config["url"]
    max_pages = config["max_pages"]
    domain = urlparse(base_url).netloc

    visited = set()
    to_visit = [base_url]
    pages = []
    all_links = []
    issues = []

    # Seed from sitemap if available
    sitemap_url = config.get("sitemap")
    if sitemap_url:
        try:
            print(f"Fetching sitemap: {sitemap_url}")
            resp = requests.get(sitemap_url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                import re as sitemap_re
                urls = sitemap_re.findall(r'<loc>(.*?)</loc>', resp.text)
                to_visit = list(set(urls))
                print(f"  Found {len(to_visit)} URLs in sitemap")
        except Exception as e:
            print(f"  Sitemap error: {e}")

    print(f"Crawling {base_url} (max {max_pages} pages)...")

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)

        # Normalize
        url = url.split("#")[0].split("?")[0]
        if url in visited:
            continue

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
            visited.add(url)
        except Exception as e:
            issues.append({"url": url, "type": "error", "detail": str(e)[:100]})
            visited.add(url)
            continue

        status = resp.status_code
        if status >= 400:
            issues.append({"url": url, "type": "broken", "detail": f"HTTP {status}"})
            continue

        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract page data
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        h1_tags = soup.find_all("h1")
        h1 = h1_tags[0].get_text(strip=True) if h1_tags else ""
        h1_count = len(h1_tags)

        meta_desc_tag = soup.find("meta", attrs={"name": "description"})
        meta_desc = meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""

        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        canonical = canonical_tag.get("href", "") if canonical_tag else ""

        # Schema detection
        schemas = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict) and "@type" in item:
                        t = item["@type"]
                        if isinstance(t, list):
                            schemas.extend([str(x) for x in t])
                        else:
                            schemas.append(str(t))
            except:
                pass

        # Word count (visible text)
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        word_count = len(text.split())

        # Links
        internal_links = []
        external_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            full_url = urljoin(url, href).split("#")[0].split("?")[0]
            link_domain = urlparse(full_url).netloc

            if link_domain == domain or link_domain == "www." + domain or "www." + link_domain == domain:
                internal_links.append(full_url)
                if full_url not in visited and full_url not in to_visit:
                    to_visit.append(full_url)
            else:
                external_links.append(full_url)

        # Record links
        for link in internal_links:
            all_links.append({"from": url, "to": link, "type": "internal"})
        for link in external_links[:10]:  # Cap external links per page
            all_links.append({"from": url, "to": link, "type": "external"})

        # Issues
        if not title:
            issues.append({"url": url, "type": "missing_title", "detail": "No title tag"})
        if not h1:
            issues.append({"url": url, "type": "missing_h1", "detail": "No H1 tag"})
        if h1_count > 1:
            issues.append({"url": url, "type": "multiple_h1", "detail": f"{h1_count} H1 tags"})
        if not meta_desc:
            issues.append({"url": url, "type": "missing_meta_desc", "detail": "No meta description"})
        if word_count < 100:
            issues.append({"url": url, "type": "thin_content", "detail": f"Only {word_count} words"})

        # Multi-modal content detection
        images = soup.find_all("img")
        image_count = len(images)
        images_with_alt = sum(1 for img in images if img.get("alt", "").strip())
        videos = soup.find_all(["video", "iframe"])
        video_count = sum(1 for v in videos if "youtube" in str(v).lower() or "vimeo" in str(v).lower() or v.name == "video")
        has_multimodal = image_count > 0 and (video_count > 0 or image_count >= 3)

        # Comparison tables
        tables = soup.find_all("table")
        has_comparison_table = any(
            len(t.find_all("tr")) >= 3 and len(t.find_all("th")) >= 2
            for t in tables
        )

        # Content freshness (from meta tags or schema)
        last_modified = None
        date_meta = soup.find("meta", attrs={"property": "article:modified_time"}) or \
                     soup.find("meta", attrs={"name": "last-modified"}) or \
                     soup.find("meta", attrs={"property": "article:published_time"})
        if date_meta:
            last_modified = date_meta.get("content", "")[:10]

        # Lists count for AI structure
        lists = soup.find_all(["ul", "ol"])
        list_count = len(lists)

        # H2 questions (AI-friendly headings)
        h2s = soup.find_all("h2")
        question_h2s = sum(1 for h in h2s if "?" in h.get_text())

        page = {
            "url": url,
            "path": urlparse(url).path or "/",
            "title": title[:120],
            "h1": h1[:120],
            "meta_desc": meta_desc[:200],
            "word_count": word_count,
            "status": status,
            "schemas": schemas,
            "internal_links_out": len(internal_links),
            "external_links_out": len(external_links[:10]),
            "canonical": canonical,
            "response_time_ms": int(resp.elapsed.total_seconds() * 1000),
            "image_count": image_count,
            "images_with_alt": images_with_alt,
            "video_count": video_count,
            "has_multimodal": has_multimodal,
            "has_comparison_table": has_comparison_table,
            "table_count": len(tables),
            "list_count": list_count,
            "question_h2s": question_h2s,
            "h2_count": len(h2s),
            "last_modified": last_modified,
        }
        pages.append(page)

        # Be polite
        time.sleep(0.3)

        if len(visited) % 20 == 0:
            print(f"  ...crawled {len(visited)} pages")

    # Calculate incoming links
    incoming = defaultdict(int)
    for link in all_links:
        if link["type"] == "internal":
            incoming[link["to"]] += 1

    for page in pages:
        page["internal_links_in"] = incoming.get(page["url"], 0)

    # Find orphan pages (no incoming internal links, not homepage)
    orphans = [p["url"] for p in pages if p["internal_links_in"] == 0 and p["path"] != "/"]

    # Build site tree
    tree = build_tree(pages)

    # Calculate link depth (BFS from homepage)
    depths = calculate_depth(pages, all_links, base_url)
    for page in pages:
        page["depth"] = depths.get(page["url"], 99)

    # Positive signals
    positive = []
    for p in pages:
        if p["schemas"]:
            positive.append({"type": "schema", "url": p["url"], "detail": f"Has {', '.join(p['schemas'])} schema"})
        if p["word_count"] >= 500:
            positive.append({"type": "good_content", "url": p["url"], "detail": f"{p['word_count']} words"})
        if p["word_count"] >= 2000:
            positive.append({"type": "long_content", "url": p["url"], "detail": f"{p['word_count']} words — 3x more likely to be cited"})
        if p["internal_links_in"] >= 5:
            positive.append({"type": "well_linked", "url": p["url"], "detail": f"{p['internal_links_in']} internal links pointing here"})
        if p.get("has_multimodal"):
            positive.append({"type": "multimodal", "url": p["url"], "detail": f"{p['image_count']} images + {p['video_count']} videos — +156-317% citation rate"})
        if p.get("has_comparison_table"):
            positive.append({"type": "comparison_table", "url": p["url"], "detail": "Has comparison table — 2.5x citation rate"})
        if p.get("question_h2s", 0) >= 2:
            positive.append({"type": "faq_structure", "url": p["url"], "detail": f"{p['question_h2s']} question headings — AI-friendly structure"})

    # ── Multi-crawler access test (do bots get 200?) ──
    crawler_access = {}
    bot_uas = {
        "GPTBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.0; +https://openai.com/gptbot)",
        "ClaudeBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +https://www.anthropic.com)",
        "PerplexityBot": "Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai)",
        "Googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Bingbot": "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        "Browser": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }
    print("  Testing crawler access...")
    for bot_name, ua in bot_uas.items():
        try:
            r = requests.get(base_url, headers={"User-Agent": ua}, timeout=10, allow_redirects=True)
            crawler_access[bot_name] = {"status": r.status_code, "accessible": r.status_code == 200}
        except Exception as e:
            crawler_access[bot_name] = {"status": 0, "accessible": False, "error": str(e)[:50]}

    # ── Social links aggregation ──
    social_patterns = {
        "linkedin": r"linkedin\.com/(?:company|in)/[^\"'\s]+",
        "twitter": r"(?:twitter|x)\.com/[^\"'\s]+",
        "youtube": r"youtube\.com/(?:channel|c|@|user)/[^\"'\s]+",
        "facebook": r"facebook\.com/[^\"'\s]+",
        "instagram": r"instagram\.com/[^\"'\s]+",
        "tiktok": r"tiktok\.com/@[^\"'\s]+",
        "github": r"github\.com/[^\"'\s]+",
    }
    social_links = {}
    all_html = " ".join(p.get("_html", "") for p in pages if p.get("_html"))
    # Use the first few pages HTML if available, otherwise check links
    for platform, pattern in social_patterns.items():
        found = set()
        for link in all_links:
            url_str = link.get("to", "")
            if re.search(pattern, url_str, re.IGNORECASE):
                found.add(url_str)
        if found:
            social_links[platform] = list(found)[:3]

    # ── Topic cluster detection ──
    topic_clusters = {}
    for p in pages:
        parts = [x for x in p.get("path", "/").split("/") if x]
        if len(parts) >= 2:
            cluster = parts[0]
            if cluster not in topic_clusters:
                topic_clusters[cluster] = {"hub": f"/{cluster}/", "pages": []}
            topic_clusters[cluster]["pages"].append(p["path"])
    # Only keep clusters with 3+ pages
    topic_clusters = {k: v for k, v in topic_clusters.items() if len(v["pages"]) >= 3}

    # ── Terminology consistency (H1 word analysis) ──
    h1_words = Counter()
    for p in pages:
        h1 = p.get("h1", "").lower()
        words = re.findall(r'\b[a-z]{4,}\b', h1)
        meaningful = [w for w in words if w not in {"the", "and", "for", "with", "from", "this", "that", "your", "about", "what", "how", "does", "page", "home"}]
        h1_words.update(meaningful)
    top_terms = h1_words.most_common(20)
    # Check consistency: are the same terms used across many pages?
    total_h1s = len([p for p in pages if p.get("h1")])
    term_consistency = {}
    for term, count in top_terms[:10]:
        term_consistency[term] = {"count": count, "pct": round(count / max(total_h1s, 1) * 100, 1)}

    # ── Content freshness summary ──
    from datetime import datetime as dt
    pages_with_dates = [p for p in pages if p.get("last_modified")]
    fresh_30 = 0
    fresh_90 = 0
    stale = 0
    now = dt.now()
    for p in pages_with_dates:
        try:
            mod_date = dt.strptime(p["last_modified"][:10], "%Y-%m-%d")
            days_old = (now - mod_date).days
            if days_old <= 30:
                fresh_30 += 1
            elif days_old <= 90:
                fresh_90 += 1
            else:
                stale += 1
        except:
            pass

    result = {
        "site_id": site_id,
        "domain": domain,
        "crawled_at": datetime.now().isoformat(),
        "pages_crawled": len(pages),
        "total_issues": len(issues),
        "orphan_pages": len(orphans),
        "avg_depth": round(sum(p.get("depth", 0) for p in pages) / max(len(pages), 1), 1),
        "avg_word_count": round(sum(p["word_count"] for p in pages) / max(len(pages), 1)),
        "pages_with_schema": sum(1 for p in pages if p["schemas"]),
        "pages_with_multimodal": sum(1 for p in pages if p.get("has_multimodal")),
        "pages_with_comparison_table": sum(1 for p in pages if p.get("has_comparison_table")),
        "pages_with_video": sum(1 for p in pages if p.get("video_count", 0) > 0),
        "pages_over_2000_words": sum(1 for p in pages if p["word_count"] >= 2000),
        "images_missing_alt": sum(p.get("image_count", 0) - p.get("images_with_alt", 0) for p in pages),
        "pages_with_date": sum(1 for p in pages if p.get("last_modified")),
        "crawler_access": crawler_access,
        "social_links": social_links,
        "topic_clusters": {k: {"hub": v["hub"], "page_count": len(v["pages"])} for k, v in list(topic_clusters.items())[:20]},
        "topic_cluster_count": len(topic_clusters),
        "term_consistency": term_consistency,
        "content_freshness": {
            "pages_with_dates": len(pages_with_dates),
            "fresh_30_days": fresh_30,
            "fresh_90_days": fresh_90,
            "stale": stale,
        },
        "pages": pages,
        "links": all_links[:2000],
        "issues": issues,
        "orphans": orphans,
        "tree": tree,
        "positive_signals": positive[:100],
    }

    return result


def build_tree(pages):
    """Build a hierarchical tree from URL paths."""
    tree = {"name": "/", "path": "/", "children": []}

    for page in sorted(pages, key=lambda p: p["path"]):
        parts = [p for p in page["path"].split("/") if p]
        node = tree
        current_path = ""
        for part in parts:
            current_path += f"/{part}"
            child = next((c for c in node["children"] if c["name"] == part), None)
            if not child:
                child = {"name": part, "path": current_path, "children": []}
                node["children"].append(child)
            node = child

    return tree


def calculate_depth(pages, links, start_url):
    """BFS from homepage to calculate link depth."""
    depths = {start_url: 0}
    queue = [start_url]
    internal_links = defaultdict(set)

    for link in links:
        if link["type"] == "internal":
            internal_links[link["from"]].add(link["to"])

    while queue:
        current = queue.pop(0)
        current_depth = depths[current]
        for linked in internal_links.get(current, []):
            if linked not in depths:
                depths[linked] = current_depth + 1
                queue.append(linked)

    return depths


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for site_id, config in SITES.items():
        try:
            result = crawl_site(site_id, config)
            output_file = os.path.join(OUTPUT_DIR, f"crawl_{site_id}.json")
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2)
            print(f"Saved {result['pages_crawled']} pages for {site_id} → {output_file}")
        except Exception as e:
            print(f"Error crawling {site_id}: {e}")

    print("Done.")


if __name__ == "__main__":
    main()
