---
status: draft
site: rank4ai
type: cannibalisation_consolidation
priority: high
target_data_file: cannibalisation.json (sites.rank4ai.top)
current_state: |
  R4 has 34 queries cannibalised across multiple pages. The biggest leaks
  (from cannibalisation.json first run, 24 May 2026):

  1. "ai search agency" — 350 imp split across 2 pages:
     - pos 14.7: /research/rankings/ai-search-agencies-compared/
     - pos 15.5: /research/rankings/top-ai-seo-agencies-uk-2026/

  2. "best ai search agency" — 104 imp split across 5 pages:
     - pos 1.0: /research/rankings/best-ai-search-agencies-uk/  (STRONGEST)
     - pos 1.0: /research/rankings/top-ai-search-agencies-uk/   (DUPLICATE)
     - pos 9.4: /research/rankings/top-ai-seo-agencies-uk-2026/
     - 2 more lower

  3. "chatgpt ranking optimisation service near me" — 114 imp split 2 ways:
     - pos 7.8: /research/rankings/best-chatgpt-seo-agencies-uk/  (STRONGEST)
     - pos 13.7: /chatgpt-ranking-optimisation-service/           (WEAKER)

  4. "claude visibility agency" — 95 imp split 2 ways:
     - pos 2.3: /services/claude-optimisation/                  (STRONGEST)
     - pos 12.2: /ai-search/claude-ranking-agency/              (WEAKER)
proposed_change: |
  Safest path: add rel="canonical" on the WEAKER page pointing at the
  STRONGER. This tells Google to consolidate ranking signal without
  removing the weaker page (preserves it for direct-link visitors and
  potential alternate-intent traffic).

  Specific changes:

  a) /ai-search/claude-ranking-agency/ → canonical /services/claude-optimisation/
     - Edit ~/rank4ai-site/src/pages/ai-search/claude-ranking-agency.astro
     - Pass canonical="/services/claude-optimisation/" to Layout
     - Verify Layout.astro supports canonical override (it does, line 15 props).

  b) /chatgpt-ranking-optimisation-service/ → canonical /research/rankings/best-chatgpt-seo-agencies-uk/
     - Same pattern.

  c) /research/rankings/top-ai-search-agencies-uk/ → canonical /research/rankings/best-ai-search-agencies-uk/
     - Both are at pos 1.0 for "best ai search agency" — pick best-ai-search-agencies-uk
       as canonical (newer URL pattern, matches user query better).

  d) /research/rankings/ai-search-agencies-compared/ — needs editorial judgment.
     Is this a methodology page (keep separate) or a duplicate ranking page
     (consolidate)? Skip until Adam reviews.

  After each edit:
    cd ~/rank4ai-site && npm run build (verify clean)
    git add -A && git commit -m "R4 cannibalisation: canonical X -> Y"
    git push origin main
why: |
  R4 has 1,020 pages. The cannibalisation isn't accidental — many of these
  are intentional retargeting attempts. But Google's seeing them as
  competing signals, which depresses overall ranking for the canonical
  page. Consolidating via rel=canonical (not 301) is the right move because:

  1. It signals to Google which page is canonical for ranking
  2. It preserves the weaker page for direct visitors + sister-site links
  3. It's fully reversible (just remove the canonical tag)
  4. It typically resolves cannibalisation within 2-4 weeks per Google's
     documented behaviour
needs_human_input: |
  Item (d) above — /research/rankings/ai-search-agencies-compared/ vs
  /research/rankings/top-ai-seo-agencies-uk-2026/. Both ranking pos 14-15
  for "ai search agency". Need editorial judgment: is "ai-search-agencies-compared"
  a methodology/comparison page (keep separate) or just an older variant
  (consolidate)? Surface to Adam before consolidating.
---
