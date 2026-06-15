---
status: draft
site: rank4ai
type: title_rewrite
target_query: "ai overview optimisation agency"
target_url: /services/ai-overviews-optimisation/
current_state: "AI Overviews Optimisation Agency UK | Rank4AI"
proposed_change: "AI Overview Optimisation Agency UK | Rank4AI"
why: >
  209 impressions at position 14.2 with 0% CTR. The query uses the singular
  "overview" but the title uses the plural "Overviews". Google's query
  matching treats this as a soft mismatch and the title can fail to bold in
  the SERP, reducing click signal. Proposed fix: singular "Overview" to match
  the query exactly. One word change, no semantic loss.
---

## Context

This service page targets UK businesses looking for an agency that optimises
for Google's AI Overviews feature. 0% CTR across 209 impressions is a
strong signal the title is not triggering clicks, likely because the plural
"Overviews" does not exactly match "AI overview optimisation agency".

Google bolds the matching terms in SERP titles. "AI Overviews Optimisation"
does not bold for the singular query; "AI Overview Optimisation" does.

## Proposed title

```
AI Overview Optimisation Agency UK | Rank4AI
```

44 chars. Singular to match the query. Everything else stays the same.

## Change required

Edit `/src/pages/services/ai-overviews-optimisation.astro` frontmatter:

```astro
<Layout title="AI Overview Optimisation Agency UK | Rank4AI"
```

No body copy changes needed. H1 ("AI Overviews Optimisation Agency") can
stay plural as it is not the ranking signal here.
