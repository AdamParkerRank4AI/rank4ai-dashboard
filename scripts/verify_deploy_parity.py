#!/usr/bin/env python3
"""Deploy-verification guardrail.

For each Pages project: compare the latest commit on origin/main against
the commit of the current canonical (production) CF Pages deployment.
If they diverge, it means a commit didn't auto-deploy (webhook broken,
git push never reached CF, build failed silently, etc.).

Writes src/data/live/deploy_parity.json so the dashboard home banner can
show a red warning. Exits 0 always (intended to run in refresh_all.py
alongside other checks), but sends an email alert on drift.

Also optionally calls the project's deploy hook to auto-trigger a rebuild
when drift is detected, controlled by AUTO_REDEPLOY_ON_DRIFT env var.
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)
try:
    from notify import send_failure_alert
except Exception:
    send_failure_alert = None

LIVE = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
OUTPUT = os.path.join(LIVE, "deploy_parity.json")

AUTO_REDEPLOY_ON_DRIFT = os.environ.get("AUTO_REDEPLOY_ON_DRIFT", "false").lower() == "true"

# Project → (account_id, CF token env var, GitHub repo, local path, deploy hook id)
PROJECTS = [
    ("rank4ai-dashboard",
     "a29a9e6a4fa4965762858586f129b445",
     "CF_TOKEN_RANK4AI",
     "AdamParkerRank4AI/rank4ai-dashboard",
     os.path.expanduser("~/rank4ai-dashboard"),
     "0064972e-334f-4b49-8348-e3f666f13c04"),
    ("rank4ai-preview",
     "a29a9e6a4fa4965762858586f129b445",
     "CF_TOKEN_RANK4AI",
     "AdamParkerRank4AI/rank4ai-preview",
     os.path.expanduser("~/rank4ai-site"),
     "fbb51eae-c449-412c-99f7-a01686b1ff32"),
    ("market-invoice",
     "a29a9e6a4fa4965762858586f129b445",
     "CF_TOKEN_RANK4AI",
     "AdamParkerRank4AI/market-invoice",
     os.path.expanduser("~/compare-invoice-finance"),
     "3e647ae6-8048-4014-b424-ccb137adfa5f"),
    ("seocompare",
     "927d3dd61a9375f0c8185df7b2a1764e",
     "CF_TOKEN_MUSWELLROSE",
     "AdamParkerRank4AI/seocompare",
     os.path.expanduser("~/compareaiseo"),
     "2c148416-94e3-4fb1-a91d-84b5d012b229"),
]


def http_get_json(url, headers=None):
    req = Request(url, headers=headers or {})
    with urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def git_latest_main(repo_path):
    """Get the latest commit sha + subject on origin/main for a local repo."""
    try:
        # Fetch to ensure fresh, quiet
        subprocess.run(["git", "-C", repo_path, "fetch", "origin", "main", "--quiet"],
                       check=False, timeout=30, capture_output=True)
        sha = subprocess.check_output(
            ["git", "-C", repo_path, "rev-parse", "origin/main"],
            text=True, timeout=10).strip()
        subject = subprocess.check_output(
            ["git", "-C", repo_path, "log", "-1", "--format=%s", "origin/main"],
            text=True, timeout=10).strip()
        return sha, subject
    except Exception as e:
        return None, f"git error: {e}"


def cf_canonical_deploy(account_id, project, token):
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/{project}"
    try:
        data = http_get_json(url, {"Authorization": f"Bearer {token}"})
        r = data.get("result", {})
        canonical = r.get("canonical_deployment") or {}
        latest = r.get("latest_deployment") or {}
        # Prefer canonical (what's actually serving). Fall back to latest.
        dep = canonical or latest
        trig = dep.get("deployment_trigger", {}) or {}
        meta = trig.get("metadata", {}) or {}
        return {
            "deploy_id": dep.get("short_id"),
            "deploy_full_id": dep.get("id"),
            "commit_sha": meta.get("commit_hash"),
            "commit_msg": meta.get("commit_message", "")[:80],
            "created_on": dep.get("created_on"),
            "status": (dep.get("latest_stage") or {}).get("status"),
        }
    except Exception as e:
        return {"error": str(e)}


def trigger_redeploy(hook_id):
    try:
        req = Request(
            f"https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/{hook_id}",
            method="POST",
        )
        with urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode()).get("result", {}).get("id")
    except Exception as e:
        return f"trigger error: {e}"


def main():
    results = []
    any_drift = False
    redeploys_triggered = []

    for project, account_id, env_key, repo, local_path, hook_id in PROJECTS:
        token = os.environ.get(env_key)
        entry = {
            "project": project,
            "repo": repo,
            "git_sha": None,
            "git_subject": None,
            "deploy_sha": None,
            "deploy_id": None,
            "deploy_created": None,
            "status": "unknown",
        }

        sha, subject = git_latest_main(local_path)
        entry["git_sha"] = sha
        entry["git_subject"] = subject

        if not token:
            entry["status"] = "no_token"
            entry["note"] = f"{env_key} not set in environment"
        else:
            dep = cf_canonical_deploy(account_id, project, token)
            if dep.get("error"):
                entry["status"] = "api_error"
                entry["note"] = dep["error"]
            else:
                entry["deploy_sha"] = dep.get("commit_sha")
                entry["deploy_id"] = dep.get("deploy_id")
                entry["deploy_created"] = dep.get("created_on")
                entry["deploy_msg"] = dep.get("commit_msg")
                if sha and dep.get("commit_sha"):
                    if sha == dep["commit_sha"]:
                        entry["status"] = "in_sync"
                    elif sha.startswith(dep["commit_sha"]) or dep["commit_sha"].startswith(sha):
                        entry["status"] = "in_sync"
                    else:
                        entry["status"] = "drift"
                        any_drift = True
                        # If we can, trigger a redeploy to self-heal
                        if AUTO_REDEPLOY_ON_DRIFT and hook_id:
                            trig = trigger_redeploy(hook_id)
                            entry["auto_redeploy"] = trig
                            redeploys_triggered.append(f"{project} (deploy {trig})")

        results.append(entry)

    payload = {
        "checked_at": datetime.now().isoformat(),
        "auto_redeploy_on_drift": AUTO_REDEPLOY_ON_DRIFT,
        "any_drift": any_drift,
        "projects": results,
    }
    with open(OUTPUT, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Deploy parity: {sum(1 for r in results if r['status']=='in_sync')} in sync / "
          f"{sum(1 for r in results if r['status']=='drift')} drift / "
          f"{sum(1 for r in results if r['status'] not in ('in_sync','drift'))} unknown")
    for r in results:
        marker = {"in_sync": "✓", "drift": "⚠", "no_token": "?", "api_error": "!", "unknown": "?"}.get(r["status"], "?")
        print(f"  {marker} {r['project']:<22} git={(r['git_sha'] or 'n/a')[:7]}  deploy={(r['deploy_sha'] or 'n/a')[:7]}  [{r['status']}]")

    if any_drift and send_failure_alert:
        lines = []
        for r in results:
            if r["status"] == "drift":
                lines.append(
                    f"{r['project']}: git={r['git_sha'][:7]} ({r['git_subject']}) "
                    f"vs deploy={(r['deploy_sha'] or 'n/a')[:7]} ({r.get('deploy_msg','')})"
                )
        if redeploys_triggered:
            lines.append(f"Auto-triggered redeploys: {', '.join(redeploys_triggered)}")
        else:
            lines.append("AUTO_REDEPLOY_ON_DRIFT=false — manual action needed.")
        try:
            send_failure_alert("Deploy parity drift", lines, log_file="/tmp/deploy_parity.log")
        except Exception as e:
            print(f"(alert send failed: {e})")


if __name__ == "__main__":
    main()
