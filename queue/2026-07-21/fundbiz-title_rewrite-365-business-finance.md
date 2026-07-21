---
status: draft
site: fundbiz
type: title_rewrite
target_query: 365 business finance
target_url: /lenders/365-business-finance/
current_state: |
  Title: "365 Business Finance: UK Business Finance Rates & Eligibility (2026)"
  Description: "Panel direct MCA lender we route to for £25k+ card-flow advances where the applicant wants a no-broker-fee structure. We also sen..." [TRUNCATED at 155 chars from internal summary field]
  Position: 19.1 | Impressions: 150 | CTR: 0% | Clicks: 0
proposed_change: |
  Title: "365 Business Finance Review 2026: Merchant Cash Advance Rates & Eligibility"
  Description: "365 Business Finance provides merchant cash advance from £10k to £500k. Factor rate 1.10 to 1.40, 24 to 48 hour decisions. Compare on FundBiz."
  Code fix needed: Add a `reviewMeta` field to the 365-business-finance entry in
  src/data/lenders.ts, similar to how cardmachines terminals use `reviewMeta` to override
  the internal summary field. The lender `summary` field currently contains internal panel
  routing notes not intended for user-facing display.
why: |
  URGENT: The meta description for /lenders/365-business-finance/ is currently being
  populated from lender.summary which contains INTERNAL ROUTING NOTES: "Panel direct MCA
  lender we route to for £25k+ card-flow advances where the applicant wants a no-broker-fee
  structure. We also send case-by-case post-decline files here..." This reads as an internal
  ops note, not a public description.

  This likely affects other FundBiz lender pages with similar internal-language summaries.
  Recommend auditing all lenders.ts entries for internal-facing language before Google
  crawls and indexes these descriptions.

  The 0% CTR at position 19.1 is consistent with a meta description that confuses users
  ("Panel direct MCA lender we route to...") — users searching "365 business finance" would
  not recognise this as relevant to their query.

  Two actions needed:
  1. Fix the description immediately by adding a `reviewMeta` field to lenders.ts entries
     (or add a separate `metaDescription` field to the lender data type).
  2. Audit all lender summaries in lenders.ts for internal language that should not appear
     in user-facing meta descriptions.
---
