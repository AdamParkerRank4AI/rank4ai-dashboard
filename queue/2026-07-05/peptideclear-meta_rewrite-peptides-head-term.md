# Meta rewrite: peptideclear.co.uk — "peptides" head term

**Site:** peptideclear.co.uk (ukmetabolic repo)
**Type:** meta_rewrite
**Date queued:** 2026-07-05
**Priority:** medium (133 imp, pos 60.9 — deep ranking, head term, long journey)

## Signal

GSC: "peptides" — 133 impressions, avg position 60.9.
This is the top head term for the site. Position 60.9 means page 6 — very deep,
but the impressions show Google is already associating the site with this query.
A meta rewrite won't move the needle alone, but it ensures we're not leaving
click-through on the table when/if we rank higher. Pair with a Speakable schema
review and entity-building work (Wikidata).

## Current page

Almost certainly the homepage / (index.astro).
Confirm in GSC URL filter.

## Recommended meta rewrite

Current description (from index.astro):
"Independent UK editorial comparison of peptide skincare, ingestible collagen,
research peptides, and prescription weight-loss GLP-1 routes. No paid placements."
(165 chars — slightly over 160 target but acceptable)

Proposed improvement — lead with the query, add structured signal:
`UK peptides compared: cosmetic peptides, ingestible collagen, research peptides and GLP-1 routes. Independent editorial. No paid placements.`
(140 chars — fits cleanly, leads with "UK peptides")

## Title check

Current: "PeptideClear: UK peptides, collagen and GLP-1 compared"
(54 chars without suffix — fits)

The title is fine. The word "peptides" appears early. No change needed on title.

## Author

Oliver Mackman (sole author on this site).

## Action needed

1. Update `description` in index.astro frontmatter to the proposed version.
2. Git push to main on ~/ukmetabolic (or use GitHub MCP if git push 503s again).
3. This is a soft improvement — prioritise below the Wikidata entity work
   (which addresses the root cause of the low ranking on head terms).

## Broader context

The head-term ranking gap for PeptideClear is primarily an entity/authority issue
(site is 6 weeks old). The Wikidata stub and Wikipedia disambiguation mention
(Adam action) will do more for this than any on-page change.
Surface to Adam: Wikidata stub for PeptideClear needs to be created as part of
the fleet-wide Wikidata push flagged in FLEET_INBOX.md.
