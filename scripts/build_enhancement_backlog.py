#!/usr/bin/env python3
"""Build the persistent per-site enhancement backlog (the action ledger).

The dashboard's finding feeds (striking_distance, content_decay, cluster_decisions,
conversion_leaks, title_lint, indexing_health) are point-in-time SNAPSHOTS — each
run overwrites the last, so an opportunity that appeared three weeks ago and was
never actioned simply vanishes. This script fixes that: it converts every feed
into concrete actions, BACKFILLS missed opportunities by replaying gsc_history.json
(query-level, ~3 weeks), and merges everything into a durable ledger that:

  - gives each action a STABLE id (same finding = same id across days)
  - tracks first_seen / last_seen (so "in striking distance since 24 May" shows)
  - never loses an open item just because today's snapshot dropped it
  - respects enhancement_done.json so a finished item is never resurfaced

Outputs:
  src/data/live/enhancement_backlog.json   (the ledger the tile renders)

Reads (never writes):
  src/data/live/enhancement_done.json       (id -> {done_at, note}; written by
                                             mark_enhancement_done.py)
"""
import json
import os
import hashlib
from datetime import datetime, date

LIVE = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
CLIENTS = os.path.expanduser("~/rank4ai-dashboard/src/data/clients.json")
BACKLOG = os.path.join(LIVE, "enhancement_backlog.json")
DONE = os.path.join(LIVE, "enhancement_done.json")

TODAY = date.today().isoformat()

# Striking-distance backfill thresholds (mirror build_striking_distance intent)
SD_POS_MIN, SD_POS_MAX = 10.5, 20.5
SD_MIN_IMPR = 15          # ignore long-tail noise
SD_TOP_PER_SITE = 15      # cap historical backfill per site


def load(name, default=None):
    p = os.path.join(LIVE, name)
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def num(v):
    return v if isinstance(v, (int, float)) else 0


def short_url(u):
    if not isinstance(u, str):
        return ""
    s = u.replace("https://", "").replace("http://", "")
    return "/" + s.split("/", 1)[1] if "/" in s else s


def mk_id(site, kind, key):
    h = hashlib.sha1(f"{site}|{kind}|{key}".encode()).hexdigest()[:8]
    return f"{site[:4]}-{kind[:3]}-{h}"


def domains():
    out = {}
    with open(CLIENTS) as f:
        for c in json.load(f):
            out[c["id"]] = c.get("domain")
    return out


DOMAIN = domains()


def full_url(site, path):
    d = DOMAIN.get(site)
    if not d:
        return path
    if path.startswith("http"):
        return path
    return f"https://{d}{path if path.startswith('/') else '/' + path}"


def add(actions, site, kind, key, label, detail, metric, score, link="", first_seen=TODAY):
    """Add or keep-the-strongest action keyed by stable id."""
    aid = mk_id(site, kind, key)
    cur = actions.get(aid)
    if cur and cur["score"] >= score and cur["first_seen"] <= first_seen:
        # keep stronger/older, but pull first_seen back if this evidence is older
        cur["first_seen"] = min(cur["first_seen"], first_seen)
        return
    actions[aid] = {
        "id": aid, "site": site, "kind": kind, "label": label, "detail": detail,
        "metric": metric, "score": round(score, 1), "link": link,
        "first_seen": min(first_seen, cur["first_seen"]) if cur else first_seen,
    }


