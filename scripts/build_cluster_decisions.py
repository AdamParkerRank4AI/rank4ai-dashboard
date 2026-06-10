#!/usr/bin/env python3
"""Cluster URLs by SERP overlap (co-ranking queries) and emit one decision per
cluster: Keep / Fix / Consolidate / Optimise / Prune — with evidence + confidence.

This is the "join in the data layer": the dashboard already computes the signals
(cannibalisation, decay, indexing) in separate files; this connects URLs that
fight over the same searches into clusters and turns the signals into a single
actionable call per cluster.

Inputs (src/data/live/):
  cannibalisation.json  - per query, the co-ranking pages (+position/impressions)
                          = the SERP-overlap signal for our own pages
  content_decay.json    - per-query decay signals (cross-referenced)
Output:
  cluster_decisions.json
"""
import json, os, datetime
from collections import defaultdict
from urllib.parse import urlparse

# Evidence floors — below these a "cluster" is normal SERP behaviour, not a
# fixable problem. Without them the engine flags healthy structures (homepage
# + /contact both ranking for the brand) and incidental low-volume co-ranks.
MIN_CLUSTER_IMP = 40        # need real shared demand before recommending action
CORE_PATHS = {"", "/", "/contact", "/about", "/privacy", "/terms",
              "/cookies", "/cookie-policy", "/disclaimer", "/accessibility"}


def _path(u):
    return urlparse(u).path.rstrip("/").lower()

LIVE = os.path.join(os.path.dirname(__file__), "..", "src", "data", "live")


def load(name):
    p = os.path.join(LIVE, name)
    return json.load(open(p)) if os.path.exists(p) else {}


class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def main():
    cann = load("cannibalisation.json").get("sites", {})
    decay = load("content_decay.json").get("sites", {})

    out = {
        "computed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "method": "SERP-overlap clustering from cannibalisation co-ranking data; "
                  "decision engine joins decay + impression-concentration signals.",
        "sites": {},
    }

    for site, data in cann.items():
        top = data.get("top", []) or []

        # --- cluster: URLs that co-rank for a shared query are connected ---
        uf = UnionFind()
        for q in top:
            pages = [p["page"] for p in q.get("pages", []) if p.get("page")]
            for p in pages:
                uf.find(p)
            for i in range(1, len(pages)):
                uf.union(pages[0], pages[i])

        clusters = defaultdict(lambda: {"urls": set(), "queries": []})
        for q in top:
            pages = q.get("pages", []) or []
            if not pages:
                continue
            root = uf.find(pages[0]["page"])
            c = clusters[root]
            for p in pages:
                if p.get("page"):
                    c["urls"].add(p["page"])
            c["queries"].append(q)

        # --- decay query set for this site ---
        sd = decay.get(site, {}) or {}
        decayed_q = set()
        for key in ("position_drop", "dropped_off_page_1", "dropped_off_page_2",
                    "impressions_collapse"):
            for d in (sd.get(key) or []):
                if isinstance(d, dict) and d.get("query"):
                    decayed_q.add(d["query"])

        # --- one decision per cluster ---
        site_clusters = []
        for c in clusters.values():
            urls = sorted(c["urls"])
            queries = c["queries"]
            page_imp = defaultdict(int)
            page_pos = defaultdict(list)
            total_imp = 0
            for q in queries:
                for p in q.get("pages", []):
                    page_imp[p["page"]] += p.get("impressions", 0) or 0
                    if p.get("position"):
                        page_pos[p["page"]].append(p["position"])
                    total_imp += p.get("impressions", 0) or 0
            if not page_imp:
                continue

            winner = max(page_imp, key=lambda u: (page_imp[u], -min(page_pos.get(u, [99]))))
            win_imp = page_imp[winner]
            concentration = (win_imp / total_imp) if total_imp else 1.0
            best_pos = min((min(v) for v in page_pos.values() if v), default=99.0)
            n_urls = len(urls)
            n_q = len(queries)
            decaying = any(q["query"] in decayed_q for q in queries)

            # Guards against false positives:
            #  - winner is the homepage: you never 301 deep pages into "/",
            #    and the homepage co-ranking for brand/navigational queries
            #    alongside deep pages is expected, not cannibalisation.
            #  - the only losing URLs are core/utility pages (e.g. /contact
            #    ranking for the brand term): healthy, never prune those.
            #  - too little shared demand to act on.
            winner_is_home = _path(winner) in ("", "/")
            losers = [u for u in urls if u != winner]
            losers_all_core = bool(losers) and all(_path(u) in CORE_PATHS for u in losers)
            enough_signal = total_imp >= MIN_CLUSTER_IMP

            if (n_urls >= 2 and concentration < 0.85 and n_q >= 2
                    and enough_signal and not winner_is_home and not losers_all_core):
                rec = "Consolidate"
                reason = (f"{n_urls} pages split {total_imp} impressions across "
                          f"{n_q} shared quer{'y' if n_q == 1 else 'ies'}; one clear winner.")
                conf = "high" if (concentration < 0.6 and total_imp >= 80) else "medium"
            elif decaying and enough_signal:
                rec = "Fix"
                reason = "Cluster queries are decaying (position/impressions falling)."
                conf = "medium"
            elif best_pos > 10 and enough_signal:
                rec = "Optimise"
                reason = f"Best position {best_pos:.0f} — stuck on page 2+, demand unrealised."
                conf = "medium"
            elif win_imp < 5 and n_urls >= 2 and not winner_is_home and not losers_all_core:
                rec = "Prune"
                reason = "Negligible impressions on duplicate URLs — candidate to noindex/merge."
                conf = "low"
            else:
                rec = "Keep"
                reason = ("Single strong winner, no conflict." if enough_signal
                          else f"Only {total_imp} shared impressions — below the action threshold; monitor.")
                conf = "high"

            site_clusters.append({
                "theme": max(queries, key=lambda q: q.get("total_impressions", 0))["query"],
                "recommendation": rec,
                "confidence": conf,
                "reason": reason,
                "winner": winner,
                "urls": urls,
                "n_urls": n_urls,
                "n_queries": n_q,
                "total_impressions": total_imp,
                "winner_impression_share": round(concentration, 2),
                "best_position": round(best_pos, 1),
                "decaying": decaying,
                "queries": [q["query"] for q in queries][:10],
            })

        site_clusters.sort(key=lambda c: -c["total_impressions"])
        rec_counts = defaultdict(int)
        for c in site_clusters:
            rec_counts[c["recommendation"]] += 1
        out["sites"][site] = {
            "cluster_count": len(site_clusters),
            "recommendation_counts": dict(rec_counts),
            "clusters": site_clusters,
        }

    path = os.path.join(LIVE, "cluster_decisions.json")
    json.dump(out, open(path, "w"), indent=2)

    total = sum(s["cluster_count"] for s in out["sites"].values())
    print(f"Wrote cluster_decisions.json: {len(out['sites'])} sites, {total} clusters")
    for site, s in out["sites"].items():
        if s["cluster_count"]:
            print(f"  {site}: {s['cluster_count']} clusters {s['recommendation_counts']}")


if __name__ == "__main__":
    main()
