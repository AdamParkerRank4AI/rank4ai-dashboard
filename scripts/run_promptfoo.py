#!/usr/bin/env python3
"""
Run Promptfoo AI citation tests for all clients.
Parses results and saves JSON for the dashboard.
"""
import json
import os
import subprocess
import sys
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTFOO_DIR = os.path.join(PROJECT_DIR, "promptfoo")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "src", "data", "live")

CLIENTS = ["rank4ai", "market-invoice"]


def run_client(client_id):
    config_dir = os.path.join(PROMPTFOO_DIR, client_id)
    output_file = os.path.join(config_dir, "results.json")

    print(f"\nRunning Promptfoo for {client_id}...")

    result = subprocess.run(
        ["npx", "promptfoo", "eval", "--config", "promptfooconfig.yaml", "-o", "results.json", "--no-cache"],
        cwd=config_dir,
        capture_output=True,
        text=True,
        timeout=600,
        env={**os.environ},
    )

    if result.returncode != 0:
        print(f"  Error: {result.stderr[:200]}")
        return None

    if not os.path.exists(output_file):
        print(f"  No results file generated")
        return None

    with open(output_file) as f:
        data = json.load(f)

    # Parse results
    results_list = data.get("results", {}).get("results", [])
    if not results_list:
        results_list = data.get("results", [])

    parsed = []
    for r in results_list:
        query = ""
        # Extract query from vars or prompt
        if isinstance(r.get("vars"), dict):
            query = r["vars"].get("query", "")
        elif isinstance(r.get("prompt"), dict):
            query = r["prompt"].get("raw", "")
        elif isinstance(r.get("prompt"), str):
            query = r["prompt"]

        # Get response
        response = ""
        if isinstance(r.get("response"), dict):
            response = r["response"].get("output", "")
        elif isinstance(r.get("response"), str):
            response = r["response"]

        # Check assertions
        success = r.get("success", False)
        grade_result = r.get("gradingResult", {})
        pass_count = grade_result.get("pass", 0) if isinstance(grade_result, dict) else 0
        fail_count = grade_result.get("fail", 0) if isinstance(grade_result, dict) else 0

        # Provider info
        provider = ""
        if isinstance(r.get("provider"), dict):
            provider = r["provider"].get("label", r["provider"].get("id", ""))
        elif isinstance(r.get("provider"), str):
            provider = r["provider"]

        parsed.append({
            "query": query[:200],
            "provider": provider,
            "cited": success,
            "response_preview": str(response)[:300],
            "pass_count": pass_count,
            "fail_count": fail_count,
        })

    cited_count = sum(1 for p in parsed if p["cited"])
    total = len(parsed)
    citation_rate = round(cited_count / max(total, 1) * 100, 1)

    # Group by provider
    providers = {}
    for p in parsed:
        prov = p["provider"] or "unknown"
        if prov not in providers:
            providers[prov] = {"total": 0, "cited": 0}
        providers[prov]["total"] += 1
        if p["cited"]:
            providers[prov]["cited"] += 1

    for prov in providers:
        providers[prov]["rate"] = round(providers[prov]["cited"] / max(providers[prov]["total"], 1) * 100, 1)

    return {
        "client_id": client_id,
        "tested_at": datetime.now().isoformat(),
        "total_queries": total,
        "cited_count": cited_count,
        "citation_rate": citation_rate,
        "providers": providers,
        "results": parsed,
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_results = {}
    for client_id in CLIENTS:
        try:
            result = run_client(client_id)
            if result:
                all_results[client_id] = result
                print(f"  Citation rate: {result['citation_rate']}% ({result['cited_count']}/{result['total_queries']})")
                for prov, stats in result["providers"].items():
                    print(f"    {prov}: {stats['rate']}% ({stats['cited']}/{stats['total']})")
        except Exception as e:
            print(f"  Error: {e}")

    output_file = os.path.join(OUTPUT_DIR, "promptfoo_citations.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
