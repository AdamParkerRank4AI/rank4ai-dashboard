#!/usr/bin/env python3
"""
Fetch YouTube analytics for fleet channels.

Two APIs:
- YouTube Data API v3        → public-facing data (subs, total views, videos)
- YouTube Analytics API v2   → traffic source breakdown (the AI-referrer signal)

The AI-referrer signal is the unique value here — nothing else in the fleet
stack measures Perplexity/ChatGPT/Gemini/Claude picking up YouTube videos.

OAuth scope handling:
The PC channel's existing token (minted by pipeline/auth.js) only has
youtube.upload scope. Analytics API requires yt-analytics.readonly +
youtube.readonly. Until Adam re-auths with all three scopes, this script
emits status='auth_pending' for that channel and does not crash.

Token file shape: node-style JSON written by googleapis (Node SDK).
  { access_token, refresh_token, scope, token_type, expiry_date }
We translate that into google.oauth2.credentials.Credentials at load.

Output: ~/rank4ai-dashboard/src/data/live/youtube.json
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "youtube.json")

# AI referrers we track explicitly. Anything else falls into "other".
# Keys are the substring we look for inside insightTrafficSourceDetail
# (the raw referrer host string YouTube returns).
AI_REFERRER_HOSTS = [
    "perplexity.ai",
    "chat.openai.com",
    "chatgpt.com",
    "gemini.google.com",
    "bard.google.com",
    "claude.ai",
    "copilot.microsoft.com",
    "you.com",
    "phind.com",
    "consensus.app",
]

# Required scopes for both Data + Analytics APIs.
REQUIRED_SCOPES = {
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
}

CHANNELS = {
    "peptideclear": {
        "channel_id": "UCJ9AtfrSEkydOUdgky1bj0g",
        "site": "peptideclear.co.uk",
        "credentials_dir": "~/automations/peptideclear-youtube/credentials",
    },
    "merchanthq": {
        "channel_id": "UCkk5Whgr4TsTt5qBI9QkLbQ",
        "site": "merchanthq.co.uk",
        "credentials_dir": "~/automations/merchanthq-youtube/credentials",
    },
    # Kartapay channel_id TBC. R4 / MI channels not yet created.
    "kartapay": {
        "channel_id": None,
        "site": "kartapay.co.uk",
        "credentials_dir": "~/automations/kartapay-youtube/credentials",
    },
}


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso8601_duration(s: str) -> int:
    """Parse YouTube's ISO8601 video duration ('PT1M23S') into seconds.
    Cheap, no isodate dep."""
    if not s or not s.startswith("PT"):
        return 0
    s = s[2:]
    total = 0
    num = ""
    for ch in s:
        if ch.isdigit():
            num += ch
        elif ch == "H":
            total += int(num or 0) * 3600
            num = ""
        elif ch == "M":
            total += int(num or 0) * 60
            num = ""
        elif ch == "S":
            total += int(num or 0)
            num = ""
    return total


def _load_credentials(cred_dir: Path):
    """Translate node-style token.json into a google-auth Credentials.

    Returns (creds, scopes_set) or (None, reason) on failure.
    """
    client_secret_path = cred_dir / "client_secret.json"
    token_path = cred_dir / "token.json"

    if not client_secret_path.exists():
        return None, "client_secret_missing"
    if not token_path.exists():
        return None, "token_missing"

    try:
        with open(client_secret_path) as f:
            raw_secret = json.load(f)
        client_info = raw_secret.get("installed") or raw_secret.get("web") or {}
        client_id = client_info.get("client_id")
        client_secret = client_info.get("client_secret")
        if not client_id or not client_secret:
            return None, "client_secret_malformed"

        with open(token_path) as f:
            tok = json.load(f)

        scope_str = tok.get("scope", "") or ""
        scopes = set(scope_str.split()) if scope_str else set()

        from google.oauth2.credentials import Credentials

        creds = Credentials(
            token=tok.get("access_token"),
            refresh_token=tok.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=list(scopes) if scopes else None,
        )
        return creds, scopes
    except Exception as e:
        return None, f"creds_load_error:{type(e).__name__}:{str(e)[:80]}"


def _refresh_if_needed(creds):
    """Force refresh — node-minted tokens often look valid but 401."""
    try:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        return True, None
    except Exception as e:
        msg = str(e)
        # Insufficient scope shows up as RefreshError mentioning the scope.
        if "insufficient" in msg.lower() or "invalid_scope" in msg.lower():
            return False, "insufficient_scope"
        return False, f"refresh_failed:{msg[:120]}"


def _is_insufficient_scope_error(err: Exception) -> bool:
    msg = str(err).lower()
    if "insufficient" in msg and "scope" in msg:
        return True
    # HttpError from googleapiclient
    status = getattr(err, "resp", None)
    if status is not None and getattr(status, "status", None) == 403 and "insufficient" in msg:
        return True
    return False


def _persist_refreshed_token(cred_dir: Path, creds) -> None:
    """Write the new access_token back to token.json so Node side picks it up too."""
    token_path = cred_dir / "token.json"
    try:
        with open(token_path) as f:
            tok = json.load(f)
        tok["access_token"] = creds.token
        if creds.expiry:
            # expiry is naive UTC; google-auth stores it as such.
            tok["expiry_date"] = int(creds.expiry.replace(tzinfo=timezone.utc).timestamp() * 1000)
        with open(token_path, "w") as f:
            json.dump(tok, f, indent=2)
    except Exception:
        # Non-fatal — token still works in-memory for this run.
        pass


def fetch_data_api(yt_data, channel_id: str) -> dict:
    """channels.list → subs/views/videoCount + uploads playlist.
    Then playlistItems → latest 10 video IDs.
    Then videos.list → per-video viewCount, duration, visibility."""
    out = {
        "subscribers": 0,
        "total_views": 0,
        "video_count": 0,
        "latest_videos": [],
    }

    ch_resp = yt_data.channels().list(
        part="statistics,contentDetails",
        id=channel_id,
    ).execute()

    items = ch_resp.get("items") or []
    if not items:
        return out
    ch = items[0]
    stats = ch.get("statistics", {})
    out["subscribers"] = int(stats.get("subscriberCount", 0) or 0)
    out["total_views"] = int(stats.get("viewCount", 0) or 0)
    out["video_count"] = int(stats.get("videoCount", 0) or 0)

    uploads_pl = (ch.get("contentDetails", {}).get("relatedPlaylists", {}) or {}).get("uploads")
    if not uploads_pl:
        return out

    # Brand-new channels (or channels with only unlisted videos) return 404
    # on playlistItems for the auto-generated uploads playlist. Treat as empty.
    try:
        pl_resp = yt_data.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_pl,
            maxResults=10,
        ).execute()
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            return out
        raise

    video_ids = []
    snippets = {}
    for item in pl_resp.get("items", []):
        vid = (item.get("contentDetails") or {}).get("videoId")
        if not vid:
            continue
        video_ids.append(vid)
        snippets[vid] = item.get("snippet", {})

    if not video_ids:
        return out

    v_resp = yt_data.videos().list(
        part="snippet,contentDetails,status,statistics",
        id=",".join(video_ids),
    ).execute()

    videos = []
    for v in v_resp.get("items", []):
        vid = v["id"]
        sn = v.get("snippet", {})
        cd = v.get("contentDetails", {})
        st = v.get("status", {})
        stt = v.get("statistics", {})
        videos.append({
            "id": vid,
            "title": sn.get("title", ""),
            "uploaded": (sn.get("publishedAt", "") or "")[:10],
            "duration_seconds": _parse_iso8601_duration(cd.get("duration", "")),
            "visibility": st.get("privacyStatus", "unknown"),
            "views": int(stt.get("viewCount", 0) or 0),
        })
    # Preserve playlist order (newest first)
    videos.sort(key=lambda v: v["uploaded"], reverse=True)
    out["latest_videos"] = videos
    return out


def fetch_analytics(yt_analytics, channel_id: str) -> dict:
    """28-day Analytics pull: AI-referrer breakdown + watch minutes + top videos."""
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=28)
    start_s = start.isoformat()
    end_s = end.isoformat()
    ids = f"channel=={channel_id}"

    out = {
        "watch_minutes_28d": 0.0,
        "ai_referrers_28d": {h: 0 for h in AI_REFERRER_HOSTS},
        "top_videos_28d": [],
        "_window": {"start": start_s, "end": end_s},
    }
    out["ai_referrers_28d"]["other"] = 0

    # 1. Traffic source breakdown (the AI-citation signal).
    # We restrict to EXT_URL since AI search engines arrive as external referrers.
    try:
        ts_resp = yt_analytics.reports().query(
            ids=ids,
            startDate=start_s,
            endDate=end_s,
            metrics="views,estimatedMinutesWatched",
            dimensions="insightTrafficSourceDetail",
            filters="insightTrafficSourceType==EXT_URL",
            maxResults=200,
            sort="-views",
        ).execute()
        for row in ts_resp.get("rows", []) or []:
            referrer = (row[0] or "").lower()
            views = int(row[1] or 0)
            matched = False
            for host in AI_REFERRER_HOSTS:
                if host in referrer:
                    out["ai_referrers_28d"][host] = out["ai_referrers_28d"].get(host, 0) + views
                    matched = True
                    break
            if not matched:
                out["ai_referrers_28d"]["other"] += views
    except Exception as e:
        if _is_insufficient_scope_error(e):
            raise
        out["ai_referrers_error"] = str(e)[:160]

    # 2. Total watch minutes (last 28 days).
    try:
        wm_resp = yt_analytics.reports().query(
            ids=ids,
            startDate=start_s,
            endDate=end_s,
            metrics="estimatedMinutesWatched",
        ).execute()
        rows = wm_resp.get("rows", []) or []
        if rows:
            out["watch_minutes_28d"] = round(float(rows[0][0] or 0), 2)
    except Exception as e:
        if _is_insufficient_scope_error(e):
            raise
        out["watch_minutes_error"] = str(e)[:160]

    # 3. Top 5 videos by views in last 28 days.
    try:
        tv_resp = yt_analytics.reports().query(
            ids=ids,
            startDate=start_s,
            endDate=end_s,
            metrics="views,estimatedMinutesWatched",
            dimensions="video",
            maxResults=5,
            sort="-views",
        ).execute()
        for row in tv_resp.get("rows", []) or []:
            out["top_videos_28d"].append({
                "id": row[0],
                "views": int(row[1] or 0),
                "watch_minutes": round(float(row[2] or 0), 2),
            })
    except Exception as e:
        if _is_insufficient_scope_error(e):
            raise
        out["top_videos_error"] = str(e)[:160]

    return out


def fetch_channel(channel_key: str, channel_cfg: dict) -> dict:
    channel_id = channel_cfg.get("channel_id")
    site = channel_cfg.get("site")
    cred_dir = Path(os.path.expanduser(channel_cfg.get("credentials_dir", "")))

    base = {"channel_id": channel_id, "site": site}

    if not channel_id:
        base["status"] = "channel_id_pending"
        return base

    creds, reason_or_scopes = _load_credentials(cred_dir)
    if creds is None:
        base["status"] = "auth_pending"
        base["reason"] = reason_or_scopes
        return base

    scopes = reason_or_scopes
    if not REQUIRED_SCOPES.issubset(scopes):
        base["status"] = "auth_pending"
        base["reason"] = f"missing_scopes:have={sorted(scopes)}"
        return base

    ok, refresh_err = _refresh_if_needed(creds)
    if not ok:
        if refresh_err == "insufficient_scope":
            base["status"] = "auth_pending"
            base["reason"] = "insufficient_scope_on_refresh"
            return base
        base["status"] = "error"
        base["reason"] = refresh_err
        return base

    _persist_refreshed_token(cred_dir, creds)

    try:
        from googleapiclient.discovery import build
        yt_data = build("youtube", "v3", credentials=creds, cache_discovery=False)
        yt_analytics = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    except Exception as e:
        base["status"] = "error"
        base["reason"] = f"build_failed:{type(e).__name__}:{str(e)[:120]}"
        return base

    try:
        data = fetch_data_api(yt_data, channel_id)
    except Exception as e:
        if _is_insufficient_scope_error(e):
            base["status"] = "auth_pending"
            base["reason"] = "insufficient_scope_on_data_api"
            return base
        base["status"] = "error"
        base["reason"] = f"data_api_failed:{type(e).__name__}:{str(e)[:120]}"
        return base

    try:
        analytics = fetch_analytics(yt_analytics, channel_id)
    except Exception as e:
        if _is_insufficient_scope_error(e):
            base["status"] = "auth_pending"
            base["reason"] = "insufficient_scope_on_analytics"
            # Still return Data-API stats so the tile is partially useful.
            base.update(data)
            return base
        base["status"] = "error"
        base["reason"] = f"analytics_failed:{type(e).__name__}:{str(e)[:120]}"
        base.update(data)
        return base

    # Merge top_videos_28d titles from latest_videos when possible
    title_lookup = {v["id"]: v["title"] for v in data.get("latest_videos", [])}
    for tv in analytics.get("top_videos_28d", []):
        tv["title"] = title_lookup.get(tv["id"], "")

    base.update(data)
    base.update(analytics)
    base["status"] = "ok"
    return base


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = {
        "fetched_at": _now_utc_iso(),
        "channels": {},
    }
    for key, cfg in CHANNELS.items():
        print(f"Fetching YouTube data for {key}...")
        try:
            result = fetch_channel(key, cfg)
        except Exception as e:
            result = {
                "channel_id": cfg.get("channel_id"),
                "site": cfg.get("site"),
                "status": "error",
                "reason": f"unhandled:{type(e).__name__}:{str(e)[:120]}",
            }
        out["channels"][key] = result
        status = result.get("status", "unknown")
        if status == "ok":
            ai_total = sum(v for k, v in result.get("ai_referrers_28d", {}).items() if k != "other")
            print(f"  ok · subs={result.get('subscribers', 0)} · ai_views_28d={ai_total} · watch_min={result.get('watch_minutes_28d', 0)}")
        else:
            print(f"  {status}: {result.get('reason', '')}")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
