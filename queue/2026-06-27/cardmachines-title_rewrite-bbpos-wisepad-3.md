---
status: draft
site: cardmachines
type: title_rewrite
target_query: bbpos wisepad 3
target_url: /reviews/bbpos-wisepad-3/
current_state: |
  Title (auto-generated): "BBPOS WisePad 3: UK rates, fees and verdict 2026" (49 chars — fits)
  Meta (auto-generated): "Hands-on BBPOS WisePad 3 review by MerchantHQ. BBPOS WisePad 3 is the smaller
  mobile-first reader in the BBPOS family, white-labelled by Stripe and other Stripe
  Terminal SDK partners."
  Meta char count: ~184 — truncates in SERPs.
  Position: 17.2, impressions: 127, clicks: 0, CTR: 0%
proposed_change: |
  Title (no change — already 49 chars, well-optimised):
  "BBPOS WisePad 3: UK rates, fees and verdict 2026"
  
  Meta (new — 152 chars, fits without truncation):
  "BBPOS WisePad 3 review: Stripe Terminal's mobile card reader. UK pricing, hidden fees, when to choose it and the best alternatives. Free expert advice."
  
  Implementation: the meta is auto-generated in src/pages/reviews/[slug].astro (line 63)
  from the terminal summary. Add an optional `overrideMeta` field to terminals.ts and
  update the template:
    const description = terminal.overrideMeta 
      ?? `Hands-on ${terminal.name} review by MerchantHQ. ${terminal.summary.slice(0,155)}`;
  
  In terminals.ts for BBPOS WisePad 3, add:
    overrideMeta: 'BBPOS WisePad 3 review: Stripe Terminal\'s mobile card reader. UK pricing, hidden fees, when to choose it and the best alternatives. Free expert advice.',
why: |
  "bbpos wisepad 3" gets 127 impressions at position 17.2 with 0 clicks — this is
  a transactional research query from buyers comparing card reader hardware. The
  auto-generated meta at ~184 chars is truncated mid-sentence. The new meta:
  (1) fits in 152 chars, (2) names the Stripe Terminal link (key buying signal for
  this query), (3) calls out "UK pricing" + "hidden fees" which are the top comparison
  concerns, and (4) ends with the free advice CTA to drive conversion. The title is
  already well-structured and should not change. This is a quick single-field fix in
  terminals.ts with a low-risk template update.
---
