# Fleet Daily Review: 2026-07-11

## Mechanical fixes shipped to main

### FundBiz (fundbiz.co.uk)
- **Lender page title template** (`src/pages/lenders/[slug].astro`): Changed from "X on FundBiz: Routing and Eligibility" to "X: UK Business Finance Rates & Eligibility (2026)" — affects all 112 lender pages. Targets "365 business finance" (150 imp, pos 19.1) and similar lender-name queries.
- **Alternatives page title template** (`src/pages/alternatives/[slug].astro`): Changed from "Alternatives to X: UK specialty finance" to "Best Alternatives to X (2026): UK Business Finance Compared". Targets "iwoca alternatives" (72 imp, pos 13.2, CTR 1.39%) and similar.
- Commits pushed to `AdamParkerRank4AI/fundbiz` main.

### Market Invoice (marketinvoice.co.uk)
- **accident-credit-group.astro**: Title improved to "Accident Credit Group: Invoice Finance for Credit Hire UK (2026)"; description updated to lead with product category. Page is at pos 13.7, 100 imp, CTR 0%.
- **peak-cashflow.astro**: Meta description updated to be more benefit-led and mention "fast decisions". Page is at pos 7.7, 277 imp, CTR 0.36%.
- Commits pushed to `AdamParkerRank4AI/market-invoice` main.
- Note: Also includes 2026-07-10 em-dash fix that was committed but not pushed.

### MerchantHQ / CardMachines (merchanthq.co.uk)
- Added `reviewMeta?: string` optional field to Terminal interface in `terminals.ts`.
- Added `reviewMeta` override for **bbpos-wisepad-3** (189 imp, pos 13.4, CTR 0.53%): "BBPOS WisePad 3 is the Stripe Bluetooth card reader for UK merchants (£59). MerchantHQ review: UK compatibility, connection, battery, acquirer setup and alternatives."
- Added `reviewMeta` override for **bbpos-wisepos-e** (116 imp, pos 7.4, CTR 0%): "BBPOS WisePOS E is the Stripe smart terminal for UK merchants (£249). MerchantHQ review: UK compatibility, acquiring fees, setup and the 4 closest alternatives."
- Updated `src/pages/reviews/[slug].astro` to use `terminal.reviewMeta` when present, falling back to generated description.
- Commit pushed to `AdamParkerRank4AI/cardmachines` (auto-redirects to `AdamParkerRank4AI/merchanthq`) main.

## Fleet baseline findings

- **seocompare**: `clarity_firing: false` — Clarity Project ID is empty string in `src/layouts/BaseLayout.astro` line 42. **Adam action required**: add real Clarity Project ID.
- **market-invoice** and **cardmachines**: `no_faqpage: false` — FALSE ALARM. Both sites have per-site CLAUDE.md entries re-enabling FAQPage since June 2026. Baseline checker is outdated. No action needed.

## Human action required

1. **SEOCompare Clarity ID**: `CLARITY_ID: string = ''` in `src/layouts/BaseLayout.astro`. Add real Clarity Project ID to fix the fleet baseline failure. Adam to get ID from Microsoft Clarity dashboard.
2. **FundBiz GSC Indexing API**: `indexing@inbound-dahlia-491120-v6.iam.gserviceaccount.com` must be added as GSC Owner before Indexing API submissions work. FundBiz has 0 Indexing API submissions vs BBL's 100. Adam action.
3. **Wikidata/Wikipedia stubs**: All 8 sites lack Wikidata entity pages. Recommendations JSON lists this as critical for rank4ai and fundbiz. Adam action (or delegate as a content task).
4. **SEOCompare YouTube sameAs**: `site.manifest.ts` references a YouTube channel `@seocompare` that may not exist. Either create the channel or remove the sameAs reference.

## Content drafts in today's queue

- `rank4ai-new_page-what-is-ai-seo.md` — new page stub, "what is ai seo" (261 imp, pos 34)
- `market-invoice-new_page-invoice-discounting-vs-factoring.md` — new page stub, "invoice discounting vs factoring" (125 imp, pos 56)
- `seocompare-new_page-chatgpt-seo-agency.md` — new page stub, "chatgpt seo agency" (22 imp, pos 41)

## Carryover from 2026-07-10 queue (still pending)

- `market-invoice-title_rewrite-barclays-invoice-finance.md` — barclays invoice finance page, pos ~12 (Adam to review)
- `rank4ai-title_rewrite-ai-search-agency.md` — /ai-search-agency/ title test (864 imp, pos 13.2)
- `rank4ai-cannibalization-ai-search-agency.md` — cannibalization concern, multiple R4 pages competing for "ai search agency"
