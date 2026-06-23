# Content note: /reviews/bbpos-wisepad-3/ — merchanthq.co.uk

**Type:** content-check (page exists but low ranking)
**Site:** cardmachines (MerchantHQ)
**Priority:** medium
**Query:** "bbpos wisepad 3" — 75 impressions, pos 21.4, 0% CTR
**Source page:** src/data/terminals.ts (slug: bbpos-wisepad-3) → /reviews/bbpos-wisepad-3/

## Current state
The page auto-generates from terminals.ts. The terminal entry exists:
- slug: bbpos-wisepad-3
- name: BBPOS WisePad 3
- manufacturer: BBPOS (white-labelled by Stripe and other Stripe Terminal SDK partners)

Page title auto-generates as: "BBPOS WisePad 3: UK rates, fees and verdict 2026"

## Problem
Pos 21.4 with 75 impressions and 0% CTR. The terminal page exists and ranks but is on page 2-3. Users searching "bbpos wisepad 3" are typically developers or merchants integrating Stripe Terminal who want technical specs + UK availability info.

## Recommendations

**Content depth improvements to terminals.ts entry for bbpos-wisepad-3:**

1. **Answer-capsule** (first paragraph, 40-80 words): "BBPOS WisePad 3 is the Bluetooth card reader behind Stripe Terminal in the UK. It accepts contactless, chip and PIN. It pairs with an iOS, Android or PC app running the Stripe Terminal SDK. Price: typically £59 to £79 direct from Stripe or authorised resellers. It is not a standalone POS. It needs a host device. Setup takes under 10 minutes via the Stripe Terminal dashboard."

2. **Technical spec table** (add to terminals.ts if structure supports it, or add a `techSpecs` field):
   - Connection: Bluetooth 5.0
   - Battery: 8-hour operational life
   - Card types: Visa, Mastercard, Amex, Maestro; contactless + chip + PIN
   - SDK: Stripe Terminal SDK (iOS, Android, Web, React Native, server-driven)
   - Certifications: PCI PTS 5.x, EMVCo Level 2

3. **Who it suits** callout: "WisePad 3 suits SaaS platforms, ISVs and developers who need card payments inside a custom application. Not suitable for merchants who want a standalone solution with no SDK integration."

4. **Internal links**: Add cross-link from Stripe review page (/reviews/stripe/) to the WisePad 3 review. Add from /guides/how-to-choose-card-terminal/ if Stripe Terminal is mentioned there.

## Rationale
The query is high-commercial-intent (product research). If the page content matches what this audience needs (technical specs + UK pricing + who it's for), ranking should improve. The current auto-generated content may be too thin for this specific hardware query.
