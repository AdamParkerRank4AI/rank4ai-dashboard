---
status: draft
site: cardmachines
type: meta_rewrite
target_query: bbpos wisepad 3
target_url: /reviews/bbpos-wisepad-3/
current_state: |
  title: "BBPOS WisePad 3: UK rates, fees and verdict 2026" (auto-generated, 49 chars)
  reviewMeta: "BBPOS WisePad 3 is the Stripe Bluetooth card reader for UK merchants (£59). MerchantHQ review: UK compatibility, connection, battery, acquirer setup and alternatives."
  GSC position: 13.4 with 189 impressions and 0.53% CTR (1 click)
proposed_change: |
  reviewMeta update in terminals.ts:
  "BBPOS WisePad 3 review: £59 Bluetooth card reader for Stripe Terminal. UK setup, battery life, pairing and the 3 best alternatives for merchants who need more."
  title: "BBPOS WisePad 3 Review 2026: UK Setup, Cost and Alternatives"
  (53 chars, within template's 60-char cap)
why: |
  'bbpos wisepad 3' gets 189 impressions/28d at position 13.4 with only 0.53% CTR (1 click). The
  auto-generated title (49 chars) ranks well but converts badly. The issue is "UK rates, fees and verdict"
  is generic for a product that has no variable rate (it's a hardware reader; rate is set by the acquirer).
  Searchers typing "bbpos wisepad 3" are typically looking for setup help, compatibility, or a buy/don't-buy
  verdict. The proposed title replaces "rates, fees" with "Setup, Cost and Alternatives" which better
  matches the actual review content and the 3 search intents (setup, cost, alternatives).
  Implementation: add `reviewMeta` field to the bbpos-wisepad-3 terminal entry in terminals.ts.
  No change to auto-title logic needed if the new reviewMeta is under 160 chars.
---
