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
from collections import defaultdict

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
        if p["internal_links_in"] >= 5:
            positive.append({"type": "well_linked", "url": p["url"], "detail": f"{p['internal_links_in']} internal links pointing here"})

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
        "pages": pages,
        "links": all_links[:2000],  # Cap for file size
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
