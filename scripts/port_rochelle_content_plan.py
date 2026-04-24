#!/usr/bin/env python3
"""
Port Rochelle Marashi's Lovable content plan to the dashboard.

Reads the full Supabase export (303 rows: 104 live + 199 placeholder content-plan
slots) and writes a hierarchical JSON the dashboard can render as a tree view.

Hierarchy:
  Layer (L1 → L2A → L2B → L3 → L4)
    → Page (Hub / Authority / Service / Delivery / Comparison / Governance / custom_content)
       → Child slot (Blog / Question / Guide / Whitepaper / blog_post / question_page)

Output: ~/rank4ai-dashboard/src/data/live/site_structure_rochellemarashi.json
"""
from __future__ import annotations
import json, os
from collections import defaultdict
from pathlib import Path

EXPORT = Path(os.environ["HOME"]) / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "claude" / "Clients" / "Therapy Site" / "rochelle-marashi-full-export-2026-04-23.json"
OUT = Path(os.environ["HOME"]) / "rank4ai-dashboard" / "src" / "data" / "live" / "site_structure_rochellemarashi.json"

LAYER_ORDER = ["L1", "L2A", "L2B", "L3", "L4", None]
LAYER_LABELS = {
    "L1": "Layer 1 · Identity and Conversion",
    "L2A": "Layer 2A · Authority Pillars",
    "L2B": "Layer 2B · Service Clusters",
    "L3": "Layer 3 · Delivery and AI Bridge",
    "L4": "Layer 4 · Governance",
    None: "Container indexes and content entries",
}

PARENT_TYPES = {"Hub", "Authority", "custom_content", "Delivery", "Comparison", "Governance", "Service", "container_index"}
CHILD_TYPES = {"Blog", "Question", "Guide", "Whitepaper", "blog_post", "question_page", "podcast_episode", "guide"}


def page_number_key(n):
    """Sort key for page numbers like 10, 10.1, 10.1.B1, 10.Q1, C3.1"""
    if not n:
        return (999, 0, 0, "")
    parts = str(n).split(".")
    out = []
    for p in parts:
        # Strip any prefix letter (B, Q, G, W, C) and parse number
        letter = ""
        num_part = p
        if p and p[0].isalpha():
            letter = p[0]
            num_part = p[1:]
        try:
            out.append((letter, int(num_part) if num_part else 0))
        except ValueError:
            out.append((letter, 0))
    return tuple(out)


def main():
    with open(EXPORT) as f:
        db = json.load(f)

    pages = db["site_pages"]
    # Build children map keyed on parent_page_number
    children_by_parent = defaultdict(list)
    for p in pages:
        parent = p.get("parent_page_number")
        if parent:
            children_by_parent[parent].append(p)

    # Top-level = rows whose page_number exists but parent is None,
    # OR rows that fall outside the parent tree (container indexes etc.)
    top_level = [p for p in pages if not p.get("parent_page_number")]
    top_level.sort(key=lambda p: page_number_key(p.get("page_number")))

    def node(p):
        slot_info = None
        if p.get("status") == "not_started":
            # Derive slot family from page_type and the suffix of page_number
            pn = p.get("page_number") or ""
            suffix = pn.split(".")[-1] if "." in pn else pn
            slot_info = {
                "slot": suffix,
                "family": p.get("page_type"),
                "word_count_target": p.get("word_count_target_max"),
            }
        return {
            "id": p["id"],
            "page_number": p.get("page_number"),
            "page_name": p.get("page_name"),
            "url_path": p.get("url_path"),
            "layer": p.get("layer"),
            "page_type": p.get("page_type"),
            "status": p.get("status"),
            "word_count_actual": p.get("word_count_actual"),
            "word_count_target_min": p.get("word_count_target_min"),
            "word_count_target_max": p.get("word_count_target_max"),
            "crisis_link_required": p.get("crisis_link_required"),
            "disclaimer_required": p.get("disclaimer_required"),
            "parent_page_number": p.get("parent_page_number"),
            "slot": slot_info,
            "children": [],
        }

    def build_tree(parent_number):
        items = sorted(
            children_by_parent.get(parent_number, []),
            key=lambda p: page_number_key(p.get("page_number")),
        )
        out = []
        for c in items:
            nd = node(c)
            nd["children"] = build_tree(c.get("page_number"))
            out.append(nd)
        return out

    # Build by layer
    layers = defaultdict(list)
    for p in top_level:
        nd = node(p)
        nd["children"] = build_tree(p.get("page_number"))
        layers[p.get("layer")].append(nd)

    ordered_layers = []
    for k in LAYER_ORDER:
        if k in layers:
            ordered_layers.append({
                "layer": k or "other",
                "label": LAYER_LABELS[k],
                "pages": layers[k],
            })

    # Totals
    live = sum(1 for p in pages if p.get("status") == "live")
    not_started = sum(1 for p in pages if p.get("status") == "not_started")
    slots_by_family = defaultdict(lambda: {"filled": 0, "empty": 0})
    for p in pages:
        if p.get("page_type") in CHILD_TYPES:
            key = p.get("page_type").lower().replace("_", "-")
            if p.get("status") == "live":
                slots_by_family[key]["filled"] += 1
            else:
                slots_by_family[key]["empty"] += 1

    result = {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "source": str(EXPORT),
        "totals": {
            "total_rows": len(pages),
            "live": live,
            "not_started": not_started,
            "slots": dict(slots_by_family),
        },
        "strategy_summary": {
            "clusters": ["Power and Control", "Institutional and Systemic Harm", "Trauma Impact", "Trauma Recovery"],
            "authority_pillars": ["Therapy", "Psychotherapy", "How I Work", "Who I Work With", "About"],
            "slot_rules": {
                "Hub": "4-5 blog slots + 5-8 question slots + 1 guide slot",
                "Service": "4 blog slots + 5 question slots",
                "Authority": "5 blog slots + 8 question slots + 1 guide slot + 1 whitepaper slot",
            },
            "rule_every_service_must_link_to": ["/fees", "/contact", "online delivery phrasing"],
            "rule_every_ai_page_must_link_to": ["/safeguarding", "/crisis-and-emergency-guidance"],
        },
        "tree": ordered_layers,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUT}")
    print(f"Totals: {live} live, {not_started} not started, across {len(ordered_layers)} layers.")
    print(f"Content slots by family: {dict(slots_by_family)}")


if __name__ == "__main__":
    main()
