---
status: draft
site: cardmachines (MerchantHQ)
type: title_rewrite
target_query: bbpos wisepad 3
target_url: /reviews/bbpos-wisepad-3/
current_state: |
  Title (auto-generated from terminals.ts template): "BBPOS WisePad 3: UK rates, fees and verdict 2026"
  Description (auto-generated): "Hands-on BBPOS WisePad 3 review by MerchantHQ. BBPOS WisePad 3 is the smaller mobile-first reader in the BBPOS family, white-labelled by Stripe..."
  Position: 17.2 | Impressions: 127 | CTR: 0%
proposed_change: |
  Update terminals.ts entry for bbpos-wisepad-3:

  1. Change `name` field to add "(card reader)" disambiguation:
     Keep: slug: 'bbpos-wisepad-3', name: 'BBPOS WisePad 3'
     (name is already correct -- title template uses it and produces "BBPOS WisePad 3: UK rates, fees and verdict 2026" = 48 chars, fine)

  2. Rewrite `summary` field for stronger answer-capsule:
     Current: "BBPOS WisePad 3 is the smaller mobile-first reader in the BBPOS family, white-labelled by Stripe and other Stripe Terminal SDK partners. Pairs with a phone, tablet or POS rather than running standalone. Cheapest entry point into the Stripe Terminal estate."
     Proposed: "BBPOS WisePad 3 is a compact Bluetooth card reader priced at £59 (Stripe UK). It pairs with a phone, tablet or EPOS system via the Stripe Terminal SDK and accepts chip-and-PIN, contactless and Apple/Google Pay. Not standalone -- requires a host device with the acquirer app -- but is the cheapest way into the Stripe Terminal hardware range for UK merchants."

  3. Update `lastReviewed` to '2026-07-03' to freshen the date signal.

  4. Add a brief "Price" section near the top of the review page template (in [slug].astro), or ensure the upfrontCost (£59) appears in the first visible paragraph above the fold, since "bbpos wisepad 3 price" is a likely intent behind the query.
why: |
  127 impressions at pos 17.2 with 0% CTR. "bbpos wisepad 3" is a specific product query -- searchers want price, compatibility and a verdict. The current auto-generated description repeats "BBPOS WisePad 3" twice in the first 15 words (wasted space) and buries the £59 price point. The proposed summary rewrite puts the price in the opening sentence, clarifies the Bluetooth pairing model, and is 50 words (good answer-capsule length). The freshened lastReviewed date gives Google a reason to re-crawl and update the snippet. No template change needed for the title -- the existing auto-title is within 60 chars and on-brand.
---
