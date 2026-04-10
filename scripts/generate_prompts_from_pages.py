#!/usr/bin/env python3
"""
Generate citation prompts from site pages.
Each page's H1/title becomes a prompt mapped to that URL.
Merges with existing manual/GSC/SERP prompts.
"""
import json
import os
import re
from urllib.parse import urlparse

LIVE_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
OUTPUT = os.path.join(LIVE_DIR, "citation_prompts.json")

# Modifiers to expand key pages into prompt variations
MODIFIERS = ["best", "top", "top 5", "top 10", "compare", "recommended", "cheapest", "reviewed"]
GEOGRAPHIES = ["UK", "London", "Manchester", "near me"]

# Category words that indicate a page targets a specific vertical
CATEGORY_WORDS = ["agencies", "companies", "firms", "providers", "tools", "services", "consultants", "brokers"]


def extract_core_topic(h1):
    """Extract the core topic from an H1, stripping modifiers and dates."""
    h1_lower = h1.lower().strip()
    # Remove common prefixes
    for prefix in ["best ", "top ", "top 5 ", "top 10 ", "compare ", "the ", "a guide to ", "guide to "]:
        if h1_lower.startswith(prefix):
            h1_lower = h1_lower[len(prefix):]
    # Remove year suffixes
    import re
    h1_lower = re.sub(r'\s*\d{4}\s*$', '', h1_lower)
    # Remove trailing geography
    for geo in ["uk", "london", "manchester", "birmingham", "near me"]:
        if h1_lower.endswith(f" {geo}"):
            h1_lower = h1_lower[:-len(geo)-1]
    return h1_lower.strip()


def generate_modifier_variants(h1, path):
    """Generate prompt variations using the modifier grid for key pages."""
    variants = []
    core_topic = extract_core_topic(h1)

    if not core_topic or len(core_topic) < 5:
        return []

    # Skip if core topic looks like a CTA rather than a category
    skip_words = ["get free", "start", "sign up", "contact", "request", "apply"]
    if any(w in core_topic.lower() for w in skip_words):
        return []

    # Only generate variants for industry/comparison/best-of pages
    path_lower = path.lower()
    h1_lower = h1.lower()
    is_expandable = (
        "/best/" in path_lower or
        any(word in h1_lower for word in ["best", "top", "compare", "leading", "cheapest"])
    )

    if not is_expandable:
        return []

    # Generate: modifier + core_topic + geography
    for modifier in MODIFIERS[:5]:  # Limit to top 5 modifiers
        # Skip if H1 already starts with this modifier
        if h1_lower.startswith(modifier):
            continue
        variant = f"{modifier} {core_topic}"
        variants.append(variant)

    # Add geography variants for the top modifier only
    for geo in GEOGRAPHIES[:2]:  # UK + London only
        if geo.lower() not in h1_lower:
            variants.append(f"best {core_topic} {geo}")

    return variants


def classify_prompt_type(h1, path):
    """Classify what type of prompt this is."""
    h1_lower = h1.lower()
    if h1_lower.startswith("how") or "how do" in h1_lower or "how to" in h1_lower:
        return "how_to"
    if "?" in h1 or h1_lower.startswith("what") or h1_lower.startswith("why") or h1_lower.startswith("can") or h1_lower.startswith("do") or h1_lower.startswith("is") or h1_lower.startswith("will") or h1_lower.startswith("should"):
        return "question"
    if "vs" in h1_lower or "versus" in h1_lower or "compared" in h1_lower or "difference" in h1_lower:
        return "comparison"
    if "best" in h1_lower or "top" in h1_lower:
        return "industry"
    if "/blog/" in path:
        return "question"
    if "/guides/" in path or "/guide" in path:
        return "how_to"
    if "/compare/" in path:
        return "comparison"
    if "/providers/" in path or "/best/" in path:
        return "industry"
    if "/locations/" in path:
        return "local"
    if "/industries/" in path:
        return "industry"
    return "question"


def classify_intent(prompt_type, path):
    """Is this high intent or discovery?"""
    if prompt_type in ["industry", "recommendation", "local", "cost", "problem"]:
        return "high_intent"
    if "/best/" in path or "/compare/" in path or "/providers/" in path:
        return "high_intent"
    return "discovery"


