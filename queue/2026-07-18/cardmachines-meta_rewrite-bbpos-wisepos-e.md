---
status: draft
site: cardmachines
type: meta_rewrite
target_query: bbpos wisepos e
target_url: /reviews/bbpos-wisepos-e/
current_state: |
  title: "BBPOS WisePOS E: UK rates, fees and verdict 2026" (48 chars, auto-generated)
  reviewMeta: "BBPOS WisePOS E is the Stripe smart terminal for UK merchants (£249). MerchantHQ review: UK compatibility, acquiring fees, setup and the 4 closest alternatives."
  GSC position: 7.4 with 116 impressions and 0% CTR (0 clicks)
proposed_change: |
  reviewMeta update in terminals.ts:
  "BBPOS WisePOS E: the £249 Android smart terminal behind Stripe Terminal. MerchantHQ 2026 review: UK setup, acquirer fees, build quality and the 4 best alternatives."
  title: "BBPOS WisePOS E Review 2026: Stripe Terminal, Cost & Verdict"
  (57 chars, within template's 60-char cap)
why: |
  'bbpos wisepos e' gets 116 impressions/28d at position 7.4 with ZERO clicks. Position 7.4 is top of
  page 1 and zero CTR is a strong signal of a title/description mismatch. The current auto-generated
  title "BBPOS WisePOS E: UK rates, fees and verdict 2026" is accurate but not compelling at position 7.
  At that position, the snippet competes directly with Stripe's own documentation. The proposed title
  adds "Stripe Terminal" as a secondary keyword (that's what searchers actually want, the underlying
  platform) and changes "rates, fees" to "Cost and Verdict" which is more concrete for hardware review intent.
  This is the highest-urgency fix on MerchantHQ: position 7.4 with 0 clicks means every impression is
  wasted. Even a 3% CTR would yield 3 clicks/28d from this one query.
  Implementation: update `reviewMeta` field on the bbpos-wisepos-e entry in
  /home/user/cardmachines/src/data/terminals.ts. No other file changes needed.
---
