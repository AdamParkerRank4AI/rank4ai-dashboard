---
status: draft
site: fundbiz
type: title_rewrite
target_query: 365 business finance
target_url: https://fundbiz.co.uk/lenders/365-business-finance/
current_state: |
  Title: "365 Business Finance: UK Business Finance Rates & Eligibility (2026)"
  Description: "Panel direct MCA lender we route to for £25k+ card-flow advances where the applicant wants a no-broker-fee structure. We also send case-by-case post-decline files here when missed payments or recent CCJs sit in the file but the card flow remains strong. Best fit for hos" [auto-generated, 155 char slice of lender.summary]
proposed_change: |
  Title: "365 Business Finance: Merchant Cash Advance Rates & Review 2026"
  Description: "365 Business Finance offers merchant cash advances from £10k to £500k for UK limited companies. Factor rates 1.10 to 1.40. No broker fee. Compare and apply via FundBiz."
why: >
  "365 business finance" gets 150 impressions at pos 19.1 with 0% CTR (0 clicks). This is a
  brand query for an MCA lender and the searcher intent is clear: they want to know what 365
  Business Finance does and whether to use them. The current title says "UK Business Finance
  Rates" which is generic; "Merchant Cash Advance" is the specific product and should match
  the query intent better. The auto-generated description from lender.summary reads like an
  internal routing note ("Panel direct MCA lender we route to") — not appropriate for a SERP
  snippet. The proposed description is public-facing: £ amounts, factor rates, the "no broker
  fee" USP (a strong differentiator), and a clear CTA. The description field in lenders.ts
  does not accept a custom field yet — this change requires either adding a `reviewMeta` field
  to the lender type (mirrors the `terminal.reviewMeta` pattern in cardmachines) or overriding
  the auto-slice in [slug].astro. Adam to decide approach.
---
