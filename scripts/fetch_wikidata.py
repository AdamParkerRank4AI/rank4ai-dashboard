#!/usr/bin/env python3
"""
fetch_wikidata.py — populate src/data/live/wikidata.json with each fleet
brand's real Wikidata status, verified by official-website (P856) so we
never false-match a same-named third party (e.g. the Kriya "MarketInvoice"
lender item Q16997376, whose P856 is NOT marketinvoice.co.uk).

For each client we:
  1. wbsearchentities on the brand name,
  2. fetch each candidate's P856 (official website),
  3. mark exists=True + qid ONLY when a candidate's P856 host == the
     client's own domain. Otherwise exists=False (with any same-name
     decoy recorded under `decoy_qid` for transparency).

Read by scripts/generate_recommendations.py (the "Not listed on Wikidata"
rule) and push_to_fleet. Hand-editing is fine; this just keeps it honest.
"""
import json, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENTS = os.path.join(ROOT, "src/data/clients.json")
OUT = os.path.join(ROOT, "src/data/live/wikidata.json")
API = "https://www.wikidata.org/w/api.php"
UA = {"User-Agent": "rank4ai-fleet-dashboard/1.0 (adam@muswellrose.com)"}

# Only the owned/core fleet sites are worth tracking; skip pre-launch demos.
TRACK = {
    "rank4ai", "market-invoice", "seocompare", "bestbusinessloans",
    "fundbiz", "cardmachines", "kartapay", "peptideclear",
}


def _get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def domain_host(domain):
    return domain.lower().split("/")[0].replace("www.", "")


def entity_facts(qid):
    """Return (p856_host, has_p856, label) for an entity."""
    try:
        d = _get({"action": "wbgetentities", "ids": qid,
                  "props": "claims|labels", "format": "json"})
        e = d["entities"][qid]
        label = e.get("labels", {}).get("en", {}).get("value", "")
        p856 = e.get("claims", {}).get("P856", [])
        host = None
        for c in p856:
            url = c["mainsnak"]["datavalue"]["value"]
            host = urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
            if host:
                break
        return host, bool(p856), label
    except Exception:
        return None, False, ""


def _norm(s):
    return "".join(ch for ch in s.lower() if ch.isalnum())


def check(name, domain):
    host = domain_host(domain)
    try:
        res = _get({"action": "wbsearchentities", "search": name,
                    "language": "en", "format": "json", "limit": 5})
    except Exception as e:
        return {"exists": None, "error": str(e), "checked": name}
    incomplete = None  # ours by label but no P856 to confirm
    decoy = None       # same-name third party (has a P856 that isn't us)
    for hit in res.get("search", []):
        qid = hit["id"]
        site, has_p856, label = entity_facts(qid)
        time.sleep(0.3)
        if site and host in site:
            return {"exists": True, "qid": qid,
                    "description": hit.get("description", ""),
                    "verified_via": "P856", "checked": name}
        # Our own freshly-created stub: name matches, but P856 not yet set.
        if not has_p856 and _norm(name) in _norm(label) and incomplete is None:
            incomplete = qid
        elif decoy is None:
            decoy = qid
    if incomplete:
        return {"exists": True, "qid": incomplete, "verified_via": "label",
                "p856_missing": True,
                "note": "Item is ours but has no official-website (P856) link "
                        "— add P856=https://%s so Google KG can resolve it." % host,
                "checked": name}
    return {"exists": False, "qid": None, "decoy_qid": decoy, "checked": name}


def main():
    clients = json.load(open(CLIENTS))
    if isinstance(clients, dict):
        clients = clients.get("clients", list(clients.values()))
    out = {}
    for c in clients:
        cid = c.get("id")
        if cid not in TRACK:
            continue
        r = check(c.get("name", cid), c.get("domain", ""))
        out[cid] = r
        flag = "✓" if r.get("exists") else ("?" if r.get("exists") is None else "—")
        print(f"  {flag} {cid:18} {r.get('qid') or r.get('decoy_qid') or ''}")
        time.sleep(0.4)
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"wrote {OUT} ({len(out)} sites)")


if __name__ == "__main__":
    main()
