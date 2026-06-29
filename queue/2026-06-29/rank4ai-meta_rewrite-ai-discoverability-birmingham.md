---
status: draft
site: rank4ai
type: meta_rewrite
target_query: ai discoverability birmingham
target_url: /who-we-help/birmingham/
current_state: |
  Position: 6.3, impressions: 76, clicks: 0, CTR: 0%
  The /who-we-help/birmingham/ page covers AI search visibility for Birmingham
  businesses. It ranks at position 6.3 — near the top of page 1 — but generates
  no clicks, suggesting the title or meta is not resonating with search intent.
proposed_change: |
  Title (proposed):
  "AI Discoverability for Birmingham Businesses | Rank4AI"

  Meta (new — 152 chars):
  "Rank4AI helps Birmingham businesses appear in ChatGPT, Gemini, Perplexity and Google AI Overviews. Local AI search visibility audit and strategy. Free check."

  Implementation: edit src/pages/who-we-help/birmingham/index.astro (or .astro file
  at that route), update `title` and `description` props on BaseLayout.
  Specifically:
  - Check if the title currently includes "AI Discoverability" — if not, rewrite to match
    the query intent exactly ("AI Discoverability for Birmingham Businesses")
  - Replace meta with the 152-char string above
why: |
  "ai discoverability birmingham" at position 6.3 with 76 impressions and 0 clicks
  is the best ratio of rank/impressions/CTR failure in the rank4ai fleet today:
  position 6 is page 1, yet not one of those 76 impressions converted to a click.
  This strongly suggests a title/meta mismatch. The query is very specific ("ai
  discoverability" + city), so users are clearly looking for local AI search help.
  If the title doesn't include "AI discoverability" (or uses "AI search" instead),
  Google's snippet won't bold-match the query, suppressing CTR. The proposed title
  mirrors the exact query phrase. The meta leads with the local outcome ("appear in
  ChatGPT") and ends with the conversion hook ("free check"). A single title+meta
  edit on a page already ranking pos 6 could convert 5-8% of impressions = 3-4
  additional monthly clicks from a niche but very high-intent query.
---
