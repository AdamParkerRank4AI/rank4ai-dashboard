---
status: draft
site: rank4ai
type: title_rewrite
target_query: "ai search agency"
target_url: /ai-search-agency/
current_state: "AI Search Agency UK: Get Cited by ChatGPT & Gemini"
proposed_change: "AI Search Agency UK: ChatGPT, Gemini and AI Overviews | Rank4AI"
why: >
  872 impressions at position 16.9 with 0.11% CTR. The current title leads
  with a command verb phrase ("Get Cited by") which is benefit framing, not
  query-match framing. Searchers typing "ai search agency" are looking to hire
  one. Proposed title front-loads the query match, lists the three AI channels
  that matter to UK buyers, and closes with the brand. No em dash. Character
  count: 64 (under 65-char Google display window).
---

## Context

Rank4AI's core commercial page. The query "ai search agency" has the
highest impression volume of any non-brand query (872 in the GSC window).
CTR at 0.11% means roughly one click per 900 impressions, which is the
floor for a page-2 result. Moving to page 1 requires a title that signals
"this is the agency" rather than "this is what the agency does for you".

## Proposed title

```
AI Search Agency UK: ChatGPT, Gemini and AI Overviews | Rank4AI
```

64 chars. Front-loads the match phrase, names the three channels UK buyers
recognise (ChatGPT, Gemini, AI Overviews), ends with brand. Drops the
"& Gemini" shortcut that truncated the original.

## Alternative (shorter, less channel detail)

```
UK AI Search Agency | ChatGPT, Gemini, AI Overviews | Rank4AI
```

62 chars. Moves "UK" before "AI" which some title tests suggest improves
UK-user click confidence, but splits the natural "AI Search Agency" phrase.

## Change required

Edit `/src/pages/ai-search-agency.astro` line 9:

```astro
<Layout
  title="AI Search Agency UK: ChatGPT, Gemini and AI Overviews | Rank4AI"
```

No body copy changes needed.
