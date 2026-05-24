#!/usr/bin/env python3
"""
classify_queries.py — split each site's GSC top_queries into 5 intent buckets
so the dashboard can surface where to build /alternatives/, where to add
calculators/tools, where to deepen informational content, and which queries
are already pure-brand-own (defensible).

Buckets (in priority order; first match wins):
  1. branded_own       — query contains the site's own brand
  2. branded_competitor — query contains a known competitor brand for the site's vertical
  3. transactional     — quote, calculator, rates, compare, price, cost, best, cheapest, near me
  4. location          — UK city/region name (London, Manchester, etc) in the query
  5. informational     — what is, how does, why, when, can I, do I need, explained, guide
  6. other             — anything left

Output → src/data/live/intent_split.json with per-site rolled-up counts +
top 10 sample queries per bucket. The dashboard consumes this to render
the Intent Split panel + the gap-action lists.
"""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

LIVE = Path(os.path.expanduser("~/rank4ai-dashboard/src/data/live"))

# Per-site brand-own tokens + known competitor brands.
# Competitors are the ones we want to capture via /alternatives/<brand>/ pages.
SITE_PROFILE = {
    "rank4ai": {
        "brand_own": ["rank4ai", "rank 4 ai"],
        "competitors": ["found", "propeller", "charle", "varn", "impression", "builtvisible", "kaizen", "awarenessai", "first page sage", "ipullrank", "directive"],
        "transactional_extra": ["audit", "agency", "consultant"],
    },
    "market-invoice": {
        "brand_own": ["market invoice", "marketinvoice"],
        "competitors": ["bibby", "hsbc", "barclays", "lloyds", "natwest", "santander", "aldermore", "close brothers", "skipton", "ultimate finance", "igf", "novuna", "time finance", "sonovate", "kriya", "stenn", "marketfinance", "market finance", "capitalise", "penny", "iwoca", "fundingcircle", "funding circle"],
        "transactional_extra": ["quote", "rates", "calculator", "compare", "advance"],
    },
    "seocompare": {
        "brand_own": ["seocompare", "seo compare"],
        "competitors": ["clickslice", "found", "ipullrank", "first page sage", "directive consulting", "impression digital", "builtvisible", "kaizen", "varn", "omnius", "awarenessai", "polemic digital"],
        "transactional_extra": ["audit", "agency", "consultant", "compare", "best"],
    },
    "bestbusinessloans": {
        "brand_own": ["bestbusinessloans", "best business loans"],
        "competitors": ["iwoca", "funding circle", "fundingcircle", "capitalise", "swoop", "allica", "oaknorth", "tide", "capify", "liberis", "bizcap", "365 business finance", "got capital", "propel", "esme", "lendingcrowd", "starling business loan"],
        "transactional_extra": ["quote", "compare", "calculator", "rates", "apr", "cost"],
    },
    "fundbiz": {
        "brand_own": ["fundbiz"],
        "competitors": ["iwoca", "swoop", "capitalise", "funding circle", "fundingcircle", "365 business finance", "capify", "liberis", "bizcap", "youlend", "jpm capital", "allica", "oaknorth", "aldermore", "shawbrook", "metro bank"],
        "transactional_extra": ["quote", "compare", "calculator", "rates", "apr", "cost", "refinance"],
    },
    "cardmachines": {
        "brand_own": ["merchanthq", "merchant hq", "acceptcard"],
        "competitors": ["square", "stripe", "sumup", "zettle", "worldpay", "barclaycard", "takepayments", "dojo", "paymentsense", "tyl", "adyen", "mypos", "elavon", "global payments", "lloyds cardnet", "opayo"],
        "transactional_extra": ["quote", "compare", "calculator", "rates", "fees", "cheapest", "best"],
    },
    "peptideclear": {
        "brand_own": ["peptideclear", "peptide clear"],
        "competitors": ["numan", "voy", "manual", "juniper", "phlo", "pharmacy2u", "simplymeds", "boots online doctor", "asda online doctor", "my-peptides", "direct sarms", "pure peptides", "aquila", "pinnacle", "nooku", "bare biology", "vital proteins", "hooke", "echelon"],
        "transactional_extra": ["compare", "review", "cheapest", "best", "where to buy", "uk"],
    },
    "kartapay": {
        "brand_own": ["kartapay"],
        "competitors": ["polcard", "sumup", "stripe", "square", "worldpay", "mypos", "barclaycard", "dojo", "zettle", "takepayments"],
        "transactional_extra": ["porównanie", "comparație", "kalkulator", "calculator", "compare", "rates", "fees"],
    },
}

