---
status: draft
site: cardmachines
type: title_rewrite
target_query: bbpos wisepad 3
target_url: https://merchanthq.co.uk/reviews/bbpos-wisepad-3/
current_state: |
  Title (auto-generated): "BBPOS WisePad 3: UK rates, fees and verdict 2026"
  Description (auto-generated): "Hands-on BBPOS WisePad 3 review by MerchantHQ. [first sentence of terminal.summary]"
  Position: 17.2  |  Impressions: 127  |  CTR: 0%  |  Clicks: 0
proposed_change: |
  Title: "BBPOS WisePad 3 Review 2026 | Stripe Terminal UK Rates & Verdict"
  Description: "Hands-on BBPOS WisePad 3 review: Stripe Terminal's Bluetooth card reader for UK merchants. Rates, setup, who it suits and honest verdict. Updated 2026."
why: |
  "bbpos wisepad 3" has 127 impressions at position 17.2 (mid-page-2) and 0 clicks. The existing GSC top_pages data shows the same page at pos 11.4 over a longer window, suggesting the ranking fluctuates — the page is borderline page 1.

  The current auto-generated title ("BBPOS WisePad 3: UK rates, fees and verdict 2026") uses a colon separator and is informative but doesn't signal "review" intent. Searchers looking up "bbpos wisepad 3" are almost always on a pre-purchase research journey — "Review" is the highest-intent word for that journey and significantly lifts CTR.

  Adding "Stripe Terminal" positions the reader immediately — the WisePad 3 is the classic Stripe Terminal Bluetooth reader, and many searchers arrive from Stripe's own ecosystem. This adds brand signal they'll recognise and trust.

  The description rewrite explicitly names Stripe Terminal (not just "BBPOS") to capture merchant cohort searching from the Stripe ecosystem.

  Implementation: the title is auto-generated from `reviewTitleCandidates` in `src/pages/reviews/[slug].astro`. The quickest override is to add a `reviewTitle` field to the `bbpos-wisepad-3` entry in `src/data/terminals.ts` and update the template to check for it before falling back to the generated candidates. Alternatively, the template title candidates can be reordered to include "Review" as the first option (global change affecting all review pages).
---
