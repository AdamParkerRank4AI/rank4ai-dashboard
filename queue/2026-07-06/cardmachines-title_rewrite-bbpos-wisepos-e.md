---
status: draft
site: cardmachines
type: title_rewrite
target_query: "bbpos wisepos e"
target_url: /reviews/bbpos-wisepos-e/
current_state: |
  title: (generated — likely "BBPOS WisePOS E Review 2026 | MerchantHQ")
  meta: "Hands-on BBPOS WisePOS E review by MerchantHQ. Compact handheld with touchscreen..."
proposed_change: |
  title: "BBPOS WisePOS E Review: Stripe Countertop Terminal UK Price & Specs"
  meta: "BBPOS WisePOS E review for UK merchants. Stripe Smart Reader with full touchscreen: £249, WiFi/4G/Bluetooth, custom acquirer rates. Independent verdict. MerchantHQ."
why: |
  "bbpos wisepos e" has 64 impressions at pos 7.0 — barely off page 1, but 0 CTR despite
  being ~top of page 2. This is very close to the page 1 threshold; a title/meta improvement
  combined with minor on-page work could push it over.

  BBPOS WisePOS E is Stripe's flagship countertop Smart Reader. Users searching this term
  are almost all Stripe Terminal evaluators comparing hardware before purchasing. The key
  differentiators they care about: it has a full touchscreen (unlike the WisePad 3 which
  pairs with a phone), WiFi/4G connectivity, and is priced at £249 (Stripe list).

  The proposed title adds "Stripe Countertop Terminal" (exact context for the audience and
  a secondary search phrase), "UK Price & Specs" (covers the two highest-intent micro-queries
  for hardware reviews). The meta includes the actual price (£249) and connectivity specs,
  which are the first things a buyer wants to confirm. "Custom acquirer rates" is accurate
  per terminals.ts and signals this is a real review not a placeholder.

  Same implementation approach as WisePad 3: add a `reviewTitle` override field in
  terminals.ts or use a per-slug title map in [slug].astro. Both terminals can be done in
  one edit.
---