UK_CITIES = {
    "london", "manchester", "birmingham", "leeds", "bristol", "liverpool",
    "glasgow", "edinburgh", "cardiff", "belfast", "newcastle", "sheffield",
    "nottingham", "coventry", "leicester", "brighton", "reading", "oxford",
    "cambridge", "york", "aberdeen", "bath", "plymouth", "southampton",
    "milton keynes", "swansea", "derby", "portsmouth", "stoke",
}

TRANSACTIONAL_TOKENS = [
    "quote", "calculator", "rates", "rate", "compare", "comparison",
    "price", "pricing", "cost", "costs", "fee", "fees", "cheapest",
    "cheap", "best", "top", "vs", "alternative", "alternatives",
    "near me", "uk", "buy", "for sale",
]

INFORMATIONAL_TOKENS = [
    "what is", "what's", "how does", "how do", "how to", "why does",
    "why is", "when do", "when does", "where can", "can i", "do i",
    "is invoice", "explained", "guide", "vs", "meaning", "definition",
    "review", "reviews", "examples",
]


def classify(query, profile):
    q = query.lower()

    # Branded-own first (defensible)
    for token in profile.get("brand_own", []):
        if token in q:
            return "branded_own"

    # Branded competitor
    for token in profile.get("competitors", []):
        # Use word boundary roughly — match whole token
        if re.search(rf"\b{re.escape(token)}\b", q):
            return "branded_competitor"

    # Transactional intent (high commercial)
    trans = TRANSACTIONAL_TOKENS + profile.get("transactional_extra", [])
    for token in trans:
        if token in q:
            return "transactional"

    # Location-bound
    for city in UK_CITIES:
        if re.search(rf"\b{re.escape(city)}\b", q):
            return "location"

    # Informational
    for token in INFORMATIONAL_TOKENS:
        if token in q:
            return "informational"

    return "other"


def is_noise(q):
    text = q.get("query", "")
    if not text or len(text) > 90:
        return True
    if "-site:" in text or '"' in text:
        return True
    return False


def main():
    gsc = json.load(open(LIVE / "gsc.json"))
    out = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "sites": {},
    }
    for site_id, profile in SITE_PROFILE.items():
        site_data = gsc.get(site_id) or {}
        queries = site_data.get("top_queries") or []
        # Filter noise (research operator strings, etc)
        queries = [q for q in queries if not is_noise(q)]

        buckets = {
            "branded_own": [],
            "branded_competitor": [],
            "transactional": [],
            "location": [],
            "informational": [],
            "other": [],
        }
        for q in queries:
            bucket = classify(q["query"], profile)
            buckets[bucket].append(q)

        site_out = {"total_queries": len(queries), "buckets": {}, "actionable_gaps": []}
        for name, items in buckets.items():
            items.sort(key=lambda x: -x.get("impressions", 0))
            total_imp = sum(q.get("impressions", 0) for q in items)
            total_clicks = sum(q.get("clicks", 0) for q in items)
            site_out["buckets"][name] = {
                "count": len(items),
                "total_impressions": total_imp,
                "total_clicks": total_clicks,
                "ctr": round(total_clicks / total_imp * 100, 2) if total_imp else 0,
                "top": items[:10],
            }
        out["sites"][site_id] = site_out

    output_path = LIVE / "intent_split.json"
    with open(output_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote → {output_path}\n")
    print("Per-site summary:")
    for site_id, data in out["sites"].items():
        b = data["buckets"]
        print(f"\n━ {site_id} (total: {data['total_queries']} queries) ━")
        for name in ["branded_own", "branded_competitor", "transactional", "location", "informational", "other"]:
            bb = b[name]
            print(f"  {name:22s} count={bb['count']:3d} imp={bb['total_impressions']:5d} clk={bb['total_clicks']:3d} CTR={bb['ctr']}%")


if __name__ == "__main__":
    main()
