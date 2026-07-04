# cardmachines — Title/Meta Rewrite: /reviews/bbpos-wisepad-3

**Date queued:** 2026-07-04
**Type:** title-meta
**Priority:** high (pos 17.2, 127 impr, 0% CTR — hardware query, near page 1, zero clicks)
**URL:** https://www.merchanthq.co.uk/reviews/bbpos-wisepad-3/
**Source file:** cardmachines/src/pages/reviews/[slug].astro, cardmachines/src/data/terminals.ts

## Why

"bbpos wisepad 3" gets 127 impressions at position 17.2 with zero clicks. This is a hardware lookup — someone researching a specific card reader. Our review page exists and ranks but the title isn't pulling. The current template generates from `reviewTitleCandidates`, which likely produces a 60-char title. The description is auto-generated from `terminal.summary`.

## Current (generated from terminals.ts)

Terminal data:
```
name: 'BBPOS WisePad 3',
manufacturer: 'BBPOS (white-labelled by Stripe and other Stripe Terminal SDK partners)',
summary: 'BBPOS WisePad 3 is the smaller mobile-first reader in the BBPOS family, white-labelled by Stripe and other Stripe Terminal SDK partners. Pairs with a phone, tablet or POS rather than running standalone. Cheapest entry point into the Stripe Terminal estate.'
```

Generated description: first 155 chars of summary — factually OK but dry.

## Recommended changes

Add `titleOverride` and `descriptionOverride` to the BBPOS WisePad 3 terminal entry in `terminals.ts`:

```typescript
// terminals.ts, bbpos-wisepad-3 entry:
titleOverride: 'BBPOS WisePad 3 Review 2026: Stripe Terminal Card Reader UK',
descriptionOverride: 'Full review of the BBPOS WisePad 3 mobile card reader. Works with Stripe Terminal SDK. Pairs with phone or tablet. Cheapest entry into the Stripe Terminal estate. UK pricing and alternatives.',
```

**Title:** 59 chars — exact query match + "Stripe Terminal" (high-value association) + "UK" (intent signal)
**Description:** 188 chars — direct, adds "UK pricing and alternatives" as CTR hook, stays factual

Then in [slug].astro:
```javascript
const titleOverride = terminal.titleOverride;
const title = titleOverride
  ? titleOverride
  : reviewTitleCandidates.find(t => t.length <= 60) ?? reviewTitleCandidates[reviewTitleCandidates.length - 1];
const description = terminal.descriptionOverride
  ? terminal.descriptionOverride
  : `Hands-on ${terminal.name} review by MerchantHQ. ${(terminal.summary.split(/(?<=[.!?])\s+/)[0] || terminal.summary.slice(0,155)).slice(0,155)}`;
```

## Also

"bbpos wisepos e" is pos 7.0 / 64 impr / 0% CTR — already page 1 but also zero clicks. Apply same description fix to the WisePOS E entry too. Quick batch in the same commit.

## Effort

Edit terminals.ts (add 2 optional fields to 2 entries) + update [slug].astro (4 lines). Build + push to main. 30 minutes.