def compute_today(actions):
    """Actions from the current snapshots."""
    SD = load("striking_distance.json").get("sites", {})
    for site, blk in SD.items():
        for q in (blk.get("top") or [])[:3]:
            pot = num(q.get("potential_clicks_at_page_1"))
            add(actions, site, "rank", q.get("query", ""),
                f'Push “{q.get("query","")}” to page 1',
                f'pos {num(q.get("position")):.1f} · {num(q.get("impressions")):,} impr',
                f'+{pot} clicks' if pot else f'{num(q.get("impressions"))} impr',
                pot * 12 + num(q.get("impressions")),
                link=q.get("query", ""))

    DEC = load("content_decay.json").get("sites", {})
    for site, blk in DEC.items():
        rows = ([dict(r, off=True) for r in (blk.get("dropped_off_page_1") or [])]
                + (blk.get("impressions_collapse") or [])
                + (blk.get("position_drop") or []))
        for r in rows[:3]:
            impr = num(r.get("impressions_now"))
            add(actions, site, "decay", r.get("query", ""),
                f'Refresh “{r.get("query","")}” — slipping',
                f'pos {num(r.get("position_before")):.0f}→{num(r.get("position_now")):.0f} · {impr:,} impr',
                f'{impr:,} impr at risk', impr * 1.2 + (200 if r.get("off") else 0),
                link=r.get("query", ""))

    CL = load("cluster_decisions.json").get("sites", {})
    for site, blk in CL.items():
        for cl in (blk.get("clusters") or []):
            if cl.get("recommendation") not in ("Consolidate", "Prune"):
                continue
            imp = num(cl.get("total_impressions"))
            add(actions, site, "consolidate", cl.get("theme", ""),
                f'{cl.get("recommendation")} {num(cl.get("n_urls"))} URLs · “{cl.get("theme","")}”',
                f'→ {short_url(cl.get("winner",""))} · {imp:,} impr' + (" · decaying" if cl.get("decaying") else ""),
                f'{imp:,} impr', imp * 1.5 + (50 if cl.get("recommendation") == "Consolidate" else 0),
                link=cl.get("winner", ""))

    CV = load("conversion_leaks.json").get("sites", {})
    for site, blk in CV.items():
        pages = sorted([p for p in (blk.get("pages") or []) if p.get("class") in ("DEAD_WEIGHT", "LEAK", "BOUNCE")],
                       key=lambda p: -num(p.get("humans")))
        for p in pages[:2]:
            add(actions, site, "cro", p.get("path", ""),
                f'Fix {str(p.get("class","")).lower().replace("_"," ")}: {short_url(p.get("path",""))}',
                f'{num(p.get("humans"))} humans · {num(p.get("scroll"))}% scroll · {num(p.get("active_s"))}s active',
                f'{num(p.get("humans"))} humans', num(p.get("humans")) * 6 + (30 if p.get("class") == "LEAK" else 0),
                link=full_url(site, p.get("path", "")))

    TL = load("title_lint.json").get("sites", {})
    for site, blk in TL.items():
        n = num(blk.get("flagged_count"))
        if n:
            eg = (blk.get("flagged") or [{}])[0]
            add(actions, site, "hygiene", "titles",
                f'Shorten {n} long title{"s" if n > 1 else ""}',
                (f'e.g. “{eg.get("title","")}” ({eg.get("length")} chars)' if eg else ""),
                f'{n} titles', n * 2, link=eg.get("url", ""))

    IX = load("indexing_health.json").get("per_site", {})
    for site, ix in IX.items():
        cov = ix.get("gsc_coverage") or {}
        if num(cov.get("not_indexed")) > 50:
            add(actions, site, "index", "not_indexed",
                f'Resolve indexing — {num(cov.get("not_indexed")):,} not indexed',
                f'{num(cov.get("indexed")):,}/{num(cov.get("total_known")):,} indexed ({cov.get("index_rate")}%)',
                f'{num(cov.get("not_indexed")):,} URLs', min(num(cov.get("not_indexed")), 1500) * 0.6 + 100)
        roll = ix.get("activity_rollup_today") or {}
        # Use the EFFECTIVE submission signal (Google API rollup + IndexNow), not the
        # stale per-URL log — so this only fires when indexing is genuinely stalled.
        if num(ix.get("submitted_today_effective")) == 0 and num(roll.get("sitemap_url_count")) > 0:
            last = ix.get("last_submission_at")
            last_s = last[:10] if last else "never"
            add(actions, site, "index", "indexnow_restart",
                f'Restart IndexNow — last {last_s}',
                f'{num(roll.get("sitemap_url_count")):,} URLs queued', f'{num(roll.get("sitemap_url_count")):,} queued', 95)


