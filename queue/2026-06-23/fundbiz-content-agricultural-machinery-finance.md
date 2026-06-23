# Content improvement: /asset-finance/tractor-finance/ — fundbiz.co.uk

**Type:** title-rewrite + content-improvement quick-win
**Site:** fundbiz
**Priority:** high (pos 11.9 = edge of page 1)
**Query:** "agricultural machinery finance" — 15 impressions, pos 11.9, 0% CTR
**Source page:** src/data/asset-types.ts (slug: tractor-finance) → /asset-finance/tractor-finance/

## Current state
- Title: "Tractor and agricultural machinery finance UK"
- Slug: tractor-finance
- Page: /asset-finance/tractor-finance/

## Problem
Pos 11.9 is right on the page 1/2 boundary. The query is "agricultural machinery finance" but the title leads with "Tractor and". The slug is `tractor-finance` which is also sub-optimal for this query.

## Recommended changes

**Option A: Change name in asset-types.ts (changes H1 and title)**
Change from: `name: 'Tractor and agricultural machinery finance'`
Change to: `name: 'Agricultural machinery finance'`
New title would be: "Agricultural machinery finance UK"
New H1 would be: "Agricultural machinery finance"

This directly targets the query. Note: "tractor finance" is also a valid query — check if there's a separate "tractor finance" query to preserve. If not, the rename is clean.

**Option B: Add a `titleOverride` field**
Add `titleOverride: 'Agricultural Machinery Finance UK: Tractors, Combines and Farm Kit'` to the asset-types entry and update the [slug].astro template to use it.

## Content depth additions to asset-types.ts entry
The intro already covers the topic well. Consider adding:
- A specific rate guide (typical: 4-8% APR HP; 3-6% APR finance lease on new machinery)
- Named lenders in body: Oxbury Bank, AGCO Finance, John Deere Financial, CNH Industrial Capital, Aldermore (already in topLenders but not prose)
- BPS/SFI subsidy timing note as a callout block

## Recommended action
1. Rename the asset type `name` to "Agricultural machinery and tractor finance" (puts the query keyword first without losing tractor finance coverage)
2. Update `title` template in [slug].astro if needed to ensure <= 60 chars
3. Submit /asset-finance/tractor-finance/ to Google Indexing API after publish
