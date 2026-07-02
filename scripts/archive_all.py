#!/usr/bin/env python3
"""archive_all.py — keep EVERY bit of dashboard data, every day.

WHY (Adam, 2 Jul 2026): most of the dashboard's ~139 data files are fetched in
OVERWRITE mode — each daily refresh replaces the previous snapshot, so the raw
day-by-day history was being lost (only leads + bot hits, which live in Supabase,
were durable). This is one blanket archiver: it gzips the entire live data dir
(~2.5MB/day) and uploads a dated snapshot to Supabase Storage (durable, off the
laptop, reuses the service key). One mechanism captures every file — including any
new ones added later — with zero per-fetcher changes.

Storage layout (bucket 'dashboard-archive', private):
    live/YYYY/YYYY-MM-DD.tgz     full gzipped snapshot of src/data/live for that day

Also keeps the last 21 days locally in src/data/_archive/ (gitignored) for quick
access. Never raises in a way that breaks the daily refresh — archiving failure
must not stop the build/deploy.

Run: SUPABASE_SERVICE_KEY=... python3 scripts/archive_all.py
"""
import os
import sys
import glob
import tarfile
import urllib.request
from datetime import datetime, timezone

SUPABASE_URL = "https://tsscscjcxbzhicuuhter.supabase.co"
BUCKET = "dashboard-archive"


def _service_key():
    # Same resolution as every other fetcher: env first, then the on-disk file
    # (the launchd job has no env, so the file is how the cron authenticates).
    k = os.environ.get("SUPABASE_SERVICE_KEY")
    if k:
        return k.strip()
    p = os.path.expanduser("~/.supabase-service-key")
    if os.path.exists(p):
        with open(p) as f:
            return f.read().strip()
    return ""


SERVICE_KEY = _service_key()

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)
LIVE_DIR = os.path.join(PROJECT_DIR, "src", "data", "live")
LOCAL_ARCHIVE = os.path.join(PROJECT_DIR, "src", "data", "_archive")
LOCAL_KEEP_DAYS = 21


def make_snapshot(day):
    os.makedirs(LOCAL_ARCHIVE, exist_ok=True)
    path = os.path.join(LOCAL_ARCHIVE, f"{day}.tgz")
    with tarfile.open(path, "w:gz") as tar:
        # store paths relative to live dir so extraction is clean
        tar.add(LIVE_DIR, arcname="live")
    return path


def upload(path, day):
    if not SERVICE_KEY:
        print("archive_all: SUPABASE_SERVICE_KEY missing — LOCAL snapshot kept, upload skipped", file=sys.stderr)
        return False
    key = f"live/{day[:4]}/{day}.tgz"
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{key}"
    with open(path, "rb") as f:
        body = f.read()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/gzip",
        "x-upsert": "true",   # re-running the same day overwrites, never errors
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            ok = 200 <= r.status < 300
            print(f"archive_all: uploaded {key} ({len(body)//1024} KB) -> {r.status}")
            return ok
    except Exception as e:
        print(f"archive_all: upload FAILED for {key}: {e} (local copy kept)", file=sys.stderr)
        return False


def prune_local():
    files = sorted(glob.glob(os.path.join(LOCAL_ARCHIVE, "*.tgz")))
    for old in files[:-LOCAL_KEEP_DAYS]:
        try:
            os.remove(old)
        except OSError:
            pass


def main():
    if not os.path.isdir(LIVE_DIR):
        print(f"archive_all: live dir not found at {LIVE_DIR}", file=sys.stderr)
        return 0  # never fail the refresh
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        path = make_snapshot(day)
        upload(path, day)
        prune_local()
    except Exception as e:
        print(f"archive_all: non-fatal error {e}", file=sys.stderr)
    return 0  # ALWAYS 0 — archiving must never break the daily refresh


if __name__ == "__main__":
    sys.exit(main())
