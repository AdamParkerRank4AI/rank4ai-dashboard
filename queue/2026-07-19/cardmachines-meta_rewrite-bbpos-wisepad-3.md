---
status: draft
site: cardmachines
type: meta_rewrite
target_query: bbpos wisepad 3
target_url: /reviews/bbpos-wisepad-3/
current_state: "BBPOS WisePad 3: UK rates, fees and verdict 2026 | meta is truncated (reviewMeta override added 2026-07-11)"
proposed_change: "Title rewrite to put 'card reader' and 'Stripe' earlier in title for better CTR at position 13"
why: |
  "bbpos wisepad 3" gets 189 impressions at position 13 with 0.53% CTR. The
  reviewMeta override was added in Fleet auto-review 2026-07-11 to fix the
  truncated meta description. The next lever is the title. The current title
  "BBPOS WisePad 3: UK rates, fees and verdict 2026" (50 chars) is fine but
  does not include "Stripe" or "card reader" which are the context signals
  searchers associate with BBPOS. Adding one of these could lift CTR from
  position 13.
---

## Title rewrite

File: `src/data/terminals.ts` — the `pax-a77` slug entry's `reviewMeta`
and `name` fields. For title, the template in `src/pages/reviews/[slug].astro`
generates: `${terminal.name}: UK rates, fees and verdict ${reviewYear}`

Since the template is fixed, the only lever without touching the template is
adding a `reviewTitle` field to the terminal data (similar to `reviewMeta`).

**Option A — add reviewTitle field:**
In `terminals.ts` for the `bbpos-wisepad-3` entry:
```ts
reviewTitle: 'BBPOS WisePad 3 (Stripe Terminal): UK rates, fees and verdict 2026',
```
Then in `[slug].astro` line 69:
```ts
const title = terminal.reviewTitle ?? reviewTitleCandidates.find(...) ?? ...;
```

**Option B — rename terminal in name field:**
Change `name: 'BBPOS WisePad 3'` to `name: 'BBPOS WisePad 3 card reader'`
— but this propagates everywhere, including the H1.

**Recommend Option A** — it is surgical and non-breaking.

**Proposed title:** "BBPOS WisePad 3 (Stripe Terminal): UK rates, fees and verdict 2026" (65 chars)

## Note on current state
The meta description was already fixed with the `reviewMeta` override in
commit `a5e262f` (2026-07-11). The title is the remaining opportunity.
The 2026-07-09 crawl (before the reviewMeta fix) showed pos 13 / 189 impressions.
