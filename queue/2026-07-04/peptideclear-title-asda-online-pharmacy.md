# peptideclear — Title/Meta Rewrite: /pharmacies + /pharmacies/asda-online-doctor

**Date queued:** 2026-07-04
**Type:** title-meta + possible new page
**Priority:** high (pos 18.0, 111 impr, 0% CTR — 3 "asda" queries in top-5 content gaps)
**URL:** https://www.peptideclear.co.uk/pharmacies/
**Source file:** ukmetabolic/src/pages/pharmacies/index.astro

## Why

"asda online pharmacy" gets 111 impressions at position 18.0 with zero clicks. The broader /pharmacies/ comparison page ranks for this query but covers 5 pharmacies (Phlo, Pharmacy2U, Simply Meds, Boots Online Doctor, Asda Online Doctor). Someone searching "asda online pharmacy" wants Asda-specific information, not a multi-provider hub.

Also flagged: "asda online doctor" (pos 25, 95 impr, 0% CTR), "asda doctors online" (pos 37.9, 57 impr), "asda doctor" (pos 34.7, 55 impr) — all pointing at the same Asda gap.

## Current

```javascript
const title = 'UK online pharmacies for GLP-1 medication: comparison 2026';
const description = 'Ranked comparison of UK online pharmacies dispensing GLP-1 medication. Phlo, Pharmacy2U, Simply Meds, Boots Online Doctor, Asda Online Doctor. GPhC registered.';
```

Title: 59 chars — no "Asda" in title, so Asda-searchers get no signal.
Description: 161 chars — Asda is listed but buried at the end.

## Option A: Add "Asda" to /pharmacies/ title (quick, 10 mins)

```javascript
const title = 'UK GLP-1 Online Pharmacies 2026: Asda, Boots, Phlo & More';
const description = 'Independent comparison of UK online pharmacies for GLP-1 medication. Includes Asda Online Doctor, Boots Online Doctor, Phlo, Pharmacy2U and Simply Meds. GPhC registered. Updated 2026.';
```
(58 chars / 183 chars)

Advantage: one edit, immediate. Disadvantage: the page still doesn't give Asda-first searchers what they want.

## Option B: Build /pharmacies/asda-online-doctor/ (stronger, 2-3 hours)

Dedicated page in the existing pharmacies/ pattern (Boots and SimplyMeds already have sub-pages at `/pharmacies/boots/` and `/pharmacies/simplymeds/`). Would target:
- "asda online pharmacy" (111 impr, pos 18)
- "asda online doctor" (95 impr, pos 25)
- "asda doctors online" (57 impr, pos 37.9)
- "asda doctor" (55 impr, pos 34.7)

Total addressable: ~318 impressions from 4 queries, currently 0 clicks.

Page spec:
- Title: "Asda Online Doctor Review 2026: GLP-1 Medication UK"
- Description: "Independent review of Asda Online Doctor for GLP-1 weight-management medication. GPhC registered. Ozempic, Wegovy, Mounjaro dispensed. From £149/mo. UK-wide delivery."
- Content: editorial review, no clinical advice, CTA to Asda Online Doctor
- Author: Oliver Mackman
- Schema: Article + Speakable (NO FAQPage — check peptideclear CLAUDE.md before adding)
- Hard rules: no em dashes, no branded weight-loss pill comparison framing, no clinical advice

## Recommendation

Ship Option A immediately (one edit, zero risk). Queue Option B as a content piece for the next editorial session — it closes 4 queries at once and slots into the existing pharmacies/ pattern which already has sub-pages.

## Effort

Option A: 1 edit, 5 mins. Ship to main today.
Option B: new page, ~2 hours. YMYL adjacent — review before shipping.
