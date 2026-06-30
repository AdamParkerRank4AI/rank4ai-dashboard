---
status: draft
site: cardmachines
type: title_rewrite
target_query: bbpos wisepad 3
target_url: /reviews/bbpos-wisepad-3/
current_state: |
  Title (generated from template): "BBPOS WisePad 3 vs [other] compared: UK 2026" for vs pages;
  Review page title is dynamically generated — check [slug].astro title template.
  Likely: "BBPOS WisePad 3 Review: UK Card Reader [year]" or similar.
proposed_change: |
  Review page title: "BBPOS WisePad 3 Review UK 2026: Stripe Terminal Card Reader"
  Description (under 158 chars): "BBPOS WisePad 3 is a £59 Bluetooth card reader white-labelled by Stripe. MerchantHQ independent review: specs, rate, Stripe Terminal SDK setup, and who it suits."
why: |
  GSC: pos 17.2 for "bbpos wisepad 3" (127 impressions, 0% CTR). The query is product-specific;
  users are researching before buying or setting up. The current template title may not include
  "Stripe Terminal" which is the key purchase context — most buyers searching "bbpos wisepad 3"
  are Stripe merchants. Adding "Stripe Terminal Card Reader" to the title matches the mental model
  and improves CTR. Also signals to Bing (primary channel) exactly what the page is about.
  This is a per-terminal title override in terminals.ts or the [slug].astro template, not a
  global template change.
---
