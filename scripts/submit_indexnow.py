#!/usr/bin/env python3
"""
Submit URLs to Bing/Yandex via IndexNow API.
Free, unlimited, instant indexing.

Usage:
  python3 submit_indexnow.py rank4ai          # NEW + genuinely-changed urls
  python3 submit_indexnow.py all              # all clients
  python3 submit_indexnow.py all --dry-run    # compute + print, POST nothing
  python3 submit_indexnow.py all --seed       # seed state from sitemaps, POST nothing
  python3 submit_indexnow.py all --force       # re-submit everything (manual, rare)

Change-detection guard (fixes Bing IndexNow over-use, 2026-07-08)
-----------------------------------------------------------------
Sitemap <lastmod> is stamped at BUILD time on this fleet, so every rebuild
re-stamped every page and the old "changed vs lastmod" guard re-pushed the
whole sitemap daily (merchanthq ~800/day, babydata ~210/day, kartapay
~114/day). That is the over-use Bing flagged.

The guard now works on a CONTENT signature (a hash of real content fields from
crawl_<client>.json), NOT lastmod:
  * NEW urls (never seen in state)              -> submit.
  * EXISTING urls                               -> re-submit ONLY when we have
    positive evidence the content changed (its stored content-hash differs from
    the current one). No crawl data for a site => no signal => existing urls are
    never re-submitted on a rebuild (new-urls-only). --force overrides.
  * Legacy <lastmod> state values and first-seen sites are SEEDED (hash stored,
    nothing submitted) so switching schema never triggers a mass re-push — this
    matches how state was originally seeded on 23 Jun.

Backstop cap: if a site's computed submit set is >30% of its sitemap (and not
--force), it is SKIPPED with a loud WARNING, so a bad deploy can never silently
re-push a whole site again.

State: src/data/live/indexnow_state.json  {client: {url: "h:<hash>"}}
"""
import json
import os
import sys
from datetime import datetime

import requests

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
BING_API_KEY = "c129b8c91294404d96cca29e1cf613fe"

SITES = {
    "rank4ai": "https://www.rank4ai.co.uk",
    "market-invoice": "https://marketinvoice.co.uk",
    "seocompare": "https://www.seocompare.co.uk",
    "bestbusinessloans": "https://bestbusinessloans.ai",
    "fundbiz": "https://fundbiz.co.uk",
    "cardmachines": "https://merchanthq.co.uk",
    "peptideclear": "https://peptideclear.co.uk",
    "kartapay": "https://kartapay.co.uk",
    "homesandhedge": "https://homesandhedge.co.uk",
    "hervitals": "https://hervitals.co.uk",
    "adhdhelper": "https://adhdhelper.co.uk",
    "company-rescue": "https://ltdturnaround.co.uk",
    "datesandtimes": "https://datesandtimes.co.uk",
    "fitcalcs": "https://fitcalcs.co.uk",
    "babydata": "https://babydata.co.uk",
    "vettedhome": "https://vettedhome.co.uk",
    "mortgageexplained": "https://mortgageexplained.co.uk",
}

INDEXNOW_URL = "https://api.indexnow.org/indexnow"

# Per-site IndexNow keys — each registered in its own repo's public/<key>.txt.
# Falling back to BING_API_KEY (above) for sites not in this map.
# The single shared key 403'd as "UserForbiddedToAccessSite" because Bing
# associates each IndexNow key with the BWT account that originally claimed it.
SITE_KEYS = {
    "rank4ai":           "4c1cc17752ab451887a14b719906f527",
    "market-invoice":    "a2dbf411f85049958a10a31d0eea8ab9",
    "seocompare":        "4c1cc17752ab451887a14b719906f527",
    "bestbusinessloans": "6c8693c2af63422098320cf1a132e7d2",
    "fundbiz":           "4d8cee5b9f8249d8848a5305264ca1cc",
    "cardmachines":      "0090cd828ef442e38aa2c00baca23c6d",
    "peptideclear":      "9b4e84786bf3482db8081609777b3811",
    "kartapay":          "e7ac3dd5700130fb675be39a3a0effc5",
    "homesandhedge":     "4109de09679304557367b5b3e1b90c9b",
    "hervitals":         "4d36b67015e69fd2c5009095402cac74",
    "adhdhelper":        "a39ace08e7ac01f94c8fadff07824ebd",
    "company-rescue":    "1644a63379414ee2be55d249cffa2d7d",
    "datesandtimes":     "b77809bc20917b53ed29bef15cf3fb64",
    "fitcalcs":          "34efe4973ea9b6923b1bb736aad21f75",
    "babydata":          "723526312aa65870fda148e84ca0b79a",
    "vettedhome":        "e8ac7f2771ef3889025ba977c4ace41e",
    "mortgageexplained": "b3d9f1a05c7e42d8a9061f4c8e2b7a35",
}


