# market-invoice — Title/Meta Rewrite: /providers/peak-cashflow

**Date queued:** 2026-07-04
**Type:** title-meta
**Priority:** high (pos 8.7, 243 impr, 0.41% CTR — top-ranked content gap on site)
**URL:** https://www.marketinvoice.co.uk/providers/peak-cashflow/
**Source file:** market-invoice/src/pages/providers/peak-cashflow.astro

## Why

"peak cashflow" drives 243 impressions at position 8.7 (bottom of page 1) with only 1 click (0.41% CTR). This is a brand query — someone looking specifically for Peak Cashflow, an independent invoice finance provider. Our review page should close that query with a compelling snippet but the current title sounds generic.

## Current

```javascript
const title = "Peak Cashflow Review 2026 - Rates, Fees & Features";
const description = "Peak Cashflow is an independent invoice finance provider established in 2007 in Birmingham. Small business focused with facilities up to £1m. Transparent.";
```

**Title length:** 50 chars. Good length, but "Rates, Fees & Features" is weak — reads like a template.
**Description:** 152 chars. Fine length but leads with dry facts rather than a hook.

## Recommended changes

```javascript
const title = "Peak Cashflow Review 2026: Invoice Finance for Small Business";
```
(61 chars — keeps the brand, adds the exact product category, signals small-biz angle)

```javascript
const description = "Independent review of Peak Cashflow, the Birmingham-based invoice finance specialist. Facilities from £25k to £1m. Transparent pricing, no hidden fees. Established 2007.";
```
(168 chars — factual differentiators up front, builds trust, no fabricated data)

## Also note

- The GSC query "accident credit group" is at pos 16.1 with 78 impr and 0 clicks — same template issue on that page. See sister draft: market-invoice-title-accident-credit-group.md
- If Peak Cashflow title change lifts CTR, apply the same hook pattern ("Review 2026: [product] for [audience]") across all /providers/ pages.

## Effort

Edit only — lines 10-11 in providers/peak-cashflow.astro. Build + push to main.
