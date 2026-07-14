# Title/Meta Rewrite: fundbiz /banks/hsbc/

**Site:** fundbiz.co.uk
**File:** `fundbiz/src/pages/banks/[slug].astro` (template, affects all bank pages)
**Type:** title template pattern change — OR — data-level override for HSBC entry in `banks.ts`
**GSC signal:** "hsbc business loan" 144 imp, pos 22.7 | "365 business finance" 150 imp, pos 19.1

## Current template

```ts
const title = `${bank.bankName}: when declined`;
// HSBC generates: "HSBC UK business loan: when declined"
```

## Problem

"hsbc business loan" query at pos 22.7 (page 3) with 144 impressions. The title "HSBC UK business loan: when declined" leads with "HSBC UK business loan" which matches the query well. However, "when declined" signals a very specific use case and may be suppressing impressions for users who are simply researching HSBC business loans generally.

The page is getting impressions for "hsbc business loan" but ranking very deep because the content is decline-focused, not general-information-focused. This is correct for fundbiz's positioning (post-decline specialty), but the title optimisation below would help for users already in the decline pathway.

## Option A: Data-level title override (recommended, minimal risk)

Add a `titleOverride` field to the `BankPage` interface and update the HSBC entry in `banks.ts`:

```ts
// In BankPage interface:
titleOverride?: string;

// In HSBC entry in banks.ts:
titleOverride: 'HSBC business loan declined? What to do next',
```

Update template to use: `const title = bank.titleOverride ?? \`${bank.bankName}: when declined\`;`

This targets the "hsbc business loan declined" adjacent query cluster without changing the template for all 13 banks.

## Option B: Change template pattern

```ts
const title = `${bank.bankName} declined: alternatives and next steps`;
// HSBC: "HSBC UK business loan declined: alternatives and next steps"
```

This would help all bank pages rank for "[bank] business loan declined" and "[bank] declined alternatives" but removes the clean `: when declined` pattern.

## 365 Business Finance (secondary opportunity)

"365 business finance" at 150 imp, pos 19.1 — check whether fundbiz has a `/banks/365-business-finance/` or `/providers/365-business-finance/` page. If not, consider adding a provider card to the banks data or a standalone page.

If the query is being picked up by the homepage or a generic page, adding a dedicated page for 365 Business Finance would be the move (they are a prominent UK alternative lender for declined cases — directly in fundbiz's wheelhouse).

## Action (Option A, HSBC)

1. Add `titleOverride?: string;` to `BankPage` interface in `fundbiz/src/data/banks.ts`
2. Add `titleOverride: 'HSBC business loan declined? What to do next',` to the HSBC entry
3. Update `[slug].astro` line 16 to use: `const title = bank.titleOverride ?? \`${bank.bankName}: when declined\`;`
4. Push to main.

Adam: please confirm Option A vs B before implementing template change.
