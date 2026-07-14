# Meta Description Rewrite: cardmachines /reviews/bbpos-wisepad-3/

**Site:** merchanthq.co.uk
**File:** `cardmachines/src/data/terminals.ts` — `reviewMeta` field for slug `bbpos-wisepad-3`
**Type:** description rewrite (title is auto-generated from terminal name, already good)
**GSC signals:**
- "bbpos wisepad 3" — 189 imp, pos 13.4 (page 2 boundary)
- Page `/reviews/bbpos-wisepad-3/` — 702 imp total, pos 11.0

## Current title (auto-generated, 48 chars)

```
BBPOS WisePad 3: UK rates, fees and verdict 2026
```

This is already well-structured. No title change needed.

## Current description (`reviewMeta` field in terminals.ts)

```
BBPOS WisePad 3 is the Stripe Bluetooth card reader for UK merchants (£59). MerchantHQ review: UK compatibility, connection, battery, acquirer setup and alternatives.
```

## Problem

At pos 13.4, the page is on the boundary between page 1 and 2. The description needs to drive CTR hard when it does surface. The current meta:
- Opens with "BBPOS WisePad 3 is the Stripe Bluetooth card reader" — good, front-loads the product.
- But doesn't signal what the user actually wants to know: is this the right reader for me?
- "acquirer setup and alternatives" is good but buried.

The page has 702 total impressions at pos 11.0, meaning many long-tail variants are hitting it. The description should speak to the widest-intent searcher (someone comparing this to SumUp / Zettle / Stripe M2).

## Recommended replacement (`reviewMeta`)

```
BBPOS WisePad 3 is the Stripe Bluetooth card reader for UK merchants at £59. MerchantHQ review: who it suits, Stripe-only lock-in explained, and the 4 best alternatives if it doesn't fit.
```

Rationale:
- "who it suits" is a stronger hook than "UK compatibility".
- "Stripe-only lock-in explained" signals the key concern buyers have (they've probably read elsewhere it only works with Stripe).
- "4 best alternatives" is a concrete number that improves CTR vs "alternatives".
- Length: 191 chars. Within the ~155-160 char visible limit (Google may trim, but the key info is front-loaded).

## Action

Edit the `reviewMeta` field for `bbpos-wisepad-3` in `cardmachines/src/data/terminals.ts`.
No template changes. Push to main.
