---
status: draft
site: cardmachines
type: title_rewrite
target_query: bbpos wisepad 3
target_url: https://merchanthq.co.uk/reviews/bbpos-wisepad-3/
current_state: |
  Title: "BBPOS WisePad 3: UK rates, fees and verdict 2026"
  H1:    "BBPOS WisePad 3 review"
  GSC:   pos 17.2, 127 imp, 0% CTR (0 clicks). Also: several /vs/bbpos-wisepad-3-vs-*/ pages competing; /alternatives/bbpos-wisepad-3/ exists.
proposed_change: |
  Title: "BBPOS WisePad 3 Review 2026: Price, Transaction Fees & Verdict UK"
  Meta (new):  "BBPOS WisePad 3 is Stripe's mobile card reader, white-labelled by Stripe Terminal partners. This review covers UK pricing, transaction fees, setup and which businesses it suits."

  Changes:
  - Moves "Review" to immediately after the product name — aligns with how searchers write this query ("bbpos wisepad 3 review").
  - Replaces "UK rates, fees and verdict" with "Price, Transaction Fees & Verdict UK" — "Price" precedes "Fees" (searcher priority), "UK" moves to end (natural language), ampersand adds scannability.
  - Adds year directly after "Review" (freshness signal for comparison shoppers).
  - Meta: adds context that it's "Stripe's mobile card reader" and "Stripe Terminal partner" — the search intent is often from Stripe customers trying to understand the hardware.
why: |
  127 impressions at pos 17.2 with 0 clicks across a 28-day window is a clear title-CTR failure. The current title structure "BBPOS WisePad 3: UK rates, fees and verdict 2026" places the year at the end, buries the review signal after a colon, and doesn't match the natural phrasing searchers use ("bbpos wisepad 3 review"). The /vs/ comparison pages for this terminal are capturing some competing traffic but without a strong review hub the site loses the higher-intent purchase-decision clicks. With the PAX A77 orphan cluster now fixed (commit e8b9e86 on 1 Jul), the review page itself is the next bottleneck.
---
