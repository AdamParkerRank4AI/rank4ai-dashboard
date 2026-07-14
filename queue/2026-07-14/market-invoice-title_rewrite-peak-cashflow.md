# Title/Meta Rewrite: market-invoice /providers/peak-cashflow/

**Site:** marketinvoice.co.uk
**File:** `market-invoice/src/pages/providers/peak-cashflow.astro`
**Type:** title + description rewrite
**GSC signal:** "peak cashflow" 277 imp, pos 7.7, CTR 0.36%

## Current

```
title = "Peak Cashflow Review 2026 - Rates, Fees & Features"
description = "Peak Cashflow invoice finance for UK small businesses. Independent provider, Birmingham, facilities to £1m. Transparent pricing, fast decisions. Full 2026 review."
```

## Problem

277 impressions at pos 7.7 is page 1, but CTR of 0.36% is very low for a brand-name query. At pos 7-8 on page 1, a provider review should expect 2-4% CTR minimum. Something in the SERP snippet is failing to convert the impression.

Likely causes:
1. Title includes "Rates, Fees & Features" which is generic and doesn't differentiate.
2. Description doesn't lead with what makes Peak Cashflow distinctive (independent, Birmingham, small-business focus, transparent pricing).
3. "Full 2026 review" at the end is weak closing copy.

## Recommended replacement

```
title = "Peak Cashflow Review 2026: Invoice Finance Rates and Verdict"
description = "Peak Cashflow: independent Birmingham invoice finance provider, facilities to £1m, transparent pricing. Is it right for your business? MarketInvoice.co.uk review."
```

Rationale:
- Title adds "Verdict" which is a stronger CTR signal — searchers want to know if this provider is good.
- "Invoice Finance Rates and Verdict" is more specific than "Rates, Fees & Features".
- Description leads with the differentiators (independent, Birmingham, transparent) then adds a question-based hook.
- Branding "MarketInvoice.co.uk review" signals authority and source.
- Title length: 58 chars. Within 60-char limit.

## Action

Edit `title` and `description` constants in `peak-cashflow.astro` (lines 10-11).
No structural content changes needed.
Push to main. Run `npm run index` after deploy.