def backfill_striking_from_history(actions):
    """Replay gsc_history dates: any query that sat at pos 11–20 with real
    impressions on ANY past date is a missed opportunity — surface it with
    first_seen = the EARLIEST date it qualified (that's the age that's been lost)."""
    hist = load("gsc_history.json")
    if not isinstance(hist, dict):
        return
    # per site -> query -> {first_date, best_impr, last_pos}
    found = {}
    for d in sorted(hist):
        for site, blk in (hist[d] or {}).items():
            qs = (blk or {}).get("queries") or {}
            if not isinstance(qs, dict):
                continue
            for q, m in qs.items():
                pos, impr = num(m.get("position")), num(m.get("impressions"))
                if SD_POS_MIN < pos < SD_POS_MAX and impr >= SD_MIN_IMPR:
                    rec = found.setdefault(site, {}).setdefault(q, {"first": d, "impr": 0, "pos": pos})
                    rec["first"] = min(rec["first"], d)
                    rec["impr"] = max(rec["impr"], impr)
                    rec["pos"] = pos  # last seen position
    for site, qmap in found.items():
        top = sorted(qmap.items(), key=lambda kv: -kv[1]["impr"])[:SD_TOP_PER_SITE]
        for q, rec in top:
            age = (date.fromisoformat(TODAY) - date.fromisoformat(rec["first"])).days
            add(actions, site, "rank", q,
                f'Push “{q}” to page 1',
                f'pos ~{rec["pos"]:.0f} · {rec["impr"]:,} impr · seen since {rec["first"]}',
                f'{rec["impr"]:,} impr',
                rec["impr"] + (30 if age >= 14 else 0),  # nudge long-stale ones up
                link=q, first_seen=rec["first"])


def main():
    actions = {}
    compute_today(actions)
    backfill_striking_from_history(actions)

    prev = load("enhancement_backlog.json", {"items": []})
    existing = {it["id"]: it for it in prev.get("items", [])}
    done = load("enhancement_done.json", {})

    out = dict(existing)  # carry forward everything (don't lose open items)
    for aid, act in actions.items():
        if aid in out:
            o = out[aid]
            o.update({k: act[k] for k in ("label", "detail", "metric", "score", "link", "kind", "site")})
            o["first_seen"] = min(o.get("first_seen", TODAY), act["first_seen"])
            o["last_seen"] = TODAY
            o["seen_count"] = o.get("seen_count", 1) + 1
        else:
            out[aid] = {**act, "first_seen": act["first_seen"], "last_seen": TODAY,
                        "seen_count": 1, "status": "open"}

    # Apply the done ledger as the SINGLE SOURCE OF TRUTH — both directions.
    # An id in done.json is done; an id NOT in it is open (so an --undo actually
    # reopens, instead of the carried-forward 'done' status sticking forever).
    done = done or {}
    for aid, item in out.items():
        if aid in done:
            item["status"] = "done"
            item["done_at"] = done[aid].get("done_at")
            item["done_note"] = done[aid].get("note", "")
        else:
            item["status"] = "open"
            item.pop("done_at", None)
            item.pop("done_note", None)

    items = sorted(out.values(), key=lambda x: (x.get("status") == "done", -num(x.get("score"))))
    open_items = [i for i in items if i.get("status") != "done"]

    payload = {
        "generated_at": datetime.now().isoformat(),
        "open_count": len(open_items),
        "done_count": len(items) - len(open_items),
        "items": items,
    }
    with open(BACKLOG, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Enhancement backlog: {len(open_items)} open, {payload['done_count']} done, {len(items)} total")
    by_site = {}
    for i in open_items:
        by_site[i["site"]] = by_site.get(i["site"], 0) + 1
    for s, n in sorted(by_site.items(), key=lambda kv: -kv[1]):
        print(f"  {s}: {n} open")


if __name__ == "__main__":
    raise SystemExit(main())
