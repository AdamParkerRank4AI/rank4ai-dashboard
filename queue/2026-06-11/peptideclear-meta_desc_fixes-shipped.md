---
status: shipped
site: peptideclear
type: meta_desc_fix
commit: 10f352f82d40183cb54bdfcb8b038dab3a1b09c4
date: 2026-06-11
---

## What shipped

9 meta description fields trimmed to under 160 characters (were 162-212 chars, triggering
daily audit warnings). All changes are frontmatter-only in blog .md files. No copy changes.

| File | Old length | New length |
|---|---|---|
| best-nad-supplement-uk.md | 205 | 159 |
| best-nmn-supplement-uk.md | 219 | 139 |
| iv-drip-uk.md | 180 | 146 |
| iv-drip-vs-supplement.md | 212 | 139 |
| longevity-supplements-uk.md | 196 | 151 |
| nad-cost-uk.md | 192 | 153 |
| nad-iv-drip-uk.md | 207 | 159 |
| nad-side-effects-uk.md | 222 | 148 |
| nad-supplement-uk.md | 200 | 157 |

All descriptions are still over 120 chars (Google's observed truncation lower bound) and
clearly describe the page content. No em dashes. No medicinal claims.

## Result

CF Pages rebuild triggered on push to AdamParkerRank4AI/ukmetabolic main. Daily audit should
show 0 meta desc issues on peptideclear once crawl refreshes.
---
