#!/usr/bin/env python3
"""
llms.txt validator (Batch 9).

Fetches each fleet site's /llms.txt and /llms-full.txt, scores
structure quality 0-100, lists missing sections.

Output: src/data/live/llms_validation.json
Schema:
  {
    "<site_id>": {
      "site_url": "...",
      "fetched_at": "...",
      "llms_txt": {
        "accessible": bool,
        "score": 0-100,
        "size_bytes": N,
        "checks": [{"label": str, "pass": bool}],
        "missing": [str]
      },
      "llms_full_txt": {...}
    },
    "fleet_summary": {"avg_score": N, "all_accessible": bool}
  }
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LIVE = Path(__file__).resolve().parent.parent / "src" / "data" / "live"
OUT = LIVE / "llms_validation.json"

SITES = [
    {"id": "rank4ai", "url": "https://www.rank4ai.co.uk"},
    {"id": "market-invoice", "url": "https://marketinvoice.co.uk"},
    {"id": "seocompare", "url": "https://seocompare.co.uk"},
    {"id": "rochellemarashi", "url": "https://rochellemarashi.pages.dev"},
]

UA = "Rank4AI-LLMSTxt-Validator/1.0"
TIMEOUT = 15


def fetch(url):
    try:
        req = Request(url, headers={"User-Agent": UA})
        with urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as e:
        return getattr(e, "code", 0), ""


def validate_llms_txt(body, full=False):
    """Score 0-100 + per-check breakdown."""
    if not body:
        return {"accessible": False, "score": 0, "size_bytes": 0, "checks": [], "missing": ["file not accessible"]}

    lines = body.split("\n")
    checks = []

    # H1 (`# Name`)
    has_h1 = bool(lines) and lines[0].startswith("# ") and len(lines[0]) > 2
    checks.append({"label": "Starts with H1 (# Name)", "pass": has_h1, "weight": 15})

    # Blockquote intro (`> X is a Y`)
    has_blockquote = any(line.startswith("> ") and len(line) > 5 for line in lines[:20])
    checks.append({"label": "Has entity-function blockquote (> X is a Y)", "pass": has_blockquote, "weight": 15})

    # Section headers (## ...)
    section_count = sum(1 for line in lines if line.startswith("## "))
    has_sections = section_count >= 1
    checks.append({"label": f"Has section headers (## ...) — found {section_count}", "pass": has_sections, "weight": 15})

    # Markdown links
    import re
    links = re.findall(r"\[[^\]]+\]\((https?://[^)]+)\)", body)
    has_links = len(links) >= 3
    checks.append({"label": f"Has 3+ markdown links — found {len(links)}", "pass": has_links, "weight": 15})

    # No BOM
    no_bom = not body.startswith("﻿")
    checks.append({"label": "No UTF-8 BOM", "pass": no_bom, "weight": 5})

    # Size reasonable
    size = len(body.encode("utf-8"))
    if full:
        size_ok = 5000 < size < 5_000_000  # llms-full.txt should be substantial
        size_label = f"Size 5KB-5MB — actual {size//1024}KB"
    else:
        size_ok = 200 < size < 200_000  # llms.txt should be lean
        size_label = f"Size 200B-200KB — actual {size//1024}KB"
    checks.append({"label": size_label, "pass": size_ok, "weight": 10})

    # Has core pages section (## Core Pages or similar)
    core_terms = ["## Core Pages", "## Key Pages", "## Important", "## Pages"]
    has_core = any(term.lower() in body.lower() for term in core_terms)
    checks.append({"label": "Has 'Core Pages' or equivalent section", "pass": has_core, "weight": 10})

    # Has site URL or domain reference in body
    has_site_url = "http" in body[:500] or "://" in body[:500]
    checks.append({"label": "Has site URL near top", "pass": has_site_url, "weight": 5})

    # Recommended: optional sections
    optional_sections = ["## About", "## Author", "## Methodology", "## Disambiguation"]
    optional_present = sum(1 for s in optional_sections if s in body)
    checks.append({"label": f"Optional sections (About / Author / Methodology / Disambiguation) — {optional_present}/4 present", "pass": optional_present >= 1, "weight": 10})

    total_weight = sum(c["weight"] for c in checks)
    earned = sum(c["weight"] for c in checks if c["pass"])
    score = round(100 * earned / total_weight) if total_weight else 0

    return {
        "accessible": True,
        "score": score,
        "size_bytes": size,
        "checks": [{"label": c["label"], "pass": c["pass"]} for c in checks],
        "missing": [c["label"] for c in checks if not c["pass"]],
    }


def check_site(site):
    print(f"\n→ {site['id']} ({site['url']})")

    txt_status, txt_body = fetch(site["url"].rstrip("/") + "/llms.txt")
    full_status, full_body = fetch(site["url"].rstrip("/") + "/llms-full.txt")

    txt_result = validate_llms_txt(txt_body if txt_status == 200 else "", full=False)
    full_result = validate_llms_txt(full_body if full_status == 200 else "", full=True)

    print(f"  llms.txt: {txt_result['score']}/100 ({txt_result['size_bytes']}B)")
    print(f"  llms-full.txt: {full_result['score']}/100 ({full_result['size_bytes']}B)")

    return {
        "site_url": site["url"],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "llms_txt": txt_result,
        "llms_full_txt": full_result,
    }


def main():
    out = {}
    scores = []
    accessible_count = 0
    total_count = 0
    for site in SITES:
        result = check_site(site)
        out[site["id"]] = result
        if result["llms_txt"]["accessible"]:
            scores.append(result["llms_txt"]["score"])
            accessible_count += 1
        total_count += 1

    out["fleet_summary"] = {
        "avg_score": round(sum(scores) / len(scores)) if scores else 0,
        "accessible": accessible_count,
        "total": total_count,
        "all_accessible": accessible_count == total_count,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    LIVE.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n✓ wrote {OUT}")
    print(f"  fleet avg llms.txt score: {out['fleet_summary']['avg_score']}/100")
    return 0


if __name__ == "__main__":
    sys.exit(main())
