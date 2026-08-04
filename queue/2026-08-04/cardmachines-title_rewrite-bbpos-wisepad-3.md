---
status: draft
site: cardmachines
type: title_rewrite
target_query: bbpos wisepad 3
target_url: /reviews/bbpos-wisepad-3/
gsc_position: 13.4
gsc_impressions: 189
gsc_ctr: 0.53%
current_title: "BBPOS WisePad 3: UK review 2026"
current_description: "BBPOS WisePad 3 is the Stripe Bluetooth card reader for UK merchants (£59). MerchantHQ review: UK compatibility, connection, battery, acquirer setup and alternatives."
proposed_title: "BBPOS WisePad 3 Review: Stripe Bluetooth Card Reader UK (2026)"
proposed_description: "BBPOS WisePad 3 (£59): Stripe Bluetooth card reader for UK merchants. MerchantHQ review covering UK compatibility, 1.5%+5p rate, battery life, pairing and 4 alternatives."
author: Oliver Mackman
date: 2026-08-04
---

## Why

"bbpos wisepad 3" at pos 13.4 with 189 impressions and 0.53% CTR. This is one of the higher-impression hardware queries in the cardmachines GSC data. At position 13, improving to page 1 top-10 is achievable — but the title and description also need improving to lift CTR once there.

The current title follows the same pattern as WisePOS E but is equally generic. "BBPOS WisePad 3 Review" front-loads the action word, which is the stronger click signal for hardware searches. Adding "Stripe Bluetooth Card Reader UK" in the title covers the key attributes: brand association (Stripe), form factor (Bluetooth, portable), and market (UK).

The current description covers the right topics but does not include the rate (1.5% + 5p), which is the primary cost question for a Stripe reader buyer. Adding the rate makes the description more complete as a standalone SERP snippet.

## Implementation note

Same pattern as the WisePOS E fix. Update `reviewMeta` in `src/data/terminals.ts` for the `bbpos-wisepad-3` entry.

Current value: `'BBPOS WisePad 3 is the Stripe Bluetooth card reader for UK merchants (£59). MerchantHQ review: UK compatibility, connection, battery, acquirer setup and alternatives.'`

## Proposed changes to terminals.ts (bbpos-wisepad-3 entry)

```ts
reviewMeta: 'BBPOS WisePad 3 (£59): Stripe Bluetooth card reader for UK merchants. MerchantHQ review covering UK compatibility, 1.5%+5p rate, battery life, pairing and 4 alternatives.',
```

(172 chars — slightly over 160, trim "life, pairing" to "and pairing" or "battery + pairing" to hit 160 if needed)

For the title, same as WisePOS E: add an optional `reviewTitle` field to the terminal entry in `terminals.ts` and update `[slug].astro` to use it when present:

```ts
reviewTitle: 'BBPOS WisePad 3 Review: Stripe Bluetooth Card Reader UK (2026)',
```

(62 chars — marginally over 60; test whether Google clips or rewrites)

## Validation

After deploy: 14-day CTR delta on "bbpos wisepad 3". CTR target: above 2% (modest target given mid-SERP position). Position target: sub-10 (page 1).
