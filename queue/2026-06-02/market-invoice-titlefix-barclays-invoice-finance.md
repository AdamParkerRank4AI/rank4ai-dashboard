# Title fix: /providers/barclays/

**Site:** marketinvoice.co.uk
**Type:** title + meta rewrite
**Priority:** MEDIUM
**GSC signal:** "barclays invoice finance" — pos 12.3, 26 impressions, 0% CTR (28-day period to 2026-05-19)
**Secondary signals:** "barclays invoice factoring" pos 9.0, 14 impr | "barclays invoice financing" pos 12.1, 12 impr
**Author:** Oliver Mackman

## Problem

Pos 12 means page 2 result. 0% CTR confirms no clicks at all from 26 impressions. The current title
truncates and does not include the word "compare" or the year, which reduces urgency.

Current title (from crawl):
> Barclays Invoice Finance 2026: Rates, Eligibility, Revi...

(Title is being cut — likely too long or missing strong hook)

## Proposed title

> Barclays Invoice Finance 2026: Rates, Limits and Alternatives

Changes:
- Adds "Alternatives" — the most common next intent after searching a bank's own product name is comparison
- Removes vague "Revi..." (probably "Review") which at pos 12 adds no pull
- Stays within ~60 chars

## Proposed meta description (155 chars)

Barclays invoice finance: rates, eligibility and what to ask. Plus: how Barclays compares to Lloyds, HSBC and independent providers. No broker fee for initial quote.

## File

`src/pages/providers/barclays.astro` (or equivalent)
Change `title` and `description` constants only.

## Note

The page already has 15 internal_links_in. Internal linking is not the issue here. Pure title/meta CTR play.