STATE_FILE = os.path.join(OUTPUT_DIR, "indexnow_state.json")


def load_state():
    """client -> {url: "h:<content-hash>"} map of what we've already seen, so we
    only ping IndexNow for NEW urls or urls whose CONTENT actually changed
    instead of re-submitting the whole sitemap every run (Bing flags that as
    over-use). Legacy values are raw <lastmod> strings and are migrated to
    content hashes on the fly without re-submitting."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_urls_from_crawl(client_id):
    """Get all URLs from the latest crawl as {url: ""} (no lastmod available)."""
    crawl_file = os.path.join(OUTPUT_DIR, f"crawl_{client_id}.json")
    if not os.path.exists(crawl_file):
        return {}
    with open(crawl_file) as f:
        data = json.load(f)
    return {p["url"]: "" for p in data.get("pages", []) if p.get("url")}


# Fields from crawl_<client>.json that reflect real CONTENT, not build churn.
# These change only when a page's actual content changes; they are NOT touched
# by a rebuild/redeploy (unlike sitemap <lastmod>, which is stamped at build
# time — the root cause of the Bing IndexNow over-use warning).
_SIG_FIELDS = (
    "title", "h1", "meta_desc", "word_count",
    "schemas", "internal_links_out", "image_count", "h2_count",
)


def get_content_sigs(client_id):
    """Return {url: "h:<hash>"} from the latest crawl, hashing stable CONTENT
    fields only. This is our trustworthy "did the content change" signal —
    unlike <lastmod>, it ignores build-time churn.

    Returns {} if there is no crawl file for the site (e.g. babydata,
    datesandtimes, fitcalcs, hervitals, vettedhome). Sites with no crawl data
    therefore have no change-signal, so their EXISTING urls are never
    re-submitted on a rebuild (new-urls-only) — which is exactly what we want.
    """
    import hashlib
    crawl_file = os.path.join(OUTPUT_DIR, f"crawl_{client_id}.json")
    if not os.path.exists(crawl_file):
        return {}
    try:
        with open(crawl_file) as f:
            data = json.load(f)
    except Exception:
        return {}
    sigs = {}
    for p in data.get("pages", []):
        url = p.get("url")
        if not url:
            continue
        raw = "|".join(str(p.get(k, "")) for k in _SIG_FIELDS)
        sigs[url] = "h:" + hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]
    return sigs


def get_urls_from_sitemap(base_url):
    """Get all URLs from the live sitemap (source of truth, always current).

    Expands a sitemap index into its child sitemaps and follows redirects
    (e.g. www -> non-www), so the URLs returned are the canonical ones. This
    is preferred over crawl data because it always includes newly published
    pages and never silently returns nothing for a site that lacks crawl data.
    """
    import re
    base = base_url.rstrip("/")
    headers = {"User-Agent": "Mozilla/5.0"}

    def parse_urlset(xml):
        # Map each <loc> to its <lastmod> (empty string if absent), so callers
        # can detect changed pages, not just new ones.
        out = {}
        for block in re.findall(r"<url>(.*?)</url>", xml, re.S):
            loc = re.search(r"<loc>([^<]+)</loc>", block)
            if not loc:
                continue
            lm = re.search(r"<lastmod>([^<]+)</lastmod>", block)
            out[loc.group(1).strip()] = (lm.group(1).strip() if lm else "")
        # Fallback for sitemaps without <url> wrappers
        if not out:
            for loc in re.findall(r"<loc>([^<]+)</loc>", xml):
                out[loc.strip()] = ""
        return out

    for path in ("sitemap-index.xml", "sitemap.xml", "sitemap-0.xml"):
        try:
            r = requests.get(f"{base}/{path}", timeout=20, allow_redirects=True, headers=headers)
            if r.status_code != 200:
                continue
            xml = r.text
            if "<sitemapindex" in xml:
                urls = {}
                for child in re.findall(r"<loc>([^<]+)</loc>", xml):
                    try:
                        cr = requests.get(child, timeout=20, allow_redirects=True, headers=headers)
                        if cr.status_code == 200:
                            urls.update(parse_urlset(cr.text))
                    except Exception:
                        pass
                if urls:
                    return urls
            else:
                urls = parse_urlset(xml)
                if urls:
                    return urls
        except Exception:
            pass
    return {}


def submit_urls(client_id, urls):
    """Submit URLs via IndexNow API.

    The host (and key location) are derived from the actual URLs, grouped by
    hostname, so submissions always match the canonical host and never fail on
    a www/non-www mismatch with the configured base URL.
    """
    from urllib.parse import urlparse

    if not urls:
        return 0

    # Per-site key (each registered with its own BWT account), fallback to shared.
    key = SITE_KEYS.get(client_id, BING_API_KEY)

    by_host = {}
    for u in urls:
        host = urlparse(u).netloc
        if host:
            by_host.setdefault(host, []).append(u)

    batch_size = 100
    total_submitted = 0

    for host, host_urls in by_host.items():
        key_location = f"https://{host}/{key}.txt"
        for i in range(0, len(host_urls), batch_size):
            batch = host_urls[i:i + batch_size]
            payload = {
                "host": host,
                "key": key,
                "keyLocation": key_location,
                "urlList": batch,
            }
            try:
                resp = requests.post(INDEXNOW_URL, json=payload, timeout=15)
                if resp.status_code in [200, 202]:
                    total_submitted += len(batch)
                    print(f"  Submitted {len(batch)} URLs to {host} (batch {i // batch_size + 1})")
                else:
                    print(f"  Batch {i // batch_size + 1} failed: HTTP {resp.status_code} — {resp.text[:100]}")
            except Exception as e:
                print(f"  Batch error: {e}")

    return total_submitted


# If a site's computed submit set exceeds this fraction of its sitemap (and it
# isn't --force), we treat it as a likely bad-deploy mass re-push and SKIP it
# with a loud warning rather than spamming Bing. Only applies to sites with
# enough urls that a percentage is meaningful.
CAP_RATIO = 0.30
CAP_MIN_URLS = 10


def _is_hash(v):
    return isinstance(v, str) and v.startswith("h:")


def plan_site(client_id, url_map, sig_map, prev, force):
    """Decide what to submit for one site, and compute the next state for it.

    Returns (to_submit, new_state, mode) where mode is one of:
      'seed'    - first-seen/empty site: record sigs, submit nothing
      'normal'  - new + genuinely-changed urls
      'force'   - everything
    new_state already contains on-the-fly migrations of legacy/seed values;
    the hashes for `to_submit` urls are applied by the caller AFTER a successful
    submit (so a failed/capped submit doesn't mark them as done).
    """
    def cur_sig(u):
        # Content hash if we have crawl data for this url, else a neutral
        # "seen" sentinel (known url, but no change-signal available).
        return sig_map.get(u, "seen")

    if force:
        return list(url_map.keys()), {u: cur_sig(u) for u in url_map}, "force"

    # First time we've ever seen this site (or empty state): SEED it — record
    # every url's signature and submit NOTHING. This is how state was seeded on
    # 23 Jun, and it means adding a new site (e.g. mortgageexplained) or a fresh
    # schema never triggers a whole-sitemap push.
    if not prev:
        return [], {u: cur_sig(u) for u in url_map}, "seed"

    to_submit = []
    new_state = dict(prev)
    for u in url_map:
        stored = prev.get(u)
        if stored is None:
            # NEW url on a known site → genuine new page → submit.
            to_submit.append(u)
        elif _is_hash(stored) and u in sig_map:
            # We have a real prior content-hash AND current crawl data:
            # re-submit only if the content actually changed.
            if stored != sig_map[u]:
                to_submit.append(u)
            # else: unchanged (build churn ignored) → skip.
        else:
            # Legacy <lastmod> value, "seen" sentinel, or no current signal:
            # silently migrate to a content hash if we have one, never submit.
            if u in sig_map:
                new_state[u] = sig_map[u]
            # else keep stored as-is.
    return to_submit, new_state, "normal"


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 submit_indexnow.py <client_id|all> [--dry-run|--seed|--force]")
        return

    # --force / --all-urls re-submits everything (manual reset, rare).
    # --dry-run computes + prints counts but POSTs nothing and writes nothing.
    # --seed records current signatures as state and POSTs nothing (clean reseed).
    force = "--force" in sys.argv or "--all-urls" in sys.argv
    dry_run = "--dry-run" in sys.argv
    seed_only = "--seed" in sys.argv or "--reseed" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    target = args[0] if args else "all"
    clients = list(SITES.keys()) if target == "all" else [target]

    if dry_run:
        print("== DRY RUN — computing to_submit only, no POST, no state/log write ==")
    if seed_only:
        print("== SEED — recording content signatures as state, no POST ==")

    results = {}
    state = load_state()
    import sys as _sys2, os as _os2; _sys2.path.insert(0, _os2.path.dirname(_os2.path.abspath(__file__)))
    from site_status import skip as _skip
    for client_id in clients:
        if client_id not in SITES:
            print(f"Unknown client: {client_id}")
            continue
        if _skip(client_id):
            print(f"  skip {client_id} (paused/pre-launch)"); continue

        # Prefer the live sitemap (always current, includes new pages); fall
        # back to crawl data only if the sitemap is unreachable.
        url_map = get_urls_from_sitemap(SITES[client_id])
        source = "sitemap"
        if not url_map:
            url_map = get_urls_from_crawl(client_id)
            source = "crawl"

        if not url_map:
            print(f"\n{client_id}: No URLs found (sitemap unreachable and no crawl data)")
            continue

        sig_map = get_content_sigs(client_id)
        prev = state.get(client_id, {})

        # --seed forces the seed path for every targeted site.
        if seed_only:
            state[client_id] = {u: sig_map.get(u, "seen") for u in url_map}
            print(f"\n{client_id}: seeded {len(url_map)} urls (crawl-sigs for {len(sig_map)}), submitted 0")
            continue

        to_submit, new_state, mode = plan_site(client_id, url_map, sig_map, prev, force)

        has_sig = "crawl" if sig_map else "NO-crawl (new-only)"
        print(f"\n{client_id}: {len(to_submit)} to submit of {len(url_map)} urls "
              f"[{mode}, sig={has_sig}, source={source}]")

        # Backstop: never let a single run push more than CAP_RATIO of a site.
        capped = False
        if (not force and mode == "normal" and len(url_map) >= CAP_MIN_URLS
                and len(to_submit) > CAP_RATIO * len(url_map)):
            pct = 100.0 * len(to_submit) / len(url_map)
            print(f"  ⚠️  WARNING: {client_id} would submit {len(to_submit)}/{len(url_map)} "
                  f"urls ({pct:.0f}% > {int(CAP_RATIO*100)}% cap) — SKIPPING to avoid Bing "
                  f"over-use. Likely a bad deploy or template-wide change. Use --force if genuine.")
            capped = True

        if mode == "seed":
            # Record signatures, submit nothing.
            if not dry_run:
                state[client_id] = new_state
            print(f"  Seeded {len(url_map)} urls (first-seen/empty state) — submitted 0")
            continue

        if capped:
            # Keep on-the-fly migrations, but do NOT record the to_submit hashes
            # (so they stay 'changed' and re-surface until resolved or --force'd).
            if not dry_run:
                state[client_id] = new_state
            results[client_id] = {
                "submitted": 0, "capped": True,
                "would_submit": len(to_submit), "total_urls": len(url_map),
                "source": source, "submitted_at": datetime.now().isoformat(),
            }
            continue

        if to_submit and not dry_run:
            submitted = submit_urls(client_id, to_submit)
            for u in to_submit:
                new_state[u] = sig_map.get(u, "seen")
            state[client_id] = new_state
            results[client_id] = {
                "submitted": submitted,
                "new_or_changed": len(to_submit),
                "total_urls": len(url_map),
                "source": source,
                "submitted_at": datetime.now().isoformat(),
            }
            print(f"  Done: {submitted}/{len(to_submit)} submitted ({len(url_map)} total, rest unchanged)")
        elif to_submit and dry_run:
            print(f"  [dry-run] would submit {len(to_submit)} urls")
        else:
            # No new/changed urls: still persist any on-the-fly migrations.
            if not dry_run:
                state[client_id] = new_state
            print(f"  Nothing new or changed since last run — skipped (no re-submit)")

    if dry_run:
        print("\n[dry-run] state and log NOT written.")
        return

    save_state(state)

    # Save submission log
    log_file = os.path.join(OUTPUT_DIR, "indexnow_log.json")
    if os.path.exists(log_file):
        with open(log_file) as f:
            log = json.load(f)
    else:
        log = []

    log.append({
        "date": datetime.now().isoformat(),
        "results": results,
    })

    with open(log_file, "w") as f:
        json.dump(log[-50:], f, indent=2)  # Keep last 50 submissions

    print(f"\nLog saved → {log_file}")


if __name__ == "__main__":
    main()
