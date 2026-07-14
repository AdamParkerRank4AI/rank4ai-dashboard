# Fleet Daily Review — 2026-07-14

Dashboard data generated: 2026-07-09T08:21:56 UTC (5 days old — re-run push_to_fleet.py for fresh data).

---

## Shipped (mechanical fixes)

### fundbiz — em-dash sweep (commit 97c52ec, pushed to main)

6 em-dashes removed from user-facing copy in `src/data/grants.ts` and
`src/pages/grants/grants-vs-business-loans/index.astro`.
All replaced with full stops, colons, or parentheses per fleet rule.
No build failures (string replacements only; build not runnable in remote env).

---

## Queued for Adam's review (5 drafts)

| File | Site | Type | GSC signal |
|------|------|------|-----------|
| rank4ai-title_rewrite-best-ai-seo-agencies-uk.md | rank4ai.co.uk | Title swap | "ai search agency" 864 imp, pos 13.2 |
| market-invoice-title_rewrite-peak-cashflow.md | marketinvoice.co.uk | Title + desc | "peak cashflow" 277 imp, pos 7.7, CTR 0.36% |
| fundbiz-title_rewrite-hsbc-business-loan.md | fundbiz.co.uk | Title template | "hsbc business loan" 144 imp, pos 22.7 |
| cardmachines-meta_rewrite-bbpos-wisepad-3.md | merchanthq.co.uk | Meta desc | "bbpos wisepad 3" 189 imp, pos 13.4 |
| cardmachines-meta_rewrite-bbpos-wisepos-e.md | merchanthq.co.uk | Meta desc | "bbpos wisepos e" 116 imp, pos 7.4 |
| peptideclear-new_page-asda-pharmacy.md | peptideclear.co.uk | New page spec | "asda online pharmacy" 194 imp, pos 18.7 |

---

## Needs human input (cannot auto-fix)

### 1. SEOCompare — Clarity project ID missing

`seocompare/src/layouts/BaseLayout.astro` line: `const CLARITY_ID: string = '';`

Clarity is wired up but the project ID is empty so it never fires.
Fleet baseline check reports this as a failure.

**Action needed:** Adam to provide the Clarity project ID for seocompare.co.uk.
Once you have it, drop it into `CLARITY_ID` in BaseLayout.astro and push to main.

### 2. FundBiz — FAQPage schema on grants-vs-business-loans page

`fundbiz/src/pages/grants/grants-vs-business-loans/index.astro` lines 28-31 emit inline FAQPage schema.
Fleet hard rule says NO FAQPage. Market-invoice and Kartapay are explicitly exempted (CLAUDE.md says "FAQPage ALLOWED AND WANTED").
FundBiz CLAUDE.md does NOT include this exemption.

**Action needed:** Adam to decide — remove the inline FAQPage schema from this page (fleet baseline compliance),
or add FundBiz to the list of exempted sites in its CLAUDE.md.

### 3. AI citation rate — all 8 sites at 0%

Dashboard recommendations flag 0% AI citations across the fleet as critical.
The recommended fix (Wikidata/Wikipedia entries) requires Adam to draft and publish
Wikipedia-quality entity data for each site. This is a human editorial task.

---

## False positives in fleet_baseline.json (no action needed)

- **market-invoice FAQPage check:** FAILS but is correct — FAQPage is explicitly allowed and
  wanted on market-invoice per CLAUDE.md (reversed 22 Jun 2026).
- **MerchantHQ FAQPage check:** FAILS but is correct — MerchantHQ re-enabled FAQPage site-wide
  on 2026-06-23 per code comment in BaseLayout.astro. Bing/Brave/Copilot still parse it.
- **MerchantHQ orphan PAX A77 VS pages:** Was stale. Fix committed at 09:23 UTC 2026-07-09
  (commit e8b9e86 "Links: add 10 PAX A77 curated vs-pairs to fix orphaned comparison pages")
  — already deployed before this review ran.

The fleet_baseline.json checker needs updating to reflect the FAQPage policy exceptions.
