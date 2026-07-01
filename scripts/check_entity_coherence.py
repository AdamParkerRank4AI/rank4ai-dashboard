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

DATA = Path(__file__).resolve().parent.parent / "src" / "data"
LIVE = DATA / "live"
OUT = LIVE / "entity_coherence.json"
CLIENTS = DATA / "clients.json"
ENTITY_STACK = DATA / "entity_stack.json"

# Homepages that differ from "https://<domain>" (www, scheme, sub-path).
URL_OVERRIDES = {
    "rank4ai": "https://www.rank4ai.co.uk",
    "rochellemarashi": "https://rochellemarashi.pages.dev",
}

# Fallback if clients.json can't be read.
SITES = [
    {"id": "rank4ai", "url": "https://www.rank4ai.co.uk"},
    {"id": "market-invoice", "url": "https://marketinvoice.co.uk"},
    {"id": "seocompare", "url": "https://seocompare.co.uk"},
    {"id": "rochellemarashi", "url": "https://rochellemarashi.pages.dev"},
]


def build_sites():
    """Derive the site list (id + homepage) from clients.json, keeping overrides."""
    try:
        clients = json.load(open(CLIENTS))
    except Exception as e:
        print(f"  clients.json unreadable ({e}); using fallback SITES")
        return SITES
    sites, seen = [], set()
    for c in clients:
        cid = c.get("id")
        domain = (c.get("liveDomain") or c.get("domain") or "").strip()
        if not cid or not domain:
            continue
        url = URL_OVERRIDES.get(cid) or ("https://" + domain.split("/")[0])
        sites.append({"id": cid, "url": url})
        seen.add(cid)
    if "rochellemarashi" not in seen:
        sites.append({"id": "rochellemarashi", "url": URL_OVERRIDES["rochellemarashi"]})
    return sites


def load_entity_stack():
    """Return {client_id: [ {place, url, priority, status}, ... ]} for rows with a URL."""
    try:
        raw = json.load(open(ENTITY_STACK))
    except Exception:
        return {}
    out = {}
    for key, brand in raw.items():
        if key.startswith("_") or not isinstance(brand, dict):
            continue
        rows = []
        for p in brand.get("platforms", []):
            u = (p.get("url") or "").strip()
            if u:
                rows.append({"place": p.get("place"), "url": u,
                             "priority": p.get("priority"), "status": p.get("status")})
        out[key] = rows
    return out


def norm_url(u):
    if not u:
        return ""
    u = u.strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


def _orig_from_entities(n, entities):
    for role in ("person", "organization"):
        for e in entities.get(role, []):
            for s in e.get("sameAs", []):
                if norm_url(s) == n:
                    return s
    return n


def build_ecosystem(entities, stack_rows, live_lookup):
    """Cross-check entity_stack profile URLs against on-site schema.org sameAs.
    Emits per-URL {url, place, in_stack, in_sameas, live, http_status, verdict}."""
    sameas = set()
    for role in ("person", "organization"):
        for e in entities.get(role, []):
            for s in e.get("sameAs", []):
                sameas.add(norm_url(s))

    stack_by_norm = {norm_url(r["url"]): r for r in stack_rows}
    profiles = []
    for n in sorted(set(stack_by_norm) | sameas):
        in_stack = n in stack_by_norm
        in_sameas = n in sameas
        url = stack_by_norm[n]["url"] if in_stack else _orig_from_entities(n, entities)
        res = live_lookup.get(n)
        if res is None:
            res = head_check(url)
            live_lookup[n] = res
        live = res["verdict"] in ("ok", "bot_blocked")  # bot_blocked = presumed live
        if in_sameas and not live:
            verdict = "dead"
        elif in_stack and not in_sameas:
            verdict = "missing_from_sameas"
        elif in_sameas and not in_stack:
            verdict = "in_sameas_not_stack"
        else:
            verdict = "ok"
        profiles.append({
            "url": url, "place": stack_by_norm.get(n, {}).get("place"),
            "in_stack": in_stack, "in_sameas": in_sameas, "live": live,
            "http_status": res["status"], "verdict": verdict,
        })

    return {
        "profiles": profiles,
        "summary": {
            "stack_total": len(stack_rows),
            "sameas_total": len(sameas),
            "matched": sum(1 for p in profiles if p["in_stack"] and p["in_sameas"]),
            "missing_from_sameas": sum(1 for p in profiles if p["verdict"] == "missing_from_sameas"),
            "dead_in_sameas": sum(1 for p in profiles if p["verdict"] == "dead" and p["in_sameas"]),
        },
    }

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
    except (HTTPError, URLError, TimeoutError, OSError) as e:
        # OSError catches socket.timeout, which on Python 3.9 is NOT a
        # TimeoutError subclass and otherwise crashes the whole run.
        print(f"  fetch failed {url}: {e}")
        return None


# Platforms that block automated checks but typically have valid URLs.
# These are reported as "bot_blocked" (warning, not broken).
BOT_BLOCKED_HOSTS = (
    "linkedin.com", "x.com", "twitter.com", "medium.com",
    "instagram.com", "facebook.com", "tiktok.com", "quora.com",
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
        except (URLError, TimeoutError, OSError) as e:
            # OSError also catches socket.timeout (not a TimeoutError on 3.9).
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


def check_site(site: dict, stack_rows: list = None) -> dict:
    stack_rows = stack_rows or []
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
            "ecosystem": build_ecosystem({}, stack_rows, {}),
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

    # Reuse the sameAs HEAD results so stack∩sameAs URLs aren't fetched twice.
    live_lookup = {}
    for lst in (person_links, organization_links):
        for r in lst:
            live_lookup[norm_url(r["url"])] = r

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
        "ecosystem": build_ecosystem(entities, stack_rows, live_lookup),
    }


def main() -> int:
    out = {}
    stack = load_entity_stack()
    fleet = {"total": 0, "ok": 0, "broken": 0, "bot_blocked": 0, "error": 0}
    for site in build_sites():
        result = check_site(site, stack.get(site["id"], []))
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