def generate_for_client(client_id):
    """Generate prompts from crawl data + merge with existing."""
    crawl_file = os.path.join(LIVE_DIR, f"crawl_{client_id}.json")
    if not os.path.exists(crawl_file):
        return None

    with open(crawl_file) as f:
        crawl = json.load(f)

    # Load existing prompts
    existing = {}
    if os.path.exists(OUTPUT):
        with open(OUTPUT) as f:
            all_prompts = json.load(f)
        existing = all_prompts.get(client_id, {})

    # Existing prompt queries (to avoid duplicates) — but NOT from faq
    existing_queries = set()
    for group in ["high_intent", "discovery"]:
        for p in existing.get(group, []):
            existing_queries.add(p["query"].lower().strip())
    # Don't count existing FAQs as duplicates — we want to re-sort them


    # Generate from pages
    page_prompts = {"high_intent": [], "discovery": [], "faq": []}
    seen_queries = set(existing_queries)

    for page in crawl.get("pages", []):
        h1 = page.get("h1", "").strip()
        title = page.get("title", "").strip()
        path = page.get("path", "/")
        url = page.get("url", "")

        # Skip if no useful H1
        if not h1 or len(h1) < 10 or h1.lower() in ["home", "homepage"]:
            continue

        # Skip utility pages
        skip_paths = ["/cookies", "/privacy", "/terms", "/contact", "/disclaimer", "/404", "/preview/"]
        if any(s in path.lower() for s in skip_paths):
            continue

        # The H1 itself is a prompt
        query = h1
        if query.lower().strip() in seen_queries:
            continue
        seen_queries.add(query.lower().strip())

        prompt_type = classify_prompt_type(h1, path)

        # Genuine questions (with ?) go to FAQ section
        is_faq = "?" in h1 and not any(w in h1.lower() for w in ["best", "top", "top 5", "top 10", "compare", "rated", "recommended"])

        if is_faq:
            group = "faq"
        else:
            group = classify_intent(prompt_type, path)

        prompt_id = f"{client_id}-page-{len(seen_queries)}"

        prompt = {
            "id": prompt_id,
            "type": prompt_type,
            "query": query,
            "source": "page",
            "page_url": path,
            "word_count": page.get("word_count", 0),
            "has_schema": bool(page.get("schemas")),
        }

        page_prompts[group].append(prompt)

        # Generate modifier variants for key pages
        variants = generate_modifier_variants(h1, path)
        for variant in variants:
            v_lower = variant.lower().strip()
            if v_lower in seen_queries:
                continue
            seen_queries.add(v_lower)
            v_id = f"{client_id}-var-{len(seen_queries)}"
            page_prompts["high_intent"].append({
                "id": v_id,
                "type": "industry",
                "query": variant,
                "source": "modifier",
                "page_url": path,
            })

    # Merge: existing first, then page-generated
    merged = {
        "high_intent": list(existing.get("high_intent", [])) + page_prompts["high_intent"],
        "discovery": list(existing.get("discovery", [])) + page_prompts["discovery"],
        "faq": list(existing.get("faq", [])) + page_prompts["faq"],
    }

    # Deduplicate by query
    for group in ["high_intent", "discovery", "faq"]:
        seen = set()
        unique = []
        for p in merged[group]:
            q = p["query"].lower().strip()
            if q not in seen:
                seen.add(q)
                unique.append(p)
        merged[group] = unique

    # Re-sort: move genuine questions from discovery/high_intent to faq
    stuffing_words = ["best", "top", "top 5", "top 10", "compare", "rated", "recommended", "leading", "affordable", "which", "should i use", "can you recommend"]
    for group in ["high_intent", "discovery"]:
        keep = []
        for p in merged[group]:
            q = p["query"]
            is_genuine_q = "?" in q and not any(w in q.lower() for w in stuffing_words)
            if is_genuine_q:
                merged["faq"].append(p)
            else:
                keep.append(p)
        merged[group] = keep

    # Deduplicate faq
    seen = set()
    unique = []
    for p in merged["faq"]:
        q = p["query"].lower().strip()
        if q not in seen:
            seen.add(q)
            unique.append(p)
    merged["faq"] = unique

    return merged


def main():
    # Load existing
    if os.path.exists(OUTPUT):
        with open(OUTPUT) as f:
            all_prompts = json.load(f)
    else:
        all_prompts = {}

    for client_id in ["rank4ai", "market-invoice", "seocompare"]:
        print(f"\n{client_id}:")
        result = generate_for_client(client_id)
        if result:
            all_prompts[client_id] = result
            hi = len(result["high_intent"])
            di = len(result["discovery"])
            page_hi = sum(1 for p in result["high_intent"] if p.get("source") == "page")
            page_di = sum(1 for p in result["discovery"] if p.get("source") == "page")
            print(f"  High intent: {hi} ({page_hi} from pages)")
            print(f"  Discovery: {di} ({page_di} from pages)")
            print(f"  Total: {hi + di}")

    with open(OUTPUT, "w") as f:
        json.dump(all_prompts, f, indent=2)
    print(f"\nSaved → {OUTPUT}")


if __name__ == "__main__":
    main()
