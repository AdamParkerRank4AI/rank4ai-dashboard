# DRAFT: market-invoice — meta rewrite for "accident credit group" query

**Site:** marketinvoice.co.uk
**Query:** "accident credit group"
**GSC pos:** 13.7, 100 impressions
**Priority:** MEDIUM — pos 13.7, page 2; possible entity confusion or thin match
**Type:** meta/title rewrite or new page decision

## Context

"Accident Credit Group" is likely a specific invoice finance / asset-based lender serving
personal-injury law firms, medical clinics, or credit-hire companies. Market Invoice ranking
for this query at pos 13.7 suggests a partial keyword match but no dedicated page.

## Options

A. **If Accident Credit Group is already a provider in the Market Invoice database:**
   Check `src/data/providers.ts` (or equivalent). If they are listed, their individual page
   may need a meta/title rewrite to mention "accident credit group" in the first 40 chars of
   the title, and the page intro should confirm they serve accident-related credit.

B. **If they are NOT in the database:**
   Evaluate whether to add them as a listed provider. If the niche is personal-injury / credit-
   hire, it may be worth a dedicated comparison page: "Invoice Finance for Accident Management
   Companies" or similar.

## Immediate action

1. Search `src/data/` in market-invoice for "accident" to confirm if provider is already listed
2. If listed: rewrite their page title to include "Accident Credit Group" verbatim
3. If not listed: add to content plan as a niche vertical

## Adam action

Check GSC to confirm which URL is ranking. If it is a provider page, approve meta update.
If no existing page, decide whether to add this niche vertical.
