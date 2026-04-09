#!/usr/bin/env python3
"""
Competitor SERP comparison — who ranks where for the same queries.
Uses Serper.dev to check organic rankings for client vs competitors.
"""
import json
import os
import time
from datetime import datetime
from collections import Counter

import requests

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
SERPER_API_KEY = "28257708ebacca0e696d3cfaebda39de3496fa75"

CLIENTS = {
    "rank4ai": {
        "domain": "rank4ai.co.uk",
        "competitor_domains": [
            "ceek.co.uk", "found.co.uk", "clickslice.co.uk", "charle.co.uk",
            "varn.co.uk", "yald.io", "firstanswer.agency", "aeo-rex.com",
            "propeller.co.uk", "kaizen.co.uk",
        ],
        "queries": [
            "AI search visibility agency UK",
            "best AI SEO agencies UK",
            "GEO agency UK",
            "AI search audit UK",
            "generative engine optimization UK",
            "best GEO agencies UK",
            "AI overviews optimization UK",
            "AI SEO services UK",
        ],
    },
    "market-invoice": {
        "domain": "marketinvoice.co.uk",
        "competitor_domains": [
            "bibbyfinancialservices.com", "closebrothers.com", "timefinance.com",
            "capitalise.com", "gocompare.com", "fundinvoice.co.uk",
            "compare-factoring.co.uk", "smeinvoicefinance.co.uk",
        ],
        "queries": [
            "invoice finance UK",
            "best invoice factoring companies UK",
            "compare invoice finance providers UK",
            "invoice finance for small business UK",
            "how does invoice finance work",
            "confidential invoice discounting UK",
            "invoice finance costs UK",
            "best construction invoice finance UK",
        ],
    },
    "seocompare": {
        "domain": "seocompare.co.uk",
        "competitor_domains": [
            "clickslice.co.uk", "found.co.uk", "propeller.co.uk",
            "impression.co.uk", "aira.net", "charle.co.uk",
        ],
        "queries": [
            "compare SEO agencies UK",
            "best SEO companies UK 2026",
            "how to choose an SEO agency UK",
            "top rated SEO services UK",
            "SEO agency comparison",
        ],
    },
}


def search_query(query):
    """Search via Serper."""
    try:
        resp = requests.post("https://google.serper.dev/search", json={
            "q": query, "gl": "gb", "hl": "en", "num": 20,
        }, headers={
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json",
        }, timeout=15)

        if resp.status_code != 200:
            return None

        data = resp.json()
        results = []
        for r in data.get("organic", []):
            results.append({
                "position": r.get("position", 0),
                "domain": r.get("link", "").split("/")[2] if r.get("link") else "",
                "title": r.get("title", ""),
            })
        return results
    except:
        return None


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_results = {}

    for client_id, config in CLIENTS.items():
        print(f"\n{'='*50}")
        print(f"{client_id}")
        print(f"{'='*50}")

        client_domain = config["domain"]
        comp_domains = config["competitor_domains"]
        all_domains = [client_domain] + comp_domains

        # Track positions per domain across all queries
        domain_positions = {d: [] for d in all_domains}
        domain_appearances = Counter()
        query_results = []

        for query in config["queries"]:
            time.sleep(1)
            results = search_query(query)
            if not results:
                print(f"  Error: {query[:40]}")
                continue

            query_data = {"query": query, "rankings": {}}

            for r in results[:20]:
                domain = r["domain"].replace("www.", "")
                if domain in all_domains or any(cd in domain for cd in all_domains):
                    # Match to our tracked domain
                    matched = None
                    for d in all_domains:
                        if d in domain or domain in d:
                            matched = d
                            break
                    if matched:
                        query_data["rankings"][matched] = r["position"]
                        domain_positions[matched].append(r["position"])
                        domain_appearances[matched] += 1

            query_results.append(query_data)

            # Print ranking comparison
            client_pos = query_data["rankings"].get(client_domain, "--")
            comp_positions = [(d, query_data["rankings"].get(d, "--")) for d in comp_domains if d in query_data["rankings"]]
            comp_str = ", ".join([f"{d.split('.')[0]}:#{p}" for d, p in comp_positions[:3]])
            print(f"  You:#{client_pos} | {comp_str} | {query[:40]}")

        # Calculate summary
        client_avg = round(sum(domain_positions[client_domain]) / max(len(domain_positions[client_domain]), 1), 1) if domain_positions[client_domain] else None
        client_visibility = round(domain_appearances[client_domain] / max(len(config["queries"]), 1) * 100, 1)

        competitor_summary = []
        for d in comp_domains:
            if domain_appearances[d] > 0:
                avg_pos = round(sum(domain_positions[d]) / len(domain_positions[d]), 1)
                visibility = round(domain_appearances[d] / len(config["queries"]) * 100, 1)
                competitor_summary.append({
                    "domain": d,
                    "appearances": domain_appearances[d],
                    "avg_position": avg_pos,
                    "visibility_pct": visibility,
                })

        competitor_summary.sort(key=lambda x: -x["appearances"])

        all_results[client_id] = {
            "domain": client_domain,
            "checked_at": datetime.now().isoformat(),
            "total_queries": len(config["queries"]),
            "client_appearances": domain_appearances[client_domain],
            "client_avg_position": client_avg,
            "client_visibility_pct": client_visibility,
            "competitors": competitor_summary,
            "query_results": query_results,
        }

        print(f"\n  Your visibility: {client_visibility}% ({domain_appearances[client_domain]}/{len(config['queries'])} queries)")
        if client_avg:
            print(f"  Your avg position: {client_avg}")
        print(f"  Top competitors:")
        for c in competitor_summary[:5]:
            print(f"    {c['domain']}: {c['visibility_pct']}% visible, avg pos {c['avg_position']}")

    output_file = os.path.join(OUTPUT_DIR, "competitor_serp.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved → {output_file}")
    print(f"Serper credits used: ~{sum(len(c['queries']) for c in CLIENTS.values())}")


if __name__ == "__main__":
    main()
