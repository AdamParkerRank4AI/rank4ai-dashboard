#!/usr/bin/env python3
"""
Extract entities and topics from crawled pages — no Google NLP API needed.
Parses HTML directly to find what each site is about.
"""
import json
import os
import re
from collections import Counter
from datetime import datetime

from bs4 import BeautifulSoup

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")

# Common stop words to filter out
STOP_WORDS = set("the a an is are was were be been being have has had do does did will would shall should may might can could of in to for on with at by from as into through during before after above below between out off over under again further then once here there when where why how all each every both few more most other some such no nor not only own same so than too very just don about also back even still way many our get your".split())


def extract_from_crawl(client_id):
    """Extract entities from crawled page data."""
    crawl_file = os.path.join(OUTPUT_DIR, f"crawl_{client_id}.json")
    if not os.path.exists(crawl_file):
        return None

    with open(crawl_file) as f:
        crawl = json.load(f)

    all_titles = []
    all_h1s = []
    all_h2s = []
    all_schemas = []
    word_freq = Counter()
    bigram_freq = Counter()
    page_topics = []

    for page in crawl.get("pages", []):
        title = page.get("title", "")
        h1 = page.get("h1", "")
        schemas = page.get("schemas", [])

        if title:
            all_titles.append(title)
        if h1:
            all_h1s.append(h1)
        all_schemas.extend(schemas)

        # Extract meaningful words from titles and H1s
        for text in [title, h1]:
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            meaningful = [w for w in words if w not in STOP_WORDS]
            word_freq.update(meaningful)

            # Bigrams
            for i in range(len(meaningful) - 1):
                bigram = f"{meaningful[i]} {meaningful[i+1]}"
                bigram_freq[bigram] += 1

    # Top single words (entities/topics)
    top_words = word_freq.most_common(30)

    # Top bigrams (phrases)
    top_bigrams = [(b, c) for b, c in bigram_freq.most_common(30) if c >= 2]

    # Schema types used
    schema_counts = Counter(all_schemas)

    # Categorise pages by URL pattern
    categories = {}
    for page in crawl.get("pages", []):
        path = page.get("path", "/")
        parts = [p for p in path.split("/") if p]
        if parts:
            cat = parts[0]
            categories[cat] = categories.get(cat, 0) + 1

    top_categories = sorted(categories.items(), key=lambda x: -x[1])[:15]

    return {
        "analyzed_at": datetime.now().isoformat(),
        "pages_analyzed": len(crawl.get("pages", [])),
        "top_topics": [{"word": w, "count": c} for w, c in top_words[:20]],
        "top_phrases": [{"phrase": b, "count": c} for b, c in top_bigrams[:15]],
        "schema_types": [{"type": t, "count": c} for t, c in schema_counts.most_common()],
        "url_categories": [{"category": cat, "pages": count} for cat, count in top_categories],
        "total_schemas": len(all_schemas),
        "unique_schema_types": len(schema_counts),
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_results = {}
    for client_id in ["rank4ai", "market-invoice", "seocompare"]:
        print(f"\n{client_id}:")
        result = extract_from_crawl(client_id)
        if result:
            all_results[client_id] = result
            print(f"  Pages: {result['pages_analyzed']}")
            print(f"  Top topics: {[t['word'] for t in result['top_topics'][:5]]}")
            print(f"  Top phrases: {[t['phrase'] for t in result['top_phrases'][:5]]}")
            print(f"  Schema types: {[s['type'] for s in result['schema_types'][:5]]}")
            print(f"  URL categories: {[c['category'] for c in result['url_categories'][:5]]}")
        else:
            print(f"  No crawl data found")

    output_file = os.path.join(OUTPUT_DIR, "nlp_entities.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
