# fundbiz — Title/Meta Rewrite: /lenders/365-business-finance

**Date queued:** 2026-07-04
**Type:** title-meta
**Priority:** high (pos 19.6, 103 impr, 0% CTR — near-page-1 with zero clicks)
**URL:** https://www.fundbiz.co.uk/lenders/365-business-finance/
**Source file:** fundbiz/src/pages/lenders/[slug].astro

## Why

"365 business finance" drives 103 impressions at position 19.6 with zero clicks. The current lender template generates a generic "365 Business Finance on FundBiz: Routing and Eligibility" title. That reads like internal jargon — no searcher knows what "routing" means in this context.

## Current (template-generated)

```javascript
const title = `${lender.name} on FundBiz: Routing and Eligibility`;
```

Produces: **"365 Business Finance on FundBiz: Routing and Eligibility"** (54 chars)

```javascript
const description = `${lender.summary.slice(0, 155)}`;
```

Produces a 155-char slice from internal routing notes — reads as broker jargon, not user-facing.

## Recommended changes

**Option A: Per-lender override (preferred — add to lenders.ts)**

```typescript
// in lenders.ts, 365 Business Finance entry:
titleOverride: '365 Business Finance: Merchant Cash Advance UK | FundBiz',
descriptionOverride: 'Independent overview of 365 Business Finance, the UK merchant cash advance specialist for Ltd companies and LLPs. Advances from £10k. Same-day decisions.',
```

Then in lenders/[slug].astro:
```javascript
const title = lender.titleOverride ?? `${lender.name} on FundBiz: Routing and Eligibility`;
const description = lender.descriptionOverride ?? lender.summary.slice(0, 155);
```

**Option B: Template improvement (applies to all lenders)**

```javascript
const title = `${lender.name}: ${lender.productType.split(',')[0].trim()} | FundBiz`;
```

Produces: "365 Business Finance: Merchant Cash Advance | FundBiz" (53 chars) — more descriptive without per-lender data.

## Also

- "aldermore commercial mortgages" at pos 19.4 / 38 impr / 0% CTR has same template issue. See sister draft: fundbiz-title-aldermore-commercial-mortgages.md
- Apply Option A to both 365 Business Finance and Aldermore. One commit, two entries.

## Effort

Option A: edit lenders.ts (2 new optional fields per entry) + edit [slug].astro (3 lines). Low risk.
Option B: edit [slug].astro template string only (1 line). Ship immediately.
