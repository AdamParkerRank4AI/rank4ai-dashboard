---
status: draft
site: fundbiz
type: new_page
target_query: 365 business finance
target_url: /lenders/365-business-finance/
current_state: |
  No dedicated page for 365 Business Finance exists on FundBiz. The lender appears in multiple listicles (MCA/speed/no-PG/adverse-credit), decline-reasons.ts, and vs-pairs.ts. Query "365 business finance" gets 103 impressions at pos 19.6 (0% CTR) -- Google is associating FundBiz with this query but no single page owns it.
proposed_change: |
  Create /lenders/365-business-finance/ as a bank-profile page in the existing banks.ts + [slug].astro pattern.

  Data entry for banks.ts:
  ```
  {
    slug: '365-business-finance',
    bankName: '365 Business Finance merchant cash advance',
    ownerEntity: '365 Business Finance Ltd (Companies House 06999371)',
    productOffered: 'Merchant cash advance (MCA) and revenue-based finance for UK Ltd companies and LLPs with card-terminal turnover.',
    typicalCriteria: 'Minimum 6 months trading, minimum £5,000/month card turnover, UK Ltd company or LLP. No minimum credit score stated. Personal guarantee not always required.',
    ticketRange: '£10,000 to £400,000',
    decisionPattern: '24 to 48 hours from application to funded. Direct lender, no broker. Decision based primarily on card-terminal statement analysis.',
    whyDeclines: [
      'Insufficient card-terminal turnover (below £5k/month).',
      'Business less than 6 months old.',
      'Sole trader or partnership (Ltd/LLP only).',
      'County Court Judgments above internal threshold.',
      'Business in excluded sector (gambling, adult, firearms).',
    ],
    whatToDoIfDeclined: 'A 365 decline on turnover or trading age usually means the MCA product does not fit rather than a credit issue. Match to a term-loan or asset-finance alternative on FundBiz -- or wait until card-terminal turnover clears £5k/month and reapply.',
    alternatives: ['Capify for MCA with more flexible CCJ underwriting', 'Liberis for revenue-based finance via card-terminal integration', 'iwoca for unsecured term loan up to £500k without card-turnover requirement'],
    lastReviewed: '2026-07-03',
  }
  ```

  Schema: BreadcrumbList + WebPage + FinancialProduct + FAQPage (3 Qs: what is a merchant cash advance, does 365 Business Finance check credit, how fast is approval).
why: |
  103 impressions at pos 19.6 with 0% CTR means Google already associates FundBiz with the "365 business finance" intent but there is no page to rank. A dedicated bank-profile page using the existing banks.ts + [slug].astro pattern requires only a data entry (15-minute work) and builds a reusable pattern. Given 365 is one of FundBiz's top MCA lenders referenced across 8 listicles and decline-reason slugs, this page is topically natural and provides a consolidation point for all those internal cross-links. Targeting: title "365 Business Finance: Merchant Cash Advance Rates & Review" + first answer-capsule of 60w defining what 365 offers.
---
