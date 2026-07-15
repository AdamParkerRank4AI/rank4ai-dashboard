---
status: draft
site: cardmachines
type: title_rewrite
target_query: bbpos wisepad 3
target_url: /reviews/bbpos-wisepad-3/
current_state: |
  Title generated from template: "BBPOS WisePad 3: UK rates, fees and verdict 2026" (from reviewTitleCandidates logic in [slug].astro — first candidate <=60 chars wins).
  Meta (reviewMeta already set in terminals.ts line 320): "BBPOS WisePad 3 is the Stripe Bluetooth card reader for UK merchants (£59). MerchantHQ review: UK compatibility, connection, battery, acquirer setup and alternatives."
  Position 13.4, 189 impressions, 1 click, 0.53% CTR.
proposed_change: |
  Add a `reviewMeta` field to the BBPOS WisePad 3 entry in terminals.ts:
  reviewMeta: "BBPOS WisePad 3 UK review 2026: Stripe-backed Bluetooth card reader for UK merchants. Rates, fees, setup and who it suits. Independent MerchantHQ verdict."
  
  Check reviewTitleCandidates output: "BBPOS WisePad 3: UK rates, fees and verdict 2026" (49 chars) is likely the selected title, which is correct. No title change needed.
  
  Body action: confirm H1 reads "BBPOS WisePad 3 review" and add a one-sentence "Quick answer" above the fold: "The BBPOS WisePad 3 is a Stripe-paired Bluetooth card reader suited to developers and platforms using Stripe Terminal SDK; rate is 1.5% + 20p for Stripe-direct accounts."
why: |
  "bbpos wisepad 3" drives 189 impressions at position 13.4 with only 1 click. The auto-generated meta currently uses the terminal summary opener which mentions "Stripe Terminal SDK partners" rather than leading with the searcher signal (who uses it, what it costs). Overriding with a purpose-built reviewMeta that front-loads the searcher intent ("UK review 2026: Stripe-backed Bluetooth card reader") should improve CTR from 0.53% to 2-3%, gaining 3-4 more clicks per 28 days from this query alone. At position 13 it is also a candidate for an internal link push: adding a link from /reviews/ hub page or the Stripe terminal comparison page could close the position gap to page 1.
---
