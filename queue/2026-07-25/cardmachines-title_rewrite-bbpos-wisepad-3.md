---
status: draft
site: cardmachines
type: title_rewrite
target_query: bbpos wisepad 3
target_url: https://merchanthq.co.uk/reviews/bbpos-wisepad-3/
current_state: |
  Title: "BBPOS Wisepad 3: UK rates, fees and verdict 2026" (auto-generated from terminal template)
  Description: auto-generated from terminal.summary (no reviewMeta set)
proposed_change: |
  Title: "BBPOS Wisepad 3 Review: UK Rates, Fees and Verdict 2026"
  Description: "BBPOS Wisepad 3 is a Bluetooth card reader distributed via Stripe in the UK. Compare rates, contract terms and hardware specs vs SumUp, Square and Zettle. MerchantHQ 2026."
why: >
  "bbpos wisepad 3" gets 189 impressions at pos 13.4 with 0.53% CTR (1 click). This is the
  biggest striking-distance query for the cardmachines site. The current title is 49 chars and
  technically fine, but adding "Review" makes the informational intent match explicit (SERP
  shows review-labelled results get higher CTR on product queries). The description is
  auto-sliced from terminal.summary which is internal routing language, not user-facing SERP
  copy. The proposed description names Stripe (the acquirer), names three direct competitors
  the user likely compares against (SumUp, Square, Zettle), and ends with a site authority
  signal. To implement: add `reviewMeta` field to the BBPOS Wisepad 3 entry in terminals.ts
  with the proposed description text. The review template already supports this field
  (see reviews/[slug].astro line 70: `terminal.reviewMeta ?? ...`).
---
