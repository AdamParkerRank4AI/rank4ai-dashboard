---
status: draft
site: fundbiz
type: title_rewrite
target_query: 365 business finance
target_url: /lenders/365-business-finance/
current_state: |
  Title (auto-generated): "365 Business Finance on FundBiz: Routing and Eligibility"
  Meta (auto-generated from lender.summary, truncated to 155 chars)
  Position: 19.6, impressions: 103, clicks: 0, CTR: 0%
proposed_change: |
  Title: "365 Business Finance: UK Merchant Cash Advance Review 2026"
  Meta (154 chars): "365 Business Finance provides merchant cash advances to UK SMEs. Compare eligibility, rates, and alternatives. No fixed repayments — repay as you earn."

  Implementation: the title and meta are generated from src/pages/lenders/[slug].astro
  line 13-14. To make lender-specific overrides, add an optional `overrideTitle` and
  `overrideMeta` field to the lender object in src/data/lenders.ts (similar pattern to
  how terminals.ts works in cardmachines). Then in [slug].astro:
    const title = lender.overrideTitle ?? `${lender.name} on FundBiz: Routing and Eligibility`;
    const description = lender.overrideMeta ?? `${lender.summary.slice(0, 155)}`;
  
  For 365 Business Finance specifically, set in lenders.ts:
    overrideTitle: '365 Business Finance: UK Merchant Cash Advance Review 2026',
    overrideMeta: '365 Business Finance provides merchant cash advances to UK SMEs. Compare eligibility, rates, and alternatives. No fixed repayments — repay as you earn.',
why: |
  "365 business finance" gets 103 impressions at position 19.6 — bottom of page 2.
  The current auto-generated title ("on FundBiz: Routing and Eligibility") reads like
  an internal directory entry, not a compelling result for someone searching the brand.
  Searchers want to know what 365 Business Finance actually does and how it compares.
  A cleaner title that calls out "Merchant Cash Advance Review 2026" + the no-fixed-
  repayments differentiator in the meta aligns with the commercial intent behind the
  query and should lift CTR from 0%. Adding the `overrideTitle` / `overrideMeta`
  fields to lenders.ts also gives a reusable pattern for other lender pages stuck
  on page 2 (e.g. Aldermore, iwoca alternatives).
---
