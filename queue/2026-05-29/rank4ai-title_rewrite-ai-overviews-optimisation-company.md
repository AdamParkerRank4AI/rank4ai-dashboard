---
status: draft
site: rank4ai
type: title_rewrite
target_query: ai overviews optimisation company
target_url: /services/ai-overviews-optimisation/
current_state: |
  title: "AI Overviews Optimisation Agency UK | Rank4AI"
  description: "UK company specialising in AI Overviews optimisation. Get your business cited inside Google's AI Overview answers above the ten blue links. Five Signal Model, 1,400+ UK audits. Free AI visibility check."
proposed_change: |
  title: "AI Overviews Optimisation Agency UK | Get Cited in Google AI | Rank4AI"
  description: "Rank4AI is a UK AI Overviews optimisation company. We get your business cited inside Google AI Overview answers, not just ranked below them. Five Signal Model, 1,400+ UK audits. Free AI visibility check."
why: |
  GSC data: "ai overviews optimisation company" pos 12.3, 33 imps, 0% CTR (near page 1, zero clicks).
  Also "ai overview optimisation agency" pos 17.0, 142 imps, 0% CTR.

  The current description uses the word "agency" only. Searchers using "company" are a distinct
  intent group (more transactional, less creative-services frame). Adding "company" to the
  description alongside "agency" captures both variants from a single page.

  The proposed description also fixes the ambiguous phrase "above the ten blue links" (reads
  positionally, not as the outcome) with "not just ranked below them" which is unambiguous.

  Note: a companion draft for the "agency" variant is in queue/2026-05-27/rank4ai-title_rewrite-ai-overview-optimisation-agency.md.
  Both target the same file; apply both changes together in one edit.

  File to edit: rank4ai-preview/src/pages/services/ai-overviews-optimisation.astro
  Line to change: Layout props `title` and `description`.
---

## Implementation notes

In `rank4ai-preview/src/pages/services/ai-overviews-optimisation.astro`, update the Layout props:

```astro
<Layout
  title="AI Overviews Optimisation Agency UK | Get Cited in Google AI | Rank4AI"
  description="Rank4AI is a UK AI Overviews optimisation company. We get your business cited inside Google AI Overview answers, not just ranked below them. Five Signal Model, 1,400+ UK audits. Free AI visibility check."
>
```

Note the word "company" in the description captures the "ai overviews optimisation company" query
variant. The title uses "Agency" (higher volume term) while the description includes "company"
to satisfy both intent clusters from the same page. No body copy changes needed.
