---
status: draft
site: cardmachines
type: meta_rewrite
target_query: bbpos wisepad 3
target_url: https://merchanthq.co.uk/reviews/bbpos-wisepad-3/
current_state: |
  Title: "BBPOS WisePad 3: UK rates, fees and verdict 2026"
  Description (reviewMeta): "BBPOS WisePad 3 is the Stripe Bluetooth card reader for UK merchants (£59). MerchantHQ review: UK compatibility, connection, battery, acquirer setup and alternatives."
proposed_change: |
  Title: "BBPOS WisePad 3 Review 2026: UK Price, Fees and Verdict"
  Description: "BBPOS WisePad 3 is Stripe's Bluetooth card reader for UK merchants (£59 ex VAT). MerchantHQ review: connection range, battery life, acquirer setup, Stripe Terminal fees and 3 closest alternatives."
why: |
  "bbpos wisepad 3" gets 189 impressions at position 13.4 with only 1 click (CTR 0.53%).
  The review already ranks but the CTR is low. Adding "Review" to the title signals that this
  is a dedicated review page (not a vendor product page), which typically pulls higher CTR for
  brand-model queries. The description adds "ex VAT" (UK buyers expect this), specifies
  "Stripe Terminal fees" (a key worry for the audience), and gives a concrete "3 closest
  alternatives" count to signal the page's depth. Apply by updating the reviewMeta field for
  the bbpos-wisepad-3 entry in src/data/terminals.ts. The title change requires adding a
  titleOverride field to the Terminal type and using it in the [slug].astro title computation.
---
