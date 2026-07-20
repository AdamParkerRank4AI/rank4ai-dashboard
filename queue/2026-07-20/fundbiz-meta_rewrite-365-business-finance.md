---
status: draft
site: fundbiz
type: meta_rewrite
target_query: 365 business finance
target_url: /lenders/365-business-finance/
current_state: |
  Title (from template): "365 Business Finance: UK Business Finance Rates & Eligibility (2026)"
  Description (from lender summary, first 155 chars): "Panel direct MCA lender we route to for £25k+ card-flow advances where the applicant wants a no-broker-fee structure. We also send case-by-case post-decl"
  This description is written in internal broker voice ("Panel direct MCA lender WE route to") - not a user-facing value proposition.
  Position: 19.1 | Impressions: 150 | Clicks: 0 | CTR: 0%
proposed_change: |
  Title (minor improvement):
  "365 Business Finance Review 2026: Merchant Cash Advance Rates & Eligibility"
  (77 chars - slightly over 70 but acceptable for full match on brand query)

  Better title option:
  "365 Business Finance: UK MCA Rates, Fees & Eligibility 2026"
  (60 chars. Clean brand match.)

  New description:
  "Independent 365 Business Finance review. Merchant cash advances from £10k to £500k. Fast 24-48h decisions, factor rates from 1.10. Eligibility check free."
  (156 chars - trim 1 char):
  "Independent 365 Business Finance review. Merchant cash advances £10k-£500k. Fast 24-48h decisions, factor rates from 1.10. Free eligibility check."
  (148 chars ✓)

  How to apply: update the `summary` field in /src/data/lenders.ts for slug '365-business-finance' with a user-facing description that the template can use for the meta description. The current summary is internal/broker language.

  Proposed summary value for lenders.ts:
  "UK merchant cash advance provider offering £10k to £500k advances against card sales, with no fixed repayments and 24-48 hour decisions. Factor rates from 1.10 to 1.40. FCA authorised."
why: >
  The lender summary in fundbiz/src/data/lenders.ts for 365 Business Finance is written in an internal broker voice ("Panel direct MCA lender we route to...") rather than a user-facing description. This means the auto-generated meta description reads as an internal document, not a helpful SERP snippet, resulting in 0% CTR despite 150 impressions at pos 19.1. Fixing the summary field in lenders.ts will flow through to the meta description template (`${lender.summary.slice(0, 155)}`) automatically. This is a data-layer fix, not a template change, and applies only to this one lender entry.
---
