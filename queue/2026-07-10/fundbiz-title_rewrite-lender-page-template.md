---
status: draft
site: fundbiz
type: title_rewrite
target_query: 365 business finance (and all lender head terms)
target_url: /lenders/[slug]/ (template fix — affects all ~50 lender pages)
current_state: |
  template title: "${lender.name} on FundBiz: Routing and Eligibility"
  example: "365 Business Finance on FundBiz: Routing and Eligibility"
  example: "Aldermore on FundBiz: Routing and Eligibility"
  position 365: 19.1 | impressions: 150 | clicks: 0
  position aldermore (commercial mortgages): 18.2 | impressions: 75 | clicks: 0
proposed_change: |
  template title: "${lender.name}: UK ${lender.productType} Review 2026 | FundBiz"
  example: "365 Business Finance: UK Merchant Cash Advance Review 2026 | FundBiz"
  example: "Aldermore: UK Asset Finance & Commercial Mortgage Review 2026 | FundBiz"
  
  Change in src/pages/lenders/[slug].astro line 13:
  FROM: const title = `${lender.name} on FundBiz: Routing and Eligibility`;
  TO:   const title = `${lender.name}: UK ${lender.productType} Review 2026 | FundBiz`;
  
  (Note: some lender.productType values include commas — check max title length across
  all lenders before applying.)
why: |
  "365 business finance" gets 150 impressions/month at position 19.1 (page 2) and 0
  clicks. "Aldermore commercial mortgages" gets 75 impressions at position 18.2.
  The root cause is the title format: "X on FundBiz: Routing and Eligibility" signals
  an internal admin or broker tool, not a consumer review or comparison. Searchers
  looking up "365 business finance" want product info and rates, not platform routing.
  A single template change to include the product type and "Review 2026" will make
  all ~50 lender pages match user intent across their branded head terms.
  This is the fastest page-2 lift available on FundBiz: one template line, ~50 pages
  re-optimised simultaneously.
---
