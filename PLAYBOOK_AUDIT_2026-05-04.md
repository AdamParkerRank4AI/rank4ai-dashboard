# Fleet playbook compliance audit · 2026-05-04

Audited all 3 owned sites against the BUILD-FAST-RANK-FAST playbook (Adam's distilled v4.0). Per-site results below; consolidated P1 list at the end.

Run by 3 parallel Explore agents. Pure findings — no fixes applied.

---

## R4 (rank4ai.co.uk)

**Compliance: ~92% pass.**

### What's correct
- robots.txt allows all 7 named AI crawlers
- llms.txt + llms-full.txt both present and well-structured
- Schema @graph fully linked (Person + Organization + WebSite + BreadcrumbList + FAQPage + Article)
- 3 founder Person entries in @graph (Adam, Jimmy, Oliver — Jimmy + Oliver added today)
- Homepage hero opens with "Rank4AI is a UK AI search agency that helps businesses..." (today's fix)
- /about/, /uk/, top blog/research pages all entity-function led
- Editorial policy live
- /uk/ Mapbox hub built today, linked from Header
- /research/uk-ai-search-visibility-market-report-q2-2026/ flagship LLM citation anchor exists
- 2,000-4,000 AI bot crawls/day (PerplexityBot + Claude-SearchBot strong)
- FCP 2.7s, LCP 2.9s

### Top 3 P1 gaps
1. **Jimmy + Oliver Person schema lacks `sameAs`** — Adam has LinkedIn + X. Jimmy and Oliver have `worksFor` + `knowsAbout` but no profile corroboration. Get their LinkedIn URLs and 5-min fix to Layout.astro.
2. **Adam dominates author rotation: 57% of 126 auto-published posts** — Jimmy 11, Oliver 12, Rachel 13, Team 18. Playbook says rotate evenly across 3 founders. Auto-publisher needs reweighting.
3. **Brand description drift across touchpoints** — homepage says "helps businesses get recommended", about says "specialist agency", llms.txt says "focused on improving visibility". Pick ONE canonical sentence and unify across home / about / footer / llms.txt / Organization schema description.

---

## MI (marketinvoice.co.uk)

**Compliance: ~88% pass.**

### What's correct
- robots.txt + llms.txt + llms-full.txt + IndexNow + Bing all wired
- Schema @graph with Organization + Person + WebSite + BreadcrumbList + FAQPage + Article all linked via @id
- disambiguatingDescription handles Kriya/MarketInvoice historical confusion
- Today's hero promotion of entity-function paragraph live
- /about/#disambiguation full section live
- /best/, /providers/, /industries/ all answer-capsule led
- Author = Oliver Mackman, no Adam bylines anywhere in dist/
- 5 differentiated bespoke city pages (London, Manchester, Birmingham, Leeds, Bristol)
- Mapbox now embedded on /providers/ + /industries/ (today)
- 14-day AI bot mix: Bingbot 1428, ChatGPT-User 1122, Applebot 967, PerplexityBot 680
- Speed: homepage FCP 2.6s LCP 2.6s

### Top 3 P1 gaps
1. **Lead drought is a traffic problem, not a UX problem.** Last form_submit 24 Apr. 0% Google visibility for 10 tracked queries. Today's `/best/` strengthening is one of 8 needed pages. Remaining 7 are queued in `NEXT_ACTIONS.md` as MI-1.
2. **Companies House officer URL on Oliver Mackman returns 404** — `find-and-update.company-information.service.gov.uk/officers/dKHZEH-n1H5BVmR2rILJcCJbzY4/appointments`. Either the officer ID changed or the URL pattern is wrong. Get the live URL from Companies House and update `site.manifest.ts` line 28.
3. **~150 `/questions/*` pages still scoring 23/100 on find-thin.cjs** — the QA template enrichment from 24 Apr only covers new pages. Need the bulk re-enrichment script (MI-3 in NEXT_ACTIONS).

(Note: agent flagged "only 7 /locations/* pages" as P1 — that's wrong. The dynamic `[city].astro` template generates 50 city pages from `uk-cities.json`. Only the 5 bespoke overrides are individual files. Fleet has all 50 live.)

---

## SC (seocompare.co.uk)

**Compliance: ~85% pass.**

### What's correct
- robots.txt allows all named AI crawlers
- llms.txt + llms-full.txt scoring 80/100 and 70/100 respectively (validator now in place via Batch 9)
- BaseLayout @graph with Person (Oliver Mackman) + Organization (SEOCompare / Aston Rowe Ltd) + WebSite linked
- agencies.json single source of truth exists (252 lines, 115+ agencies)
- /compare/[pair].astro alphabetises slugs (today's fix)
- Today's hero fix: "SEOCompare is the UK's independent comparison..." now visible above-fold (was schema-only before)
- Mapbox via WorldClocks.astro
- Author = Oliver Mackman everywhere, zero Adam bylines in dist/
- "Independent comparison · commercial relationships disclosed" boilerplate present
- /editorial-policy/ live
- /ai-citation-gaps/ exists (NEXT_ACTIONS SC-2 complete — agent confirmed)

### Top 3 P1 gaps
1. **YouTube `sameAs` returns 404** — `youtube.com/@seocompare` channel never created. Either create the channel (15 min) or remove the line from `site.manifest.ts:29`. Today's entity coherence checker found this; it'll keep flagging until fixed.
2. **Speed: FCP 2.6s, performance score 75/100** — below the 79 fleet baseline. Investigate image optimisation, CSS delivery, script-loading bottlenecks on mobile.
3. **City pages: 31, not the 50+ implied by content map** — current coverage stops at major UK cities. Adding 19 more (Swindon, York, Doncaster, etc.) would expand long-tail capture.

---

## Cross-fleet P1 rollup

Items affecting all 3 sites (highest leverage):

1. **Wikidata + Wikipedia stubs** — flagged by all 3 fleet research agents (26 Apr) AND surfaces in this audit as the missing entity layer. Adam declined this session, but the playbook ranks it as the #1 entity-corroboration unblocker. **No fix without your authoring time.**

2. **GSC service account on MI + SC** — 130 daily Indexing API submissions failing 403. Steps were given earlier this session. **No fix without your action.**

3. **Brand description harmonisation** — currently each site has a canonical sentence in different places that are 95% the same but not identical. Pick the canonical wording per site and audit-replace across home / about / footer / llms.txt / Organization schema description so AI sees one answer to "what is X" rather than three near-variants.

---

## Items already on the queue (don't double-up)

These appear in `NEXT_ACTIONS.md` already; don't re-flag them:
- R4-1 sameAs for Jimmy + Oliver (matches R4 P1 #1)
- R4-3 narrative arc port (touches on brand description harmonisation)
- MI-1 8 dedicated landing pages for zero-visibility queries (matches MI P1 #1)
- MI-3 bulk thin-page re-enrichment (matches MI P1 #3)
- SC-3 agency matcher refactor (partially done per audit)

---

## Items NOT on the queue, surfaced today

- R4-4 (new) — author rotation rebalancing: tweak auto-publisher to round-robin Adam → Jimmy → Oliver instead of Adam-weighted
- MI-4 (new) — fix Oliver's Companies House officer URL
- SC-4 (new) — create `youtube.com/@seocompare` channel OR remove the line from sameAs
- Fleet-1 (new) — pick one canonical brand sentence per site and audit-replace across all touchpoints

I've appended these to `NEXT_ACTIONS.md`.
