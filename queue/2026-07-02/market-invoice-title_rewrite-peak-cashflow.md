---
status: draft
site: market-invoice
type: title_rewrite
target_query: peak cashflow
target_url: https://marketinvoice.co.uk/providers/peak-cashflow/
current_state: |
  Title: "Peak Cashflow Review 2026 - Rates, Fees & Features"
  Description: "Peak Cashflow is an independent invoice finance provider established in 2007 in Birmingham. Small business focused with facilities up to £1m. Transparent."
  Position: 8.7  |  Impressions: 243  |  CTR: 0.41%  |  Clicks: 1
proposed_change: |
  Title: "Peak Cashflow Review 2026 | Invoice Finance Rates, Eligibility & Verdict"
  Description: "Peak Cashflow review: independent Birmingham invoice finance provider, facilities up to £1m. Who qualifies, what it costs, and honest verdict. Updated 2026."
why: |
  "peak cashflow" ranks at position 8.7, sitting just inside page 1. With 243 impressions, this is a real traffic opportunity, but 0.41% CTR at position 8-9 is roughly 10x below what a well-optimised title earns at that position (expected 4-6%).

  The current title uses " - " as a separator (fleet rule: replace em/en dashes with "|" in user-facing copy). More importantly, "Rates, Fees & Features" is generic and flat — it could describe any financial product listing. Searchers for "peak cashflow" want to know: can I get funding from them? What does it cost? Should I use them?

  Adding "Eligibility" targets the high-intent pre-click concern (am I eligible?) and "Verdict" signals editorial judgement rather than a dry data table. Both are proven CTR lifters on review pages.

  The description rewrite adds "who qualifies" and "honest verdict" which match what "peak cashflow" searchers are looking for.

  Implementation: update `title` and `description` const variables in `src/pages/providers/peak-cashflow.astro`. Replace " - " separator with " | " (also removes the hyphen dash that violates fleet rule).
---
