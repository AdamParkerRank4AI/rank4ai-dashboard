#!/usr/bin/env python3
"""
build_feature_coverage.py — local builder that scans each fleet repo ON DISK
and reports which high-end fleet features each site has shipped.

Mirrors the JSON shape of fleet_baseline_check.py -> fleet_baseline.json, but
instead of probing live HTML this reads the source tree of each repo so we can
see (at a glance, in a grid) which site is MISSING which feature.

Output: src/data/live/feature_coverage.json
Consumed by: src/components/FeatureCoverageTile.astro
"""
import os
import re
import json
from datetime import datetime, timezone
from pathlib import Path

LIVE = Path(os.path.expanduser("~/rank4ai-dashboard/src/data/live"))

SITES = {
    "rank4ai":            "~/rank4ai-site",
    "market-invoice":     "~/compare-invoice-finance",
    "seocompare":         "~/compareaiseo",
    "bestbusinessloans":  "~/bestbusinessloans",
    "fundbiz":            "~/fundbiz",
    "cardmachines":       "~/cardmachines",
    "kartapay":           "~/kartapay",
    "peptideclear":       "~/ukmetabolic",
}

CHECKS_ORDER = [
    "strict_lint_gate",
    "fleetcore_sha_pin",
    "llms_txt",
    "llms_full_txt",
    "ai_txt",
    "answer_capsules",
    "graph_sameas",
    "agent_data_layer",
    "dataset_schema",
    "og_png",
    "claude_md",
]

CHECK_LABELS = {
    "strict_lint_gate": "Lint gate",
    "fleetcore_sha_pin": "FC SHA pin",
    "llms_txt": "llms.txt",
    "llms_full_txt": "llms-full",
    "ai_txt": "ai.txt",
    "answer_capsules": "Answer caps",
    "graph_sameas": "sameAs",
    "agent_data_layer": "Agent API",
    "dataset_schema": "Dataset",
    "og_png": "OG PNG",
    "claude_md": "CLAUDE.md",
}

# directories we never want to descend into when grepping src/
SKIP_DIRS = {"node_modules", ".git", "dist", ".astro", ".cache", "coverage"}


def load_package_json(root: Path):
    pj = root / "package.json"
    if not pj.exists():
        return None
    try:
        return json.loads(pj.read_text(encoding="utf-8"))
    except Exception:
        return None


