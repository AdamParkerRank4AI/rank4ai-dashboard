---
status: draft
site: rank4ai
type: title_rewrite
target_query: ai search agency
target_url: https://rank4ai.co.uk/
current_state: |
  Title: "Rank4AI - UK AI Search Agency | AI Search Visibility"
  Position: 14.8 (page 2)  |  Impressions: 850  |  CTR: 0.35%  |  Clicks: 3
proposed_change: |
  Title: "AI Search Agency UK | Rank4AI"
  Description (keep current or tighten to): "Rank4AI is a UK AI search agency. We get businesses recommended by ChatGPT, Claude, Gemini, Perplexity and Google AI Overviews."
why: |
  "ai search agency" has 850 monthly impressions at position 14.8 — first result on page 2, earning just 3 clicks. The current title leads with the brand name ("Rank4AI - UK AI Search Agency") which is structurally correct for brand recognition but buries the exact query term. GSC shows 0.35% CTR against an expected ~5% for page-1, meaning even if ranking improved tomorrow, the click-through would still lag.

  Front-loading the exact query phrase ("AI Search Agency UK") and shortening the title (31 chars vs 50) makes the snippet scannable and query-matching at a glance. Brand at the end is standard practice for non-branded queries. UK specificity signals local relevance which matters for service queries.

  Secondary benefit: a tighter, query-first title signals on-page relevance to the ranking algorithm, which may help move the page from pos 14.8 to page 1.

  Implementation: edit `src/pages/index.astro` Layout title prop.
---
