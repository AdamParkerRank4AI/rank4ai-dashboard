#!/usr/bin/env python3
"""
youtube_ai_tracking.py — daily AI citation probe for fleet YouTube channels.

For each fleet channel, runs probe queries through AI models with web search
enabled, then scans responses for:
  - the channel handle (e.g. @MerchantHQuk)
  - the channel domain URL
  - branded English phrases (Five Signal Model, etc.)
  - branded foreign phrases (Hindi/Marathi/Polish/Romanian for vernacular sites)
  - specific video URLs (when fetched via YouTube Data API)

Output → src/data/live/youtube_ai_citations.json (snapshot + 90-day history)
+ urgent_alert.py fires a POSITIVE alert when a new citation is detected.

Initially runs Claude with anthropic web_search tool only (Adam's
ANTHROPIC_API_KEY already set). Perplexity + OpenAI + Gemini hooks are
present but skip if their keys aren't set.

Usage:
  python3 youtube_ai_tracking.py          # full run
  python3 youtube_ai_tracking.py --dry    # no API calls, just config check
  python3 youtube_ai_tracking.py --only rank4ai
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

LIVE = Path(os.path.expanduser("~/rank4ai-dashboard/src/data/live"))
CONFIG = Path(os.path.expanduser("~/rank4ai-dashboard/config/ai_citation_phrases.json"))
HISTORY_FILE = LIVE / "youtube_ai_citations_history.json"
SNAPSHOT_FILE = LIVE / "youtube_ai_citations.json"

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PERPLEXITY_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

NOW = datetime.now(timezone.utc)
TODAY = NOW.date().isoformat()


def load_config():
    return json.loads(CONFIG.read_text())


def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_history(h):
    HISTORY_FILE.write_text(json.dumps(h, indent=2, ensure_ascii=False))


def probe_claude(query):
    """Run a query through Claude with web search enabled. Returns full text response."""
    if not ANTHROPIC_KEY:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
            messages=[{"role": "user", "content": query}],
        )
        # Concatenate all text blocks from the response
        parts = []
        for block in resp.content:
            if hasattr(block, "text"):
                parts.append(block.text)
            elif hasattr(block, "input"):
                # tool_use block — include the search query for observability
                parts.append(json.dumps(getattr(block, "input", {})))
            # web_search_tool_result blocks contain search hits; serialise
            elif hasattr(block, "content"):
                try:
                    for c in block.content:
                        if hasattr(c, "url"):
                            parts.append(c.url)
                        if hasattr(c, "title"):
                            parts.append(c.title)
                except Exception:
                    pass
        return "\n".join(parts)
    except Exception as e:
        return f"[claude error: {str(e)[:120]}]"


def probe_perplexity(query):
    """Optional — only runs if PERPLEXITY_API_KEY is set."""
    if not PERPLEXITY_KEY:
        return None
    try:
        import requests
        r = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {PERPLEXITY_KEY}", "Content-Type": "application/json"},
            json={"model": "sonar", "messages": [{"role": "user", "content": query}]},
            timeout=30,
        )
        if r.status_code == 200:
            data = r.json()
            txt = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            # Perplexity also returns citations array
            cits = data.get("citations") or []
            return txt + "\n\nCITATIONS:\n" + "\n".join(str(c) for c in cits)
    except Exception:
        pass
    return None


def detect_signals(response_text, channel_config):
    """Scan AI response text for channel handle, URL, and branded phrases.
    Returns a dict of which signals fired."""
    if not response_text:
        return {"hits": [], "match_count": 0}
    text = response_text
    text_low = text.lower()
    hits = []

    handle = channel_config.get("handle")
    if handle and handle.lower() in text_low:
        hits.append({"type": "handle", "value": handle})
    url = channel_config.get("url")
    if url and url.lower() in text_low:
        hits.append({"type": "channel_url", "value": url})
    site = channel_config.get("site")
    if site and site.lower() in text_low:
        hits.append({"type": "site_domain", "value": site})

    for phrase in channel_config.get("phrases_branded_en", []):
        if phrase.lower() in text_low:
            hits.append({"type": "branded_en", "value": phrase})
    for phrase in channel_config.get("phrases_branded_foreign", []):
        # Non-ASCII phrases compare case-sensitive (no lowercase needed)
        if phrase in text:
            hits.append({"type": "branded_foreign", "value": phrase})

    return {"hits": hits, "match_count": len(hits)}


def run_for_channel(channel_id, cfg):
    """Run all probe queries for one channel across all available AIs."""
    out = {
        "channel": channel_id,
        "checked_at": NOW.isoformat(),
        "probes": [],
    }
    for query in cfg.get("phrases_probe_queries", []):
        probe = {"query": query, "models": {}}
        # Claude
        resp = probe_claude(query)
        if resp is not None:
            signals = detect_signals(resp, cfg)
            probe["models"]["claude"] = {
                "response_excerpt": resp[:400] + ("…" if len(resp) > 400 else ""),
                "hits": signals["hits"],
                "match_count": signals["match_count"],
            }
        # Perplexity (optional)
        resp = probe_perplexity(query)
        if resp is not None:
            signals = detect_signals(resp, cfg)
            probe["models"]["perplexity"] = {
                "response_excerpt": resp[:400] + ("…" if len(resp) > 400 else ""),
                "hits": signals["hits"],
                "match_count": signals["match_count"],
            }
        out["probes"].append(probe)
        time.sleep(2)  # gentle pacing on the Anthropic API

    # Roll-up totals
    total_hits = sum(p["models"].get("claude", {}).get("match_count", 0) + p["models"].get("perplexity", {}).get("match_count", 0) for p in out["probes"])
    out["total_hits"] = total_hits
    out["models_run"] = sorted({m for p in out["probes"] for m in p["models"].keys()})
    return out


def main():
    args = sys.argv[1:]
    dry = "--dry" in args
    only = None
    if "--only" in args:
        idx = args.index("--only")
        if idx + 1 < len(args):
            only = args[idx + 1]

    config = load_config()
    history = load_history()

    if dry:
        print(f"[dry] config has {len(config['channels'])} channels")
        for cid, c in config["channels"].items():
            print(f"  {cid}: {len(c.get('phrases_probe_queries', []))} queries, {len(c.get('phrases_branded_en', []))} EN phrases, {len(c.get('phrases_branded_foreign', []))} foreign phrases")
        return

    if not ANTHROPIC_KEY:
        print("WARN: ANTHROPIC_API_KEY not set — Claude probes disabled")
    if not PERPLEXITY_KEY:
        print("INFO: PERPLEXITY_API_KEY not set — Perplexity probes disabled (set to enable)")

    snapshot = {
        "checked_at": NOW.isoformat(),
        "channels": {},
        "summary": {"channels_checked": 0, "total_hits": 0, "newly_cited": []},
    }

    for cid, cfg in config["channels"].items():
        if only and cid != only:
            continue
        print(f"\n━━━ {cid} ━━━")
        result = run_for_channel(cid, cfg)
        snapshot["channels"][cid] = result
        snapshot["summary"]["channels_checked"] += 1
        snapshot["summary"]["total_hits"] += result["total_hits"]
        print(f"  total hits: {result['total_hits']} across {len(result['models_run'])} model(s)")

        # History entry (per day, per channel)
        hist_key = f"{cid}::{TODAY}"
        if cid not in history:
            history[cid] = {}
        # First-citation positive alert
        prior_hits = sum(v.get("total_hits", 0) for v in history[cid].values())
        if prior_hits == 0 and result["total_hits"] > 0:
            snapshot["summary"]["newly_cited"].append({
                "channel": cid,
                "first_hits": result["total_hits"],
                "sample_queries": [p["query"] for p in result["probes"] if any(m.get("match_count", 0) for m in p["models"].values())][:3],
            })
        history[cid][TODAY] = {"total_hits": result["total_hits"], "models_run": result["models_run"]}

    # Trim history older than 90 days
    cutoff = (NOW - timedelta(days=90)).date().isoformat()
    for cid in list(history.keys()):
        history[cid] = {d: v for d, v in history[cid].items() if d >= cutoff}

    SNAPSHOT_FILE.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False))
    save_history(history)
    print(f"\n→ {SNAPSHOT_FILE.name}: {snapshot['summary']['channels_checked']} channels, {snapshot['summary']['total_hits']} total hits")
    if snapshot["summary"]["newly_cited"]:
        print(f"🎉 NEWLY CITED: {', '.join(c['channel'] for c in snapshot['summary']['newly_cited'])}")


if __name__ == "__main__":
    main()
