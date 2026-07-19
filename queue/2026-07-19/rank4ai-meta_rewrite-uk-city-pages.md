---
status: draft
site: rank4ai
type: meta_rewrite
target_query: (multiple city/industry combos)
target_url: /uk/{city}/{industry}/ (20+ pages)
current_state: "All /uk/ city pages have descriptions of 190-202 chars (over 160 char limit)"
proposed_change: "Batch-shorten the description on all /uk/ city pages from ~200 chars to ~145 chars"
why: |
  The 20+ programmatic UK city/industry pages (/uk/london/dentists/,
  /uk/manchester/accountants/, etc.) each have a hardcoded description of
  190-202 chars. These are individual .astro files (not a single template),
  so a batch find-and-replace is the right approach. The current description
  pattern is: "Free AI search visibility audit for [profession] in [City].
  Test your firm across ChatGPT, Claude, Gemini, Perplexity, Copilot and
  Google AI Overviews. Delivered in five working days by Rank4AI." (198 chars)
  A shorter version fits under 160 chars while keeping the key signals.
---

## Proposed fix

Run this from `/home/user/rank4ai-preview/`:

```bash
find src/pages/uk -name "*.astro" | while read f; do
  # Extract city and profession from the file path
  city=$(echo "$f" | cut -d'/' -f5 | sed 's/-/ /g' | sed 's/\b\w/\u&/g')
  prof=$(basename "$f" .astro | sed 's/-/ /g')
  new_desc="Free AI visibility audit for ${prof} in ${city}. See exactly how you appear in ChatGPT, Gemini, Perplexity and Google AI Overviews. Five working days."
  # Use sed to replace the description (careful: sed should be scoped to the Layout description prop)
  # REVIEW BEFORE RUNNING — check the exact string patterns
done
```

**Alternative:** Open each file and shorten the description manually. There are 20 files — a 30-minute task.

**Proposed short description pattern:**
"Free AI visibility audit for [profession] in [City]. See exactly how you appear in ChatGPT, Gemini, Perplexity and Google AI Overviews. Five working days." (156 chars)

## Files to update
src/pages/uk/london/dentists.astro
src/pages/uk/london/accountants.astro
src/pages/uk/london/law-firms.astro
src/pages/uk/manchester/dentists.astro
src/pages/uk/manchester/accountants.astro
src/pages/uk/manchester/law-firms.astro
src/pages/uk/birmingham/dentists.astro
src/pages/uk/birmingham/accountants.astro
src/pages/uk/birmingham/law-firms.astro
src/pages/uk/bristol/dentists.astro
src/pages/uk/bristol/accountants.astro
src/pages/uk/bristol/law-firms.astro
src/pages/uk/leeds/dentists.astro
src/pages/uk/leeds/accountants.astro
src/pages/uk/leeds/law-firms.astro
(+ any additional city/industry combos added since last review)
