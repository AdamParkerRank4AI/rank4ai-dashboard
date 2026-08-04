---
status: draft
site: fundbiz
type: title_rewrite
target_query: 365 business finance
target_url: /lenders/365-business-finance/
gsc_position: 19.1
gsc_impressions: 150
gsc_ctr: 0%
current_title: "365 Business Finance: UK Business Finance Rates & Eligibility (2026)"
current_description: "Panel direct MCA lender we route to for £25k+ card-flow advances where the applicant wants a no-broker-fee structure. We also send case-by-case post-de"
proposed_title: "365 Business Finance Review 2026: MCA Rates, Eligibility & Alternatives"
proposed_description: "Independent review of 365 Business Finance. UK merchant cash advance from £10k to £500k, factor rate 1.10 to 1.40. Pros, cons and 4 closest alternatives."
author: Oliver Mackman
date: 2026-08-04
---

## Why

"365 business finance" at pos 19.1 with 150 impressions and 0% CTR. Position 19 is page 2 — priority is position improvement, but the meta is also broken: the current description is an internal broker routing note ("Panel direct MCA lender we route to...") that was never written for a user-facing SERP snippet. It reads as internal jargon to someone searching the brand name.

The title template `${lender.name}: UK Business Finance Rates & Eligibility (2026)` also misses the product-type signal: 365 Business Finance is specifically a merchant cash advance lender, not a generic "business finance" provider. A searcher comparing MCA providers needs to see that at a glance.

## Implementation note

The title and description are generated from the `lenders.ts` data template in `src/pages/lenders/[slug].astro`:
- Line 13: `const title = \`\${lender.name}: UK Business Finance Rates & Eligibility (2026)\`;`
- Line 14: `const description = \`\${lender.summary.slice(0, 155)}\`;`

**Option A (recommended, targeted fix):** Add a `metaTitle` and `metaDescription` optional field to the Lender type and use them when present, falling back to the template. This lets us fix the worst pages without touching the template for clean pages.

**Option B (simpler):** Update the lender entry in `lenders.ts` to add a `metaTitle` and `metaDescription` field (or rename `summary` to have a public-facing variant). However this is a structural change that affects all lender pages.

For now: add `metaTitle` and `metaDescription` optional fields to the `365-business-finance` entry in `lenders.ts`, then update `[slug].astro` to prefer them.

## Proposed lenders.ts addition (in the 365-business-finance entry)

```ts
metaTitle: '365 Business Finance Review 2026: MCA Rates, Eligibility & Alternatives',
metaDescription: 'Independent review of 365 Business Finance. UK merchant cash advance from £10k to £500k, factor rate 1.10 to 1.40. Pros, cons and 4 closest alternatives.',
```

## Validation

After deploy: recheck GSC position and CTR on "365 business finance". A cleaner description and product-specific title should also support position improvement from 19 toward page 1 (target: sub-10).
