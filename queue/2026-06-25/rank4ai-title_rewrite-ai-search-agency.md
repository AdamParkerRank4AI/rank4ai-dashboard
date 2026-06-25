---
status: draft
site: rank4ai
type: title_rewrite
target_query: ai search agency
target_url: https://rank4ai.co.uk/ (homepage — 859 impressions match closely; confirm in GSC query detail)
current_state: |
  Position: 14.8 | Impressions: 850 | Clicks: 3 | CTR: 0.35%
  Homepage is the most likely ranking page (impressions overlap). With 850 impressions at pos 14.8,
  this query sits mid-page-2 and gets almost no clicks. The site headline/title does not lead with
  the phrase "AI search agency" — it likely reads as a brand line rather than a category match.
proposed_change: |
  Homepage <title> tag change:
  BEFORE: whatever the current title is (check src/pages/index.astro)
  AFTER: "AI Search Agency UK: Rank in ChatGPT, Perplexity & AI Overviews | Rank4AI"

  Homepage meta description:
  "Rank4AI is a UK AI search agency helping brands get cited in ChatGPT, Perplexity, Gemini and
  AI Overviews. Entity-first SEO, structured content, and measurable AI citation uplift. Free audit."

  On-page anchor change: ensure the hero H1 or a visible sub-heading contains the exact phrase
  "AI search agency" early on the page. Currently the homepage may lead with brand language rather
  than category language.

  Also add a BreadcrumbList item anchored to the homepage in the schema (if not present).
why: |
  850 impressions means Google already associates rank4ai.co.uk with the query "ai search agency".
  At pos 14.8 the page sits mid-page-2 — a title change putting the exact phrase front of the tag
  typically shifts position 3 to 5 places. Moving from pos 14.8 to ~pos 9-12 would get the page
  onto the first page for a meaningful number of these searches. The current 0.35% CTR (3 clicks
  from 850 views) is also very low — a clearer title describing what the agency does would lift CTR
  as well as rank.

  Note: the related query "ai search agency uk" is already at pos 5.9 with 73 impressions and a
  1.37% CTR. Aligning the homepage title to the head-term ("ai search agency") rather than the
  geo-qualifier version unifies signal and should lift both queries.
priority: high
effort: low (title + meta tag change only, no content rewrite needed)
---
