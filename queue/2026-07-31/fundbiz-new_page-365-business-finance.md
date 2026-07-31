---
status: draft
site: fundbiz
type: new_page
target_query: 365 business finance
target_url: /banks/365-business-finance/
current_state: |
  No dedicated page for "365 Business Finance" exists on fundbiz.co.uk.
  Query earns 150 impressions at pos 19.1 — page 2. FundBiz mentions "365 Business Finance" as a lender partner in sectors.ts but has no dedicated review page.
  Identical query also ranking on bestbusinessloans.ai at pos 49 and market-invoice.co.uk (lower).
proposed_change: |
  Add a new entry to /home/user/fundbiz/src/data/banks.ts:

  {
    slug: '365-business-finance',
    bankName: '365 Business Finance',
    ownerEntity: '365 Business Finance Ltd (registered UK, Companies House)',
    productOffered: 'Merchant Cash Advance (MCA) and Merchant Revenue Advance for UK businesses with card-payment turnover. Advances from £5k to £400k based on monthly card receipts.',
    typicalCriteria: 'Minimum 6 months trading. Active card payment history with a UK acquirer. Ltd company, LLP or sole trader (sole traders accepted unlike most lenders on this site — note FCA perimeter applies for Ltd/LLP matchmaking only). Minimum monthly card revenue typically £5k+.',
    ticketRange: '£5k to £400k.',
    decisionPattern: 'Soft-pull credit check. Decision in 24-48h. Funds in 5-7 working days. Repayment via a fixed percentage of daily card receipts (no fixed monthly payment).',
    whyDeclines: ['Insufficient card turnover history (under 6 months).', 'Card receipts below minimum threshold.', 'Prior MCA defaults with other providers.', 'Sole-trader-only structure for FundBiz matchmaking (we route to 365 directly for sole traders).'],
    whatToDoIfDeclined: '365 BF declines are typically volume-based. If declined, check Capify or iwoca as MCA alternatives with similar speed but different volume thresholds.',
    alternatives: ['Capify', 'iwoca (flex credit line)', 'YouLend', 'Liberis'],
    lastReviewed: '2026-07-31',
  }

  This will auto-generate /banks/365-business-finance/ via the dynamic [slug].astro route.
why: |
  "365 business finance" earns 150 impressions at pos 19.1 with 0 clicks — it is one of the clearest content gaps across the fleet. FundBiz already mentions 365 Business Finance in its hospitality sector page as a recommended lender, which is why Google already associates the query with the site. A dedicated bank-review page would give the query a proper landing page, signal topical authority on MCA (a core FundBiz product category), and likely move the query to page 1 within 4-6 weeks of indexing. 365 Business Finance is a real, established UK lender operating since 2011.
---
