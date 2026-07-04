# market-invoice — Title/Meta Rewrite: /providers/accident-credit-group

**Date queued:** 2026-07-04
**Type:** title-meta
**Priority:** medium (pos 16.1, 78 impr, 0% CTR — zero-click at page 2)
**URL:** https://www.marketinvoice.co.uk/providers/accident-credit-group/
**Source file:** market-invoice/src/pages/providers/accident-credit-group.astro

## Why

"accident credit group" is a brand query with 78 impressions at position 16.1 and zero clicks. People searching the brand name and landing on our review page should click through — the current title doesn't signal that we have a useful independent review, just a generic page.

## Current

```javascript
const title = "Accident Credit Group Review: Invoice Finance for Credit"
const description = "Accident Credit Group provides specialist invoice finance for credit hire and accident management businesses. Facilities from £50k. Full independent review.";
```

**Title length:** 56 chars. Decent but "Invoice Finance for Credit" reads truncated.
**Description:** 155 chars. Reasonable but buries the niche (accident management) that differentiates.

## Recommended changes

```javascript
const title = "Accident Credit Group Review 2026: Credit Hire Invoice Finance";
```
(62 chars — adds year, names the full niche "credit hire invoice finance" which is the real differentiator)

```javascript
const description = "Independent review of Accident Credit Group, specialist invoice finance for credit hire and accident management businesses. Facilities from £50k. Updated June 2026.";
```
(164 chars — leads with "independent review" trust signal, names both sectors, ends with freshness date)

## Effort

Edit only — lines 9-10 in providers/accident-credit-group.astro. Build + push to main.
Can batch this edit with the peak-cashflow title fix in the same commit.
