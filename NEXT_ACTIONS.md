# NEXT ACTIONS — Fleet (R4 / MI / SC)

Last updated: 2026-05-04 from session today.

This file is the queue. Each item is a copy-ready Claude prompt — open the relevant site's `rc` session (or terminal in `~/rank4ai-site` / `~/compare-invoice-finance` / `~/compareaiseo`), paste the prompt, ship.

---

## R4 (rank4ai.co.uk)

### R4-1 · Add `sameAs` arrays to 3 founder Person schemas — XS, ~10 min

**Why:** Person schemas for Adam / Jimmy / Oliver have no `sameAs` corroboration. AI platforms cross-reference Person entities via LinkedIn, X, personal sites. Current Person schema has Adam's `sameAs` (LinkedIn + X) but Jimmy and Oliver are missing entirely from the global schema. Authoring quality + E-E-A-T signal.

**Prompt to paste:**
```
Read ~/rank4ai-site/src/layouts/Layout.astro. The global @graph schema has a Person entry for Adam Parker with sameAs (LinkedIn + X). Add two more Person entries to the @graph for Jimmy Connoley and Oliver Mackman, each with:
- @id with #jimmy-connoley / #oliver-mackman
- worksFor pointing at #localbusiness
- jobTitle (Co-Founder for Jimmy, Operations and Marketing Director for Oliver — match what's on /about/)
- knowsAbout (4-5 relevant terms each)
- sameAs (LinkedIn + X if known — if you can't find a verified URL, leave the field absent rather than guessing)

Then verify the /about/ page Team section uses matching @id refs where Person schema is inline, and add Author bylines on blog/Q&A pages that link to the global Person entity. Build, commit, ask before pushing to main.
```

---

### R4-2 · First client case study with before/after metrics — S, 30-60 min

**Why:** R4 has zero social proof pages. Daily brief flags "Low AI citation rate (4.3%)" and "0% Google visibility on 8 target queries" — case studies are how AI builds confidence in recommending an agency. Pick a real client (RB Financial / Blackthorne / Jolt) where audit data exists.

**Prompt to paste:**
```
Build a client case study at /research/case-studies/<slug>/. Pick the client with the most measurable AI visibility lift (RB Financial, Blackthorne, or Jolt). Required sections:
- H1: client name + one-line outcome
- First paragraph: "Rank4AI worked with [client], a [sector] [scale] business based in [location], to [outcome]." (entity-function pattern, full names, no anaphora)
- Audit baseline (date + score + per-platform visibility)
- What we changed (4-6 bullets, specific actions)
- After (date + score + per-platform visibility, with delta)
- Quote from client if available, else attributed paraphrase
- Article schema + Speakable + Person byline
Add to /research/case-studies/index.astro grid. Build, commit, ask before pushing.
```

---

### R4-3 · Port narrative arc to MI + SC home pages — S, 1h cross-site

**Why:** R4's home page now has Problem → Solution → Proof → CTA structure (entity statement, signals, stats, social proof). MI and SC have similar bones but the arc is broken up. This is the next iteration of today's entity-function fix.

**Prompt to paste:**
```
On MI homepage (~/compare-invoice-finance/src/pages/index.astro), tighten the hero into 4 explicit blocks: Problem (one sentence on cashflow gap), Solution (Market Invoice entity statement — already there), Proof (the answer capsule with best providers + 3 stats strip already on page), CTA (Get 3 Free Quotes). Move existing content into this order without losing schema.

Repeat on SC homepage (~/compareaiseo/src/pages/index.astro): Problem (one sentence on agencies adding "AI SEO" without expertise), Solution (SEOCompare entity statement — already there), Proof (115+ agencies + 12 criteria + monthly updates strip — already there), CTA (browse agency directory).

Build both. Commit per site with separate messages. Ask before pushing to main.
```

---

## MI (marketinvoice.co.uk) — lead drought is a traffic problem, fix the traffic

### MI-1 · 8 dedicated landing pages for tracked-but-zero-visibility queries — M, 4-6h (do over a week)

**Why:** Dashboard daily brief: 0% visibility for 10 tracked invoice-finance queries. Top 3 SERP for those queries owned by capitalise / bibby / fundinvoice / smeinvoicefinance / hydr. Without dedicated landing pages, MI has no chance of ranking for them. This is the load-bearing fix for the lead drought (last form_submit was 24 Apr).

**Target queries (from dashboard `serp_data.json`):** invoice finance UK, best invoice factoring companies UK, compare invoice finance providers UK, how does invoice finance work, invoice finance for small business UK, confidential invoice discounting UK, invoice finance costs UK, selective invoice finance UK.

