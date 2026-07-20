---
status: draft
site: market-invoice
type: meta_rewrite
target_query: peak cashflow
target_url: /providers/peak-cashflow/
current_state: |
  Title: "Peak Cashflow Review 2026 - Rates, Fees & Features"
  Description: "Peak Cashflow invoice finance for UK small businesses. Independent provider, Birmingham, facilities to £1m. Transparent pricing, fast decisions. Full 2026 review."
  Char count: 162 (2 over the 160 limit - may truncate in SERPs)
  Position: 7.7 | Impressions: 277 | Clicks: 1 | CTR: 0.36%
proposed_change: |
  Title (no change - well targeted at 52 chars):
  "Peak Cashflow Review 2026 - Rates, Fees & Features"

  New description (max 155 chars):
  "Independent Peak Cashflow review 2026. Invoice finance up to £1m for UK SMBs. Birmingham-based, transparent pricing, fast decisions. Compare rates."

  Char count: 148 chars. ✓
why: >
  At position 7.7, this page IS on page 1 but earns just 0.36% CTR (1 click from 277 impressions) - a strong signal that the SERP snippet isn't compelling clicks. The current description is 162 chars, 2 over the hard limit, meaning Google likely truncates it mid-sentence after "Full 2026". The truncated version reads as an incomplete sentence. The proposed description: (1) trims to 148 chars so it always renders in full; (2) moves "Independent" to the front, signalling editorial authority; (3) ends with "Compare rates" - a clear action the searcher will take, improving CTR probability. No code change needed: just update the `description` const on line 11 of /providers/peak-cashflow.astro.
---
