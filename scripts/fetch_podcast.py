#!/usr/bin/env python3
"""
fetch_podcast.py — pull the rank4ai Buzzsprout show into the dashboard.

Writes src/data/live/podcast.json: show totals + the latest episodes, so the
PodcastTile can render downloads + cadence without hitting Buzzsprout at build.

The pipeline that PUBLISHES episodes is ~/rank4ai_content_pipeline/podcast_generate.py
(launchd com.rank4ai.podcast). This is the read-side only.

Currently single-show (rank4ai, Buzzsprout 2595013). Structured as a dict of
shows keyed by brand so other brands can be added later without a tile rewrite.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

# brand -> Buzzsprout show id. Add rows here when other brands get a show.
SHOWS = {
    "rank4ai": {"podcast_id": "2595013", "site": "rank4ai.co.uk"},
}

TOKEN = os.environ.get("BUZZSPROUT_API_TOKEN")
OUT = os.path.join(os.path.dirname(__file__), "..", "src", "data", "live", "podcast.json")


def fetch_episodes(podcast_id: str):
    url = f"https://www.buzzsprout.com/api/{podcast_id}/episodes.json?api_token={TOKEN}"
    req = urllib.request.Request(url, headers={"User-Agent": "rank4ai-dashboard/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def build_show(brand: str, cfg: dict):
    try:
        eps = fetch_episodes(cfg["podcast_id"])
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
        return {"status": "error", "reason": str(e), "site": cfg["site"]}

    # public episodes only (skip private/inactive)
    pub = [e for e in eps if not e.get("private") and not e.get("inactive_at")]
    pub.sort(key=lambda e: e.get("published_at") or "", reverse=True)

    total_plays = sum(int(e.get("total_plays") or 0) for e in pub)
    recent = [
        {
            "number": e.get("episode_number"),
            "title": e.get("title"),
            "published_at": e.get("published_at"),
            "duration": e.get("duration"),
            "plays": int(e.get("total_plays") or 0),
            "url": e.get("custom_url") or e.get("audio_url"),
        }
        for e in pub[:8]
    ]
    return {
        "status": "ok",
        "site": cfg["site"],
        "podcast_id": cfg["podcast_id"],
        "episode_count": len(pub),
        "total_plays": total_plays,
        "latest_published_at": pub[0].get("published_at") if pub else None,
        "recent": recent,
    }


def main():
    if not TOKEN:
        # No token (e.g. a scheduled run before the launchd plist reloaded with
        # BUZZSPROUT_API_TOKEN). Do NOT clobber good data — keep whatever's there.
        if os.path.exists(OUT):
            print("no BUZZSPROUT_API_TOKEN; leaving existing podcast.json untouched")
            return 0
        out = {"fetched_at": datetime.now(timezone.utc).isoformat(),
               "shows": {b: {"status": "auth_pending", "site": c["site"]} for b, c in SHOWS.items()}}
    else:
        out = {"fetched_at": datetime.now(timezone.utc).isoformat(),
               "shows": {b: build_show(b, c) for b, c in SHOWS.items()}}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    ok = sum(1 for s in out["shows"].values() if s.get("status") == "ok")
    print(f"podcast.json written: {ok}/{len(SHOWS)} shows ok -> {os.path.abspath(OUT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
