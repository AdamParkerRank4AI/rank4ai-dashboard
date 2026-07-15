---
status: draft
site: cardmachines
type: title_rewrite
target_query: bbpos wisepos e
target_url: /reviews/bbpos-wisepos-e/
current_state: |
  Title generated from template: "BBPOS WisePOS E: UK rates, fees and verdict 2026" (50 chars, first candidate from reviewTitleCandidates).
  Meta (reviewMeta already set in terminals.ts line 148): "BBPOS WisePOS E is the Stripe smart terminal for UK merchants (£249). MerchantHQ review: UK compatibility, acquiring fees, setup and the 4 closest alternatives."
  Position 7.4, 116 impressions, 0 clicks, 0% CTR over 28-day period.
proposed_change: |
  Add `reviewMeta` to the BBPOS WisePOS E entry in terminals.ts:
  reviewMeta: "BBPOS WisePOS E UK review 2026: compact handheld card terminal for Stripe developers. Rates, specs and who it suits. Independent MerchantHQ verdict."
  
  Also check: does the review page at /reviews/bbpos-wisepos-e/ currently have 0 clicks because CTR is extremely low, OR because something else is wrong (canonical issue, noindex flag)? Position 7.4 is solidly page 1 — at that position, 0% CTR over a 28-day period with 116 impressions is a red flag beyond just a weak meta description. The page may be rendering a title tag that is not capturing the query signal, or the search snippet may be showing auto-generated content instead of the meta description.
  
  Priority action: inspect the actual SERP snippet for "bbpos wisepos e" and check if MerchantHQ's result is showing. If the listing appears with a garbled auto-snippet, fixing the meta description is the key lever. If the page is ranking but the listing is suppressed (schema error, manual action) that needs escalating.
why: |
  This is the single most actionable issue on the cardmachines site today. A page at position 7.4 with 116 impressions and 0 clicks in 28 days is anomalous. Normal page-1 CTR at position 7-8 is 2-4%. If the meta + title are clean, you would expect 2-5 clicks per 28 days. Something is wrong with how the snippet is appearing in the SERP. Fix this first: check the snippet live, then update the reviewMeta field.
---