def file_contains(path: Path, needles, max_bytes=2_000_000):
    """True if any needle (str) appears in the file. Binary-safe-ish."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read(max_bytes)
    except Exception:
        return False
    return any(n in data for n in needles)


def grep_tree_hit(roots, needles, exts=None):
    """Return short detail string of first hit, else None."""
    for root in roots:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if exts and not fn.lower().endswith(exts):
                    continue
                fp = Path(dirpath) / fn
                if file_contains(fp, needles):
                    rel = os.path.relpath(fp, root)
                    return rel
    return None


# Source file extensions we care about for grep checks
SRC_EXTS = (".astro", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
            ".json", ".md", ".mdx", ".html", ".vue", ".svelte")


def check_strict_lint_gate(root: Path):
    lint = (root / "scripts" / "fleet-lint.cjs").exists()
    pj = load_package_json(root)
    postbuild = ""
    if pj:
        postbuild = (pj.get("scripts", {}) or {}).get("postbuild", "") or ""
    has_strict = "FLEET_LINT_STRICT=1" in postbuild and "fleet-lint" in postbuild
    if lint and has_strict:
        return {"pass": True, "detail": "fleet-lint.cjs + strict postbuild"}
    missing = []
    if not lint:
        missing.append("no fleet-lint.cjs")
    if not has_strict:
        missing.append("postbuild not strict")
    return {"pass": False, "detail": "; ".join(missing)}


def check_fleetcore_sha_pin(root: Path):
    pj = load_package_json(root)
    if not pj:
        return {"pass": False, "detail": "no package.json"}
    deps = {}
    for key in ("dependencies", "devDependencies"):
        deps.update(pj.get(key, {}) or {})
    val = deps.get("@rank4ai/fleet-core")
    if val is None:
        return {"pass": True, "detail": "no fleet-core dep"}
    if re.search(r"#[0-9a-f]{40}$", val):
        m = re.search(r"#([0-9a-f]{40})$", val)
        return {"pass": True, "detail": f"pinned #{m.group(1)[:7]}"}
    if re.search(r"#v\d+\.\d+\.\d+$", val):
        m = re.search(r"#(v\d+\.\d+\.\d+)$", val)
        return {"pass": False, "detail": f"moveable tag {m.group(1)}"}
    return {"pass": False, "detail": f"not SHA-pinned ({val[-30:]})"}


def check_file_exists(root: Path, rel, label):
    p = root / rel
    return {"pass": p.exists(), "detail": "present" if p.exists() else f"{label} missing"}


def check_grep(root: Path, subdirs, needles, label):
    roots = [root / s for s in subdirs]
    hit = grep_tree_hit(roots, needles, exts=SRC_EXTS)
    if hit:
        return {"pass": True, "detail": f"in {hit}"}
    return {"pass": False, "detail": f"{label} not found"}


def check_agent_data_layer(root: Path):
    candidates = [
        ("public/openapi.json", (root / "public" / "openapi.json").exists()),
        ("functions/mcp.ts", (root / "functions" / "mcp.ts").exists()),
        ("public/.well-known/mcp.json", (root / "public" / ".well-known" / "mcp.json").exists()),
        ("functions/api/", (root / "functions" / "api").is_dir()),
    ]
    hits = [name for name, present in candidates if present]
    if hits:
        return {"pass": True, "detail": ", ".join(hits)}
    return {"pass": False, "detail": "no openapi/mcp/functions-api"}


def check_og_png(root: Path):
    default = root / "public" / "og-default.png"
    if default.exists() and default.stat().st_size > 5000:
        return {"pass": True, "detail": f"og-default.png {default.stat().st_size // 1024}KB"}
    # fall back to any public/og*.png > 5000 bytes
    pub = root / "public"
    if pub.is_dir():
        for fp in pub.rglob("og*.png"):
            try:
                if fp.stat().st_size > 5000:
                    return {"pass": True, "detail": f"{fp.name} {fp.stat().st_size // 1024}KB"}
            except Exception:
                continue
    if default.exists():
        return {"pass": False, "detail": f"og-default.png too small ({default.stat().st_size}B)"}
    return {"pass": False, "detail": "no og*.png > 5KB"}


def check_site(site_id: str, root: Path):
    checks = {}
    checks["strict_lint_gate"] = check_strict_lint_gate(root)
    checks["fleetcore_sha_pin"] = check_fleetcore_sha_pin(root)
    checks["llms_txt"] = check_file_exists(root, "public/llms.txt", "llms.txt")
    checks["llms_full_txt"] = check_file_exists(root, "public/llms-full.txt", "llms-full.txt")
    checks["ai_txt"] = check_file_exists(root, "public/ai.txt", "ai.txt")
    checks["answer_capsules"] = check_grep(root, ["src"], ["answer-capsule"], "answer-capsule")
    checks["graph_sameas"] = check_grep(root, ["src"], ["sameAs"], "sameAs")
    checks["agent_data_layer"] = check_agent_data_layer(root)
    checks["dataset_schema"] = check_grep(root, ["src", "public"], ['"Dataset"', "'Dataset'"], "Dataset")
    checks["og_png"] = check_og_png(root)
    checks["claude_md"] = check_file_exists(root, "CLAUDE.md", "CLAUDE.md")

    n_checks = len(checks)
    n_fail = sum(1 for c in checks.values() if not c.get("pass"))
    return {
        "site": site_id,
        "checks": checks,
        "summary": {
            "checks": n_checks,
            "failed": n_fail,
            "pass_rate": round((n_checks - n_fail) / max(1, n_checks) * 100, 1),
        },
    }


def main():
    sites = {}
    summary = {"total_sites": 0, "fully_covered": 0, "total_checks": 0, "failed_checks": 0}

    for site_id, path in SITES.items():
        root = Path(os.path.expanduser(path))
        print(f"scanning {site_id} ({root})...")
        if not root.exists():
            print(f"  ! repo missing on disk — skipping")
            continue
        r = check_site(site_id, root)
        sites[site_id] = r
        n_checks = r["summary"]["checks"]
        n_fail = r["summary"]["failed"]
        summary["total_sites"] += 1
        if n_fail == 0:
            summary["fully_covered"] += 1
        summary["total_checks"] += n_checks
        summary["failed_checks"] += n_fail
        if n_fail:
            print(f"  ✗ {n_fail}/{n_checks} missing:")
            for cname, c in r["checks"].items():
                if not c.get("pass"):
                    print(f"     · {cname}: {c.get('detail','')}")
        else:
            print(f"  ✓ all {n_checks} present")

    output = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "checks_order": CHECKS_ORDER,
        "check_labels": CHECK_LABELS,
        "sites": sites,
    }
    LIVE.mkdir(parents=True, exist_ok=True)
    out_path = LIVE / "feature_coverage.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n→ {out_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
