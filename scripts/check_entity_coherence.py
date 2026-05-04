#!/usr/bin/env python3
"""
Entity coherence check (Batch 5).

Fetches each fleet site's homepage, parses JSON-LD @graph, extracts every
sameAs URL from Person + Organization entries, and HEAD-checks each one.

Output: src/data/live/entity_coherence.json
Schema:
  {
    "<site_id>": {
      "site_url": "...",
      "fetched_at": "...",
      "person_links": [{"name": str, "url": str, "status": int, "ok": bool, "redirect_to": str|None}],
      "organization_links": [...],
      "summary": {"total": N, "ok": N, "broken": N, "rate_limited": N, "score": 0-100},
      "broken_detail": [{"url": str, "status": int, "from_entity": str, "from_role": str}]
    },
    "fleet_summary": {"total": N, "ok": N, "broken": N}
  }

Designed to run weekly (sameAs URLs do not change often). Wired into refresh_all.py.
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LIVE = Path(__file__).resolve().parent.parent / "src" / "data" / "live"
OUT = LIVE / "entity_coherence.json"

SITES = [
    {"id": "rank4ai", "url": "https://www.rank4ai.co.uk"},
    {"id": "market-invoice", "url": "https://marketinvoice.co.uk"},
    {"id": "seocompare", "url": "https://seocompare.co.uk"},
    {"id": "rochellemarashi", "url": "https://rochellemarashi.pages.dev"},
]

USER_AGENT = "Rank4AI-EntityCoherenceChecker/1.0 (+https://rank4ai.co.uk)"
TIMEOUT = 15
JSONLD_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.+?)</script>',
    re.DOTALL,
)


def fetch_html(url):
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
        with urlopen(req, timeout=TIMEOUT) as r:
            return r.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as e:
        print(f"  fetch failed {url}: {e}")
        return None


# Platforms that block automated checks but typically have valid URLs.
# These are reported as "bot_blocked" (warning, not broken).
BOT_BLOCKED_HOSTS = (
    "linkedin.com", "x.com", "twitter.com", "medium.com",
    "instagram.com", "facebook.com", "tiktok.com",
    "counselling-directory.org.uk", "psychologytoday.com",
)


def classify(status, host):
    """Return one of: ok | broken | bot_blocked | error."""
    if 200 <= status < 400:
        return "ok"
    if status in (403, 429, 999):
        for h in BOT_BLOCKED_HOSTS:
            if h in host:
                return "bot_blocked"
        return "broken"
    if status in (0, None):
        return "error"
    return "broken"  # 404, 410, 5xx, etc.


def head_check(url):
    """HEAD with GET fallback. Reports final status + redirect chain."""
    out = {"url": url, "status": 0, "ok": False, "verdict": "error",
           "redirect_to": None, "final_url": url, "error": None}
    if not url or not url.startswith(("http://", "https://")):
        out["error"] = "invalid url"
        out["verdict"] = "broken"
        return out
    host = url.split("/")[2] if "://" in url else ""
    for method in ("HEAD", "GET"):
        try:
            req = Request(url, method=method, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=TIMEOUT) as r:
                out["status"] = r.status
                out["final_url"] = r.url
                out["verdict"] = classify(r.status, host)
                out["ok"] = out["verdict"] == "ok"
                if r.url != url:
                    out["redirect_to"] = r.url
                return out
        except HTTPError as e:
            out["status"] = e.code
            out["error"] = f"HTTP {e.code}"
            out["verdict"] = classify(e.code, host)
            out["ok"] = False
            if e.code == 405 and method == "HEAD":
                continue
            return out
        except (URLError, TimeoutError) as e:
            out["status"] = 0
            out["error"] = str(e)[:100]
            out["verdict"] = "error"
            out["ok"] = False
            if method == "HEAD":
                continue
            return out
    return out


def extract_jsonld_blocks(html: str) -> list:
    blocks = []
    for m in JSONLD_RE.finditer(html):
        raw = m.group(1).strip()
        try:
            blocks.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return blocks


def collect_entities(blocks: list) -> dict:
    """Return {'person': [{name, sameAs}], 'organization': [{name, sameAs}]}."""
    out = {"person": [], "organization": []}
    for block in blocks:
        graph = block.get("@graph") if isinstance(block, dict) else None
        items = graph if isinstance(graph, list) else [block] if isinstance(block, dict) else []
        for item in items:
            if not isinstance(item, dict):
                continue
            t = item.get("@type")
            types = t if isinstance(t, list) else [t] if t else []
            same_as = item.get("sameAs", []) or []
            if isinstance(same_as, str):
                same_as = [same_as]
            same_as = [s for s in same_as if isinstance(s, str)]
            name = item.get("name", "")
            if any(x in ("Person",) for x in types):
                out["person"].append({"name": name, "sameAs": same_as})
            elif any(x in ("Organization", "LocalBusiness", "ProfessionalService") for x in types):
                out["organization"].append({"name": name, "sameAs": same_as})
    return out


def check_site(site: dict) -> dict:
    url = site["url"]
    print(f"\n→ {site['id']} ({url})")
    html = fetch_html(url)
    if html is None:
        return {
            "site_url": url,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": "could not fetch homepage",
            "person_links": [],
            "organization_links": [],
            "summary": {"total": 0, "ok": 0, "broken": 0, "rate_limited": 0, "score": 0},
            "broken_detail": [],
        }

    blocks = extract_jsonld_blocks(html)
    entities = collect_entities(blocks)

    person_links = []
    organization_links = []
    broken_detail = []
    counts = {"ok": 0, "broken": 0, "bot_blocked": 0, "error": 0}

    for entity_role, target_list in (
        ("person", person_links),
        ("organization", organization_links),
    ):
        for entity in entities[entity_role]:
            for sa_url in entity["sameAs"]:
                result = head_check(sa_url)
                result["entity_name"] = entity["name"]
                result["entity_role"] = entity_role
                target_list.append(result)
                counts[result["verdict"]] = counts.get(result["verdict"], 0) + 1
                if result["verdict"] in ("broken", "error"):
                    broken_detail.append({
                        "url": sa_url,
                        "status": result["status"],
                        "error": result.get("error"),
                        "verdict": result["verdict"],
                        "from_entity": entity["name"],
                        "from_role": entity_role,
                    })
                time.sleep(0.3)  # be nice

    total = sum(counts.values())
    # Score = ok / (total - bot_blocked). Bot-blocked are excluded because they
    # are probably valid URLs we just can't verify automatically.
    verifiable = total - counts["bot_blocked"]
    score = 100 if verifiable == 0 else round(100 * counts["ok"] / verifiable)

    return {
        "site_url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "person_links": person_links,
        "organization_links": organization_links,
        "summary": {
            "total": total,
            "ok": counts["ok"],
            "broken": counts["broken"],
            "bot_blocked": counts["bot_blocked"],
            "error": counts["error"],
            "score": score,
        },
        "broken_detail": broken_detail,
    }


def main() -> int:
    out = {}
    fleet = {"total": 0, "ok": 0, "broken": 0, "bot_blocked": 0, "error": 0}
    for site in SITES:
        result = check_site(site)
        out[site["id"]] = result
        s = result.get("summary") or {}
        for k in ("total", "ok", "broken", "bot_blocked", "error"):
            fleet[k] += s.get(k, 0)

    verifiable = fleet["total"] - fleet["bot_blocked"]
    out["fleet_summary"] = {
        **fleet,
        "score": 100 if verifiable == 0 else round(100 * fleet["ok"] / verifiable),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    LIVE.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n✓ wrote {OUT}")
    fs = out["fleet_summary"]
    print(f"  fleet: {fs['ok']}/{fs['total']} OK · {fs['broken']} broken · {fs['bot_blocked']} bot-blocked ({fs['score']}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
