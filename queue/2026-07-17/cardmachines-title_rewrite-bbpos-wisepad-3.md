---
status: draft
site: cardmachines
type: title_rewrite
target_query: bbpos widepad 3
target_url: /reviews/bbpos-wisepad-3/
current_state: >
  Title: auto-generated as "BBPOS Wisepad 3: UK rates, fees and verdict 2026"
  Meta: auto-generated from terminal.reviewMeta (null, falls back to summary excerpt)
  Current position: 13.4 (189 impressions, 1 click, 0.53% CTR)
  Note: the query spells it "widepad" (not "wisepad"). Google treats these as equivalent.
proposed_change: >
  Add a custom `reviewMeta` field to the bbpos-wisepad-3 entry in src/data/terminals.ts:

  reviewMeta: "BBPOS Wisepad 3 card reader review: UK rates, contract and settlement. Bluetooth reader used by Stripe Terminal merchants. Compare vs alternatives on MerchantHQ."

  This is a mechanical change to terminals.ts. The template already uses `terminal.reviewMeta`
  as the primary description source (see reviews/[slug].astro line 70).

  Optionally also add a `titleOverride` if the template supports custom titles, or request
  the template be updated to support `titleOverride` field for targeted terminal pages.
why: >
  The review page ranks at pos 13.4 for "bbpos widepad 3" (common misspelling of "wisepad")
  with 189 impressions and 0.53% CTR. The auto-generated meta is a truncated copy of the
  terminal summary which is not click-optimised. A custom reviewMeta that calls out:
  (a) the specific model name, (b) that it is for Stripe Terminal merchants, (c) that
  comparisons are available, would better capture the evaluation-mode intent behind this
  query. This is the second-highest impression query for cardmachines (after "bbpos wisepos
  e" at 116 impressions) and currently drives the fewest clicks per impression.

  Implementation: Edit src/data/terminals.ts, find the bbpos-wisepad-3 entry, add reviewMeta.
  Build locally to confirm no type errors. Ship to main.
---
