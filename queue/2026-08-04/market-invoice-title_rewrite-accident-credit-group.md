---
status: draft
site: market-invoice
type: title_rewrite
target_query: accident credit group
target_url: /providers/accident-credit-group/
gsc_position: 13.7
gsc_impressions: 100
gsc_ctr: 0%
current_title: "Accident Credit Group: Invoice Finance for Credit Hire UK (2026)"
current_description: "Accident Credit Group invoice finance for UK credit hire and accident management businesses. Facilities from £50k. Rates, eligibility and full 2026 review."
proposed_title: "Accident Credit Group Review 2026: Invoice Finance for UK Credit Hire"
proposed_description: "Independent review of Accident Credit Group invoice finance. UK credit hire and accident management facilities from £50k. Rates, eligibility, pros and cons."
author: Oliver Mackman
date: 2026-08-04
---

## Why

"accident credit group" at pos 13.7 with 100 impressions and 0% CTR. At position 13.7 the page is at the bottom of page 1 / top of page 2. Zero clicks from 100 impressions signals the title and description are not compelling enough to pull clicks against branded results that dominate this query (the company's own site, Companies House, LinkedIn).

The word order matters: Google rewrites titles from the left. Leading with "Accident Credit Group Review 2026" immediately signals independent-review intent and includes the year freshness signal. The current title front-loads the brand name but buries "Review" in the URL structure, not the tag.

## Proposed changes

**Title:** `Accident Credit Group Review 2026: Invoice Finance for UK Credit Hire`
- "Review 2026" positioned at brand name — clear independent-review signal, click-worthy against branded SERP
- "UK Credit Hire" retains the vertical keyword

**Description:** `Independent review of Accident Credit Group invoice finance. UK credit hire and accident management facilities from £50k. Rates, eligibility, pros and cons.`
- "Independent review" is the click hook — differentiates from the company's own site and aggregators
- "pros and cons" is a high-CTR phrase in provider-review queries
- Drops "full 2026 review" (redundant with title) in favour of specifics

## File to edit

`market-invoice/src/pages/providers/accident-credit-group/index.astro` — update `title` and `description` constants near top of frontmatter.

## Validation

After deploy: 14-day CTR delta on "accident credit group". Target: CTR above 3% (brand-query reviews should pull high CTR from people in decision mode).
