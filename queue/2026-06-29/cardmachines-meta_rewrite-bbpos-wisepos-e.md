---
status: draft
site: cardmachines
type: meta_rewrite
target_query: bbpos wisepos e
target_url: /reviews/bbpos-wisepos-e/
current_state: |
  Title (auto-generated): "BBPOS WisePOS E: UK rates, fees and verdict 2026"
  Meta (auto-generated from terminal.summary):
  "BBPOS WisePOS E is the hardware behind Stripe Terminal and many white-label
  acquirer terminals. Solid Android-based platform, customisable via the acquirer's
  SDK. Best when you need card payments inside an existing software stack rather
  than as a standalone POS."
  Meta char count: ~231 — severely truncates in SERPs.
  Position: 7.0, impressions: 64, clicks: 0, CTR: 0%
proposed_change: |
  Title (no change — 49 chars, well-optimised):
  "BBPOS WisePOS E: UK rates, fees and verdict 2026"

  Meta (new — 153 chars):
  "BBPOS WisePOS E review: the Android smart terminal behind Stripe Terminal. UK pricing, SDK integration, hidden fees, and the best alternatives compared."

  Implementation: follow the same pattern as the wisepad-3 draft from 2026-06-27.
  In src/data/terminals.ts, add an `overrideMeta` field to the BBPOS WisePOS E entry:
    overrideMeta: "BBPOS WisePOS E review: the Android smart terminal behind Stripe Terminal. UK pricing, SDK integration, hidden fees, and the best alternatives compared.",
  Then in src/pages/reviews/[slug].astro, use:
    const description = terminal.overrideMeta
      ?? `Hands-on ${terminal.name} review by MerchantHQ. ${terminal.summary.slice(0,155)}`;
  (This is the same template change already proposed in the wisepad-3 draft —
  implement both at once to avoid two separate deploys.)
why: |
  "bbpos wisepos e" gets 64 impressions at position 7.0 with 0 clicks — a perfect
  CTR fix candidate. Being on page 1 at pos 7 with 0% CTR means the title and meta
  are failing to communicate relevance to someone researching Stripe Terminal hardware.
  The current meta at ~231 chars truncates well before reaching the key buying signal
  (Stripe Terminal + SDK integration). The proposed 153-char meta leads with the
  Stripe connection, calls out SDK integration (the differentiator vs. standalone
  terminals), and ends on "alternatives compared" — matching the research intent.
  Combine this with the wisepad-3 fix for a single terminals.ts + [slug].astro
  edit that covers both quick-wins in one commit.
---
