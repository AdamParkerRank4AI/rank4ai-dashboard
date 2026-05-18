#!/usr/bin/env python3
"""Title truncation detector.

Per the MI title-length linter regression (14 May 2026): a pre-commit hook
silently truncates `const title = "..."` strings >60 chars mid-word at commit,
leaving broken titles live. Bit twice in 2 days.

Scans every crawl_<site>.json `pages[]` array for titles that look truncated:
  - length 58-62 AND ends with a letter (no terminal punctuation)
  - does NOT end on common short connectors ('and', 'AI', 'UK', 'in', 'of')

Writes title_lint.json keyed by site → list of suspicious pages.
"""
import json
import os
import re
from datetime import datetime

LIVE = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
OUT = os.path.join(LIVE, "title_lint.json")

# Words that should NEVER end a title — strong signal of mid-cut.
# Articles, conjunctions, prepositions, indefinite pronouns when at end of a 58-62 char string.
TRUNCATION_TAIL = re.compile(
    r"\b(a|an|the|and|or|but|with|from|by|at|as|of|in|on|to|for|that|this|"
    r"these|those|do|did|does|is|are|was|were|has|have|had|will|would|can|"
    r"could|should|may|might|must|i|we|you|they|it|its|my|our|their)$",
    re.I,
)
# Single-letter tail (e.g. "What Do I" cut to "What Do I")
SINGLE_LETTER_TAIL = re.compile(r"\b[A-Za-z]$")

def is_suspicious(title: str) -> bool:
    if not title:
        return False
    L = len(title)
    if not (55 <= L <= 62):
        return False
    # Must end on an alphanumeric (no punctuation = no clean ending)
    if not title[-1].isalnum():
        return False
    # Strong: ends with stopword/preposition/aux verb
    if TRUNCATION_TAIL.search(title):
        return True
    # Weak: ends with single capitalised letter (excluding "I" already covered)
    # Skip — too many false positives from acronyms like "UK", "AI"
    return False

def main():
    out = {"generated_at": datetime.now().isoformat(), "sites": {}, "total_flagged": 0}
    total = 0
    for fname in sorted(os.listdir(LIVE)):
        if not fname.startswith("crawl_") or not fname.endswith(".json"):
            continue
        if fname == "crawl_activity.json":
            continue
        site_id = fname[len("crawl_"):-len(".json")]
        try:
            data = json.load(open(os.path.join(LIVE, fname)))
        except Exception:
            continue
        flagged = []
        for p in data.get("pages", []) or []:
            t = p.get("title", "")
            if is_suspicious(t):
                flagged.append({
                    "url": p.get("url", "") or p.get("path", ""),
                    "title": t,
                    "length": len(t),
                })
        out["sites"][site_id] = {
            "flagged_count": len(flagged),
            "flagged": flagged[:50],
        }
        total += len(flagged)
    out["total_flagged"] = total
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"title_lint: {total} suspicious titles across {len(out['sites'])} sites → {OUT}")
    for sid, d in out["sites"].items():
        if d["flagged_count"]:
            print(f"  {sid}: {d['flagged_count']}")

if __name__ == "__main__":
    main()
