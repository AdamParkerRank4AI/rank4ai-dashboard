---
status: draft
site: rank4ai
type: cannibalization_audit
target_query: ai search agency
why: |
  GSC shows "ai search agency" at position 13.2 with 864 impressions. Multiple pages
  compete for this query simultaneously:
  
  - /ai-search-agency/ (pos ~34, 719 impr)
  - /research/rankings/top-ai-search-agencies-london/ (pos ~23, 1708 impr)
  - /research/rankings/top-ai-seo-companies-uk/ (pos ~15, 1803 impr)
  - /research/rankings/best-ai-seo-agencies-uk/ (pos ~31, 11005 impr)
  
  The query "ai search agency" at pos 13 is probably rotating between these pages.
  
  Recommended action for Adam to review:
  1. Set a canonical on the research/rankings/* pages pointing to /ai-search-agency/
     if that is the intended canonical for this head term.
  2. OR consolidate: have /ai-search-agency/ redirect to the rankings page that
     has the best authority signals, and redirect /ai-seo/ to the same.
  3. Add internal links from the rankings pages BACK TO /ai-search-agency/ with
     anchor text "ai search agency" to signal which page should own the head term.
  
  This is a human-input decision about which URL should own the brand head term.
  The mechanical fix (canonical or redirect) can be shipped once the decision is made.
---