**Prompt to paste (one query at a time):**
```
Build a dedicated landing page on ~/compare-invoice-finance for the query "invoice finance UK" (or whichever query I'm assigning).

Slug: /best-invoice-finance-uk/ (or canonical equivalent that matches the query intent).
Required: 1,500+ words, FAQPage schema (8 questions), Article schema, Speakable, comparison table (top 10 providers with rate / advance / setup days), 3 use-case mini-sections, named-author byline (Oliver Mackman). Lead paragraph must be entity-function: "Market Invoice is the UK's independent invoice finance comparison... [what this page covers in plain prose]."
Pull provider data from ~/compare-invoice-finance/src/pages/providers/index.astro (already has rates/setup days). FAQ pull from existing /questions/* if relevant.
Internal links: 2 to /providers/, 1 to /calculator/, 1 to relevant industry, 1 to /why-use-a-broker/.
Build, commit, ask dev or main before push.
```

Track which 8 are shipped in INBOX so we don't double-up.

---

### MI-2 · Sector expansion 28 → 35 — M, ~3h

**Why:** Sector pages are MI's strongest long-tail. The 28→35 plan was in the 26 Apr 30-day brief but nothing's been built since. Each new sector = new long-tail entry point.

**Prompt to paste:**
```
Add 7 new sector guides on ~/compare-invoice-finance under /industries/<slug>/. Sectors to add: agriculture, marketing-agencies, scaffolding-hire, asbestos-removal, scaffolding-erection, signage, equipment-hire. Use the existing /industries/[city].astro template style. Each page:
- Entity-function lead paragraph using the full sector name
- Sector-specific stats (lending volume, typical advance, common provider specialisms)
- 3-4 named-provider recommendations with reasoning
- 5 sector-specific FAQs with FAQPage schema
- Article schema + Speakable + Oliver Mackman author byline
Add the 7 new sectors to /industries/index.astro grid. Build, commit, ask before push.
```

---

### MI-3 · Bulk re-enrich the ~150 thin /questions/* pages — S, ~1h script run

**Why:** Last find-thin showed ~150 question pages still scoring 23/100. The 24 Apr enrichment made it through QA template + auto-publisher but didn't backfill existing pages.

**Prompt to paste:**
```
On ~/compare-invoice-finance, write a script (or extend an existing one) that takes each existing /questions/<slug>.astro page scoring under 50 on find-thin.cjs and adds: a What-this-means expansion (3-5 sentences), Key Points (5 bullets), Common Pitfalls (3 bullets), 3 Related FAQs with FAQPage schema, Speakable. Use Claude API (anthropic SDK already in ~/run_blogs.py for reference). Skip pages already enriched (check for "Key Points" string). Run on top 50 thinnest first, review output quality, then run on the rest.
```

---

## SC (seocompare.co.uk)

### SC-1 · Fix ~10 broken `/compare/<X>-vs-<Y>/` paths from `/alternatives/` pages — XS, ~30 min

**Why:** Today's audit surfaced these. The `/alternatives/<agency>/` pages link to comparison pages that don't exist (e.g. `/compare/seo-works-vs-clickslice/`, `/compare/targeted-seo-vs-carrieann-sudlow/`). Either build the comparison pages or strip the broken links. Strip is faster.

**Prompt to paste:**
```
On ~/compareaiseo, run `node scripts/find-broken.cjs` to list all broken targets cited from /alternatives/<agency>/ pages. For each /alternatives/* template that links to a non-existent /compare/<X>-vs-<Y>/, either:
(a) remove the broken link if there are 5+ working links remaining, or
(b) point it at /compare/ root if the page is a 1-of-2 with a working alternative.
Do NOT fabricate comparison pages. Build, verify zero broken links, commit, ask before push.
```

---

### SC-2 · `/ai-citation-gaps/` page targeting 8 missed query types — M, 1-2h

**Why:** TASKS #109 (P1). 8 query types where SC's competitors get cited and SC doesn't. This is the SC equivalent of MI-1.

**Prompt to paste:**
```
Build /ai-citation-gaps/ on ~/compareaiseo. Lead paragraph: SEOCompare entity statement, then "this page answers the AI search prompts SEOCompare is currently absent from in 2026."
For each of these 8 query types, build a section: "best AI search agencies UK", "compare AI SEO agencies UK", "what is GEO 2026", "how to choose AI search agency", "alternatives to <competitor>", "AI SEO agency vs traditional SEO", "ChatGPT optimisation cost UK", "AI Overviews ranking factors". Each section: answer-capsule paragraph, comparison table where applicable, FAQPage schema entry.
Article schema + Speakable + Oliver Mackman author byline. Build, commit, ask dev or main before push.
```

---

