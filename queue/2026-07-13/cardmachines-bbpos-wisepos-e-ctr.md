# DRAFT: cardmachines — BBPOS WisePOS E review page CTR fix

**Site:** merchanthq.co.uk
**Page:** /reviews/bbpos-wisepos-e/ (or similar)
**GSC pos:** 7.4, 116 impressions, 0% CTR
**Priority:** HIGH — pos 7.4 with 116 impressions and 0% CTR is a strong signal the snippet
is either not compelling or the title does not match search intent
**Type:** title + meta rewrite

## Problem

0% CTR at pos 7.4 is unusual. Possible causes:
1. Title does not match what users see in the SERP (Google rewrites it)
2. Description is generic or missing
3. Users prefer a branded/manufacturer result above us
4. The terminal name is unfamiliar and the snippet does not clarify what it is

## Proposed title (58 chars)

"BBPOS WisePOS E Review 2026: Rates, Features and Best For"

## Proposed description (155 chars)

"The BBPOS WisePOS E is a countertop Android smart terminal used by Stripe. Our review covers
fees, contract, hardware and who it suits. Compare alternatives."

## Note

The reviewMeta override for BBPOS WisePOS E was added in commit a5e262f (2026-07-11) which
set ratingCount and ratingValue. Confirm that change is live; if yes, this is a snippet
content issue not a schema issue.

## Adam action

Check GSC: confirm URL and that the page is indexed. Then approve proposed title/meta and
apply to the terminal data file (src/data/terminals.ts overrideTitle/overrideDescription
fields, or the .astro page if overrides live there).
