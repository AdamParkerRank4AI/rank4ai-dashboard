# fundbiz — Title/Meta Rewrite: /lenders/aldermore

**Date queued:** 2026-07-04
**Type:** title-meta
**Priority:** medium (pos 19.4, 38 impr, 0% CTR — zero-click near page 1)
**URL:** https://www.fundbiz.co.uk/lenders/aldermore/
**Source file:** fundbiz/src/pages/lenders/[slug].astro

## Why

"aldermore commercial mortgages" is at position 19.4 with 38 impressions and zero clicks. Aldermore's FundBiz page ranks for this query but the generic template title ("Aldermore on FundBiz: Routing and Eligibility") gives searchers no reason to click over Aldermore's own site.

## Current (template-generated)

Produces: **"Aldermore on FundBiz: Routing and Eligibility"** (47 chars)

## Recommended changes

Using the titleOverride approach from the 365BF draft:

```typescript
// in lenders.ts, Aldermore entry:
titleOverride: 'Aldermore Commercial Mortgages: Independent UK Review | FundBiz',
descriptionOverride: 'Independent overview of Aldermore for commercial mortgages, asset finance and invoice finance. £25k to £5m. For Ltd companies and LLPs. Broker-introduced. Updated 2026.',
```

Produced title: 64 chars — exactly matches the "aldermore commercial mortgages" query + independent review hook.

## Effort

Implement together with the 365 Business Finance fix — both require the same `titleOverride` field addition to `lenders.ts` and the template change in `[slug].astro`. One commit, two entries.
