---
status: draft
site: market-invoice
type: content_refresh
target_query: market invoice
target_url: https://marketinvoice.co.uk/
current_state: |
  "market invoice" brand query: pos best 8.9 → now 15.8 (+1.48/wk slide), 15→13 clicks.
  "marketinvoice" brand query: pos best 6.1 → now 14.2 (+1.25/wk slide), 13→11 clicks.
  Both queries losing ~1.4 positions per week — consistently across 27 snapshots (2026-05-24→2026-07-07).
proposed_change: |
  The decay is brand-query position loss — likely a brand disambiguation issue (Kriya/MarketFinance
  still dominate brand search by authority). Two levers:
  
  1. HOMEPAGE HERO: Add a first-paragraph "Not Kriya or MarketFinance?" disambiguation sentence.
     Entity-function pattern: "Market Invoice (marketinvoice.co.uk) is the UK's independent
     invoice finance comparison and broker — not a lender, not Kriya, not MarketFinance."
     This reinforces the entity signal that's sliding.
  
  2. BRAND PAGE: Build /about/market-invoice-not-kriya/ or update /about/ to explicitly clarify
     what marketinvoice.co.uk is and isn't. Cross-link from homepage and /providers/.
  
  Both changes need the Oliver Mackman author byline, no FAQPage, no em dashes.
why: |
  GSC content-decay-monitor.mjs data (2026-07-07) shows these are the 2 highest-scoring
  decay signals for market-invoice (scores 1.177 and 0.943 vs site median 0). Brand queries
  at pos 14-16 are leaking clicks to competitors. The disambiguation page pattern already
  worked on MI's /about/ page (commit c138767, Apr 2026) — refresh or extend that pattern.
  Priority: this is the #1 conversion-bottleneck site (7/12 MI leads via Bing); brand
  clarity directly protects lead volume.
---