### SC-3 · `agencies.json` single source-of-truth — M, 1-2h

**Why:** TASKS #108 (P1). Currently agency data is scattered. Building agencies.json with schema-per-agency unblocks the matcher scaling from 14 → 115+.

**Prompt to paste:**
```
On ~/compareaiseo, build src/data/agencies.json. Each entry: id, name, hq, founded, services[], platforms[], pricing_tier, industries[], distinct_claims[], url, last_reviewed_iso. Source the 115+ agencies from iCloud/claude/astro/rank4ai/AGENCY_DATABASE.md (single canonical list).
Then refactor /agency-matcher/ and /find-an-agency/ to read from agencies.json instead of hardcoded arrays. Verify the existing 14 agency cards still render. Build, commit, ask before push.
```

---

## Fleet (cross-site)

### F-1 · Wikidata + Wikipedia stubs — BLOCKED on Adam authorship

3 of 4 fleet research agents independently flagged this as the #1 entity unblocker. ~10 min per site. Adam declined this session — surface again next week.

### F-2 · GSC service account on MI + SC — BLOCKED on Adam

Add `indexing@inbound-dahlia-491120-v6.iam.gserviceaccount.com` as Owner in GSC for marketinvoice.co.uk + seocompare.co.uk. Unlocks 130 daily Indexing API submissions currently failing 403.

---

## Surfaced from 4 May playbook compliance audit

### R4-4 · Rebalance author rotation in auto-publisher — XS, ~15 min

**Why:** Audit found Adam = 57% of 126 auto-published posts (Jimmy 11, Oliver 12, Rachel 13, Team 18). Playbook expects even rotation across 3 founders for E-E-A-T balance.

**Prompt to paste:**
```
On ~/run_blogs.py and ~/run_questions.py (R4 auto-publishers), the author selection is weighted toward Adam Parker. Change to strict round-robin Adam → Jimmy → Oliver based on a counter file at ~/.rank4ai_author_counter (or modulo of post count). Skip Rachel and Team entries entirely (they dilute the founder voice). Keep Person schema bylines pointing at the matching @id from R4 Layout.astro @graph.
```

### MI-4 · Fix Oliver's Companies House officer URL — XS, ~5 min

**Why:** Today's entity coherence run found `https://find-and-update.company-information.service.gov.uk/officers/dKHZEH-n1H5BVmR2rILJcCJbzY4/appointments` returns 404. The officer ID is wrong or the URL pattern changed.

**Prompt to paste:**
```
Open https://find-and-update.company-information.service.gov.uk/company/16833937/officers in a browser, click Oliver Mackman, copy the canonical officer URL. Update ~/compare-invoice-finance/src/site.manifest.ts (or the BaseLayout sameAs reference) with the correct URL. Build, commit, ask before push.
```

### SC-4 · Create or remove YouTube channel sameAs — XS, ~15 min

**Why:** `youtube.com/@seocompare` returns 404 (channel never created). Today's entity coherence checker keeps flagging this. Two options:
- (a) Create the channel under SEOCompare (15 min, also unlocks Batch 8 syndication tracking for video)
- (b) Remove the line from `site.manifest.ts` sameAs array (1 min)

If creating the channel, set the handle to `@seocompare`, link it to oliver@mackmangroup.co.uk, set the About to the canonical SEOCompare entity-function sentence.

### Fleet-1 · Harmonise brand descriptions across touchpoints — S, ~30 min per site

**Why:** Each site has near-identical canonical descriptions that drift slightly across home / about / footer / llms.txt / Organization schema. Today's R4 fix tightened the schema description but other touchpoints are still subtly different. AI uncertainty when descriptions vary.

**Prompt to paste (per site):**
```
On <site repo>, run `grep -rn "<short brand description fragment>"` to find all places the brand description appears (BaseLayout.astro / Layout.astro, footer, /about/ first paragraph, llms.txt blockquote line, public/llms-full.txt, site.manifest.ts if present). Pick ONE canonical sentence (use the homepage hero version as canon — that's what users see). Replace across all locations. Build, commit, ask before push.
```

---

## Adam-blocked items (do once Adam confirms)

- F-1 Wikidata stubs
- F-2 GSC service account
- BBL/FundBiz/CardMachines content (waiting on lender / panel / terminal lists)

---

## Already on the dashboard auto-queue (don't duplicate)

These appear in dashboard `recommendations.json` and per-site `DAILY_BRIEF.md`:
- Page-1 zero-click CTR fixes (auto-detected)
- Manual GSC indexing queue (top 10/site/day)
- Drift report (CLAUDE.md vs live DOM mismatches)
- Daily audit issues
- AI Search citation gaps (per-prompt-cluster)
