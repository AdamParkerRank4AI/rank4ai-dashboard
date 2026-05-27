---
status: draft
site: rank4ai
type: title_rewrite
target_query: ai overview optimisation agency
target_url: /services/ai-overviews-optimisation/
current_state: |
  title: "AI Overviews Optimisation Agency UK | Rank4AI"
  description: "UK company specialising in AI Overviews optimisation. Get your business cited inside Google's AI Overview answers above the ten blue links. Five Signal Model, 1,400+ UK audits. Free AI visibility check."
proposed_change: |
  title: "AI Overviews Optimisation Agency UK | Get Cited in Google AI | Rank4AI"
  description: "Rank4AI is a UK AI Overviews optimisation agency. We get your business cited inside Google AI Overview answers, not just ranked below them. Five Signal Model, 1,400+ UK audits. Free AI visibility check."
why: |
  GSC data: "ai overviews optimisation agency" pos 6.9, 39 imps, 0% CTR (page 1, zero clicks).
  "ai overview optimisation agency" pos 17.0, 142 imps, 0% CTR.
  Page-1 position with zero CTR means the meta description is not earning the click. The current
  description says "cited inside Google's AI Overview answers above the ten blue links" which is
  ambiguous — the word "above" can read as positional (above the links) not as the outcome (cited
  IN the AI Overview). Proposed rewrite makes the outcome explicit: "cited inside Google AI Overview
  answers, not just ranked below them." This directly addresses searcher intent (they want to appear
  IN the AI Overview box, not in traditional results beneath it). Also adds "Get Cited in Google AI"
  to the title for scannability in SERP.
  
  File to edit: src/pages/services/ai-overviews-optimisation.astro
  Lines to change: frontmatter `title` and `description` props in the Layout component call.
---

## Implementation notes

In `rank4ai-preview/src/pages/services/ai-overviews-optimisation.astro`, update the Layout props:

```astro
<Layout
  title="AI Overviews Optimisation Agency UK | Get Cited in Google AI | Rank4AI"
  description="Rank4AI is a UK AI Overviews optimisation agency. We get your business cited inside Google AI Overview answers, not just ranked below them. Five Signal Model, 1,400+ UK audits. Free AI visibility check."
>
```

No body copy changes needed. Title + description only.
