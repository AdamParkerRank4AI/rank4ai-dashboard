---
status: draft
site: fundbiz
type: title_rewrite
target_query: iwoca alternatives
target_url: /alternatives/iwoca/
gsc_position: 13.2
gsc_impressions: 72
gsc_ctr: 1.39%
current_title: "Best Alternatives to iwoca (2026): UK Business Finance Compared"
current_description: "4 UK business finance alternatives to iwoca compared on rate, ticket, decision time and eligibility."
proposed_title: "iwoca Alternatives 2026: 4 UK Business Finance Lenders Compared"
proposed_description: "The 4 closest UK alternatives to iwoca for SMB lending: Funding Circle, Allica Bank, Capify, 365 Business Finance. Compared on rate, ticket, speed and eligibility."
author: Oliver Mackman
date: 2026-08-04
---

## Why

"iwoca alternatives" at pos 13.2 with 72 impressions and 1.39% CTR. Position 13 is page 1 bottom / page 2 top with a reasonable existing CTR of 1.39%. There is headroom to improve both position and CTR.

The current title leads with "Best Alternatives to" which is a listicle framing — good for long-tail but the query "iwoca alternatives" is a navigational/comparison query where users want to find the alternatives page quickly. Leading with the brand name ("iwoca Alternatives 2026") is the more natural match.

The current description is very short (under 100 chars) and does not name any of the alternatives. Naming the 3-4 actual alternatives in the description is high-CTR for alternatives queries because users scanning SERP snippets are looking for their shortlisted provider to appear.

## Implementation note

The title and description are generated from the template in `src/pages/alternatives/[slug].astro`:
- Line 28: `const title = \`Best Alternatives to \${subject.name} (2026): UK Business Finance Compared\`;`
- Line 29: `const description = \`4 UK business finance alternatives to \${subject.name} compared on rate, ticket, decision time and eligibility.\`.slice(0, 158);`

The alternatives for iwoca (from `alternatives.ts`) should be checked to confirm which 4 are listed. The description names them explicitly.

**Option A (targeted fix):** Add `metaTitle` and `metaDescription` optional fields to the ALTERNATIVES data or lender entry, use when present, fall back to template. Same pattern as the 365 Business Finance fix above.

**Option B:** Improve the alternatives template description to include the first 2-3 alternative names. For the iwoca page the description becomes ~170 chars with 4 names so this needs slicing to 158 — naming the first 3 is enough.

## Proposed description (158-char version)

Check the 4 iwoca alternatives in `src/data/alternatives.ts` to confirm the names. Based on vs-pairs.ts the key alternatives are Funding Circle, Allica Bank, Capify and 365 Business Finance. If confirmed:

`The 4 closest UK alternatives to iwoca: Funding Circle, Allica Bank, Capify, 365 Business Finance. Compared on rate, ticket size, decision speed and eligibility.`

(161 chars — trim "and eligibility" to hit 158)

## Validation

After deploy: 14-day CTR delta on "iwoca alternatives". CTR target: above 3% (alternatives queries pull high intent). Position target: sub-10.
