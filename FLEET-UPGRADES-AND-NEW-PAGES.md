# Fleet Upgrades & New Pages — status (updated 29 Jun 2026)
> Working copy in a writable path. The iCloud original (`iCloud/.../Research/beyond-serp-fleet-2026-06-17/`) is **dataless/evicted + needs Full Disk Access** for this process to write — that's the "lock" seen all session. Use this copy until FDA is granted.

## 🚨 Anti-slop SWEEP (29 Jun) — quality risk on MarketInvoice + MerchantHQ (CLEANUP IN PROGRESS)
> An anti-slop sweep of **1,359 existing LIVE pages** found **219 MAJOR issues**, clustered almost entirely on the **PROGRAMMATIC** pages: MarketInvoice `/vs/` and MerchantHQ `/best/by-trade-and-city/`, `/trade/`, `/vs/`. These are NOT 219 separate fixes · they trace to a handful of **template root causes**:
> - **(a) Fabricated ratings** — programmatic `4.x/5` and `5/5` provider ratings with **no methodology** = ASA/FCA + EEAT liability. Being **removed** (verify-first, no invented numbers).
> - **(b) Factual / category errors** — non-invoice-finance products (**iwoca, Funding Circle, Swoop, Capitalise, Allianz Trade**) compared as IF rivals; plus a repeated likely-**hallucinated** "**Bibby acquired Aldermore Working Capital Finance 2023**" claim, a Kriya/Allica date, Ultimate/Recognise, Skipton "mutual", Novuna · all verify-first before any copy change.
> - **(c) MHQ template bleed** — wrong-trade watch-outs (gold-jewellery warnings on **nail-salon / taxi** pages), a broken variable rendering "**Same as the underlying acquirer on a same as...**", and **leaked internal notes** in public copy.
> - **(d) Missing FCA referral-fee disclosure** on lead pages.
>
> **Status: CLEANUP IN PROGRESS this session** — ratings being removed, facts verified-first before edit. **FALSE POSITIVES to ignore:** the "future date 2026-xx" flags are wrong (today IS 29 Jun 2026) and the "Copy for AI" widget is likely intended, not slop.

## 🔄 29 Jun 2026 — this session's changes (banked tranche shipped + banner AdSense + full backup)
> Verified against `~/control-panel/FLEET_REALITY.md` (07:33, 17 sites; only intentional drift = LLB 401-locked + trustedinteriors CF AI-block) + CHANGELOG newest entries.
- **DEPLOYED LIVE (noindex unless noted):** **B34 Kartapay 6 guides** (⚠️ pages are INDEXABLE not noindex: flag to review) · **B35 VettedHome questions** (noindex, correct) · **MerchantHQ** last hard contrast fail fixed (fleet-core AIComprehension "Quick Reference" gray-400 2.49:1, overridden in site CSS) → gate **0 unreadable** live.
- **BANNER ADSENSE REMEDIATION SHIPPED LIVE (4 sites: HomesAndHedge, BabyData, FitCalcs, DatesAndTimes):** Adam-Parker named-editor `/authors/adam-parker/` pages (Person schema + ORCID), Privacy / Contact / Editorial-policy pages, footer legal nav, oliver→adam 301, fake "registered reviewer/midwife" claims stripped. Headshot + LinkedIn being wired in now (in progress). **PENDING ADAM: resubmit each to AdSense.** Caught + preserved a real factual line a prior commit had wrongly deleted (DatesAndTimes "World Cup bank holiday" Mon 15 Jun 2026 — verified real via gov.scot).
- **NEW BANKED CONTENT TRANCHE (built + committed + pushed to origin, noindex, NOT live):** B31 FundBiz 4 guides · B33 LTD Turnaround 4 insolvency Q-pages (HELD on named Licensed IP) · B36 BBL (other session; antislop flagged PERG-cite + BoE-base-rate fixes, not shipped) · B37 HomesAndHedge renter-disrepair · B38 HerVitals 7 Q + menopause hub + HRT tracker · B39 ADHD RTC/shared-care · B40 FitCalcs 6 guides · B41 DatesAndTimes 6 guides · B42 BabyData 7 guides · B43 TrustedInteriors 7 Q + site-index hub (HELD pre-launch). Health/legal ones need a Claude **finishing pass** (Adam-Parker named-editor + a date/figure re-verify) before drip; **no hired clinician** (editorial model, locked 22 Jun).
- **FAQPage RETROFIT + stale-rule reconcile across all 12 banked branches:** FAQPage is WANTED (Bing/AI, reversed 22 Jun); the stale "no-FAQPage" fleet-lint was a HARD build-fail under `FLEET_LINT_STRICT=1` in ~7 repos = a deploy landmine. Reconciled fleet-wide (lint → info/conditional-on-visible-FAQ); added real visible+JSON-LD FAQ to the banked Q-pages that had skipped it.
- **BACKUP PASS (29 Jun) — nothing laptop-only any more:** pushed previously laptop-only branches to origin: company-rescue (main + dev-b33), hervitals (dev-b38), trustedinteriors (dev-b43), homesandhedge (main + dev-b37), adhdhelper (dev-b39), sortedproperty (main). PeptideClear live source `dev-b29-mhra-data` also pushed (main stays the 6-behind trap, do NOT deploy main).
- **Drip-gate run across all banked batches:** all build clean + pass a11y + **0 antislop MAJORS** in new content; only blockers were contrast (shared `.text-xs` byline, fleet-core root cause) + reviewer gates.

## 🔄 26 Jun 2026 — this session's changes (deploy-coordination)
- **DEPLOYED LIVE:** B18 BabyData ONS name-trend visualiser (`/names/trends/`) · B21 HomesAndHedge Quick-Triage + Safety/Legal boxes · FitCalcs + DatesAndTimes + VettedHome + MerchantHQ + LTD logos/contrast/ad-safety.
- **Confirmed ALREADY live (the "banked" labels were stale):** B15 PeptideClear GLP-1/CagriSema · B19 ADHD Right-to-Choose hub · B20 HerVitals menopause hub (verified on the live URLs, not the commit prose).
- **LLB (#11):** the real **125-page Richard build** went live with the **corrected entity** (Lending for Later Life / **One Stop 4 Equity Release Ltd** / **FRN 952887**), replacing the stale 9-page wrong-entity build. ⚠️ **Now going PASSWORD-LOCKED** (`llb-gate.sh on`) — holding out One Stop's FRN publicly needs their **BAT approval first**; build it out fully behind the lock, unlock on One Stop sign-off. CTA stays off; Theme-A guides held.
- 🔴 **BANNER sites AdSense REJECTED** (FitCalcs/BabyData/DatesAndTimes/HomesAndHedge) — "Low value content", NOT a flip-a-switch: need Privacy + Contact + editorial-policy pages, cut the programmatic % (babydata 87% / ~7% unique), and a real named editor (replace "Oliver Mackman"), then resubmit. **Owned by the banner-AdSense session.** (FitCalcs + BabyData also left live-failing the contrast gate by an un-gated deploy — routed to that session.)
- **Reskins (E):** BBL `restyle-pilot` + FundBiz `dev-rolex-reskin` are ALREADY LIVE (the reskin IS the live branch); MHQ design live on main; **MI `dev-navy-teal-reskin` = a 26-line non-change, not a real redesign** → drop it.
- **Deploy infra:** root cause = GitHub Actions disabled account-wide (~Jun 8). Reliable manual deploy `~/fleet-deploy.sh` (now gates contrast). Verified live state in `~/control-panel/FLEET_DEPLOY_TRUTH.md`.

## Site numbering = Adam's order (core 1–6 · newer lead/content 7–12 · display-ad 13–16)
> Counts = `done / target`. ⭐ in Status = the #1 lead build to do next. 🅿️ = reskin parked.

| # | Brand | New pages | Upgrades | Tools | Answer blocks | Status |
|--:|---|--:|--:|--:|--:|---|
| 1 | MarketInvoice | 0 / 60 | **43** / 680 | **1** / 3 | 650 / ~300 | ✅ B3 funnel + GEO + league table + **FAQPage on 326pp** LIVE · **anti-slop sweep ✅ 24 Jun: Allianz/Funding-Circle non-IF mislabel fixed LIVE** · next: barclays consolidate, tighten ~64 thin capsules |
| 2 | MerchantHQ 🅿️ | **15** / 55 | 0 / 149 | 0 / 3 | 126 / 560 | ✅ **contract-exit hub LIVE** (pillar + 14 provider cancel guides) + FAQPage re-enabled · **last hard contrast fail fixed → LIVE 28 Jun (gate 0 unreadable)** · **anti-slop sweep ✅ 24 Jun: Zettle price + trade-location label fixed LIVE** · next: un-gated fee table · methodology · 🅿️ reskin still parked |
| 3 | PeptideClear | 0 / 49 | 0 / 268 | 0 / 4 | 267 / ~200 | 3 surge pages + 34 citations · ⭐ next-gen GLP-1 hub · /medical vs /research split |
| 4 | FundBiz 🅿️ | **4** / 124 | 0 / 142 | 0 / 3 | 138 / 230 | trade-credit surge · **B31 4 guides BANKED** (PG / FCA-regulation / PG-house-risk / late-filing) · ⭐ refinance / "stuck in a contract" hub · 17 decline guides |
| 5 | Best Business Loans 🅿️ | 0 / 73 | 0 / 112 | 0 / 3 | 115 / ~150 | mature · **B36 BANKED** (other session; antislop PERG-cite + BoE base-rate fixes pending, not shipped) · ⭐ MCA escalator-trap guide · real rate numbers (kill "see lender quote") · fix 398w capsule |
| 6 | Kartapay | **6** / — | 0 / 37 | 0 / 3 | 137 | PL+RO live (~40pp each); 137 answer capsules (mostly in content collections, no target set) · **B34 6 guides DEPLOYED LIVE 28 Jun** (⚠️ pages indexable not noindex: review) · ⭐ "loan, no UK credit history" PL/RO · fix EN-header bleed |
| 7 | VettedHome (Sorted) | 0 / 316 | 0 / 22 | **3** / 5 | 19 / 10 | 3 tools live (cost-to-sell, EPC, fees) · ⭐ spray-foam crisis hub · "How We Vet" · cost bands |
| 8 | Company Rescue / LTD Turnaround | **4** / ~50 | 0 / 41 | **13** / 2 | 41 / 535 | launched live + lead pipeline · **B33 4 insolvency Q-pages BANKED, HELD on named Licensed IP** · IndexNow automated 29 Jun · ⚠️ **LIVE empty-capsule bug on `/data/company-insolvency-by-type/`** (sourced answer rendering blank) — **being fixed this session** · verify privacy-404 · named-IP page · a11y labels |
| 9 | ADHD Helper | banked / 296 | 0 / 55 | **4+** / 4 | 50 / 265 | full tool suite live (ASRS/RTC/cost) · **B39 RTC / shared-care guides BANKED** (finishing pass: named-editor + CLAUDE.md FAQ-config fix) · ⭐ Right-to-Choose hub |
| 10 | Her Vitals | **7** / 328 | 0 / 70 | **1** / 3 | 80 / 1,070 | live (YMYL editorial) · **B38 7 Q-pages + menopause hub + HRT tracker BANKED** (finishing pass: Adam-Parker named-editor + verify "6-month unscheduled bleeding" line; NO clinician, editorial model) · ⭐ menopause/perimenopause evidence hub |
| 11 | Later Life Borrowing | **10** / ~20 | 0 / 115 | 0 / 4 | 0 / 250 | ✅ 10 guides + OG LIVE · ⚠️ **0 answer capsules across 125 pages = real gap, needs capsules** · remove "finalising" notice · rest = Richard/compliance |
| 12 | New IF site (2nd) | 0 / 90 | 0 / 167 | 2 / 4 | 170 / 40 | most-built, **not live** · ✅ **built right, all gates pass**; invisible "Get a quote" button fixed (contrast 4→0), AnswerCapsule component future-proofed, committed to branch `fix-answercapsule-prop` (NOT deployed, banked) · port 85-provider DB · embedded-finance + halal · **CONFIG-ONLY LAUNCH pending Adam's 5 decisions** (domain/brand, owner Ltd, CF account, author, lender panel) |
| 13 | Homes & Hedge | 21 / 367 | 0 / 44 | 0 / 3 | 36 / 13 | 21 content pages live · **AdSense remediation (author / privacy / contact / editorial) SHIPPED LIVE 28 Jun** · **B37 renter-disrepair Q-pages BANKED** (finishing pass: named-editor + verify Renters'-Rights-Act / Awaab dates) · ⭐ answer-first Quick-Triage + safety/legal boxes |
| 14 | DateKit → datesandtimes.co.uk | 32 / 216 | 0 / 32 | **10** / 5 | 33 / 1,455 | ✅ live; **bank-holiday JSON/CSV/iCal downloads LIVE** + 10 tools + data-asset · **AdSense remediation SHIPPED LIVE 28 Jun** (World-Cup BH line verified real + preserved) · **B41 6 guides BANKED** |
| 15 | FitGauge → fitcalcs.co.uk | 36 / 380 | 0 / 36 | **18** / 6 | 35 / 1,990 | ✅ live; **18 calculators (exceeds target)** · **AdSense remediation SHIPPED LIVE 28 Jun** · **B40 6 guides BANKED** · verify formula |
| 16 | NameNest → babydata.co.uk | 34 / 373 | 0 / 34 | **7** / 3 | 36 / 694 | ✅ live; ONS names + 7 tools + name-trend visualiser · **AdSense remediation SHIPPED LIVE 28 Jun** · **B42 7 guides BANKED** |
| 17 | TrustedInteriors 🔒 | **7** / TBD | — | — | 18 | 🟡 **LIVE on apex** (Neptune editorial design + section hubs + bespoke photography, per FLEET_REALITY) but **B43 7 Q-pages + site-index hub BANKED (held pre-launch)**. ⚠️ **18 answer capsules present but thin/pre-launch.** Open: owner Ltd entity (placeholders) + turn OFF CF "Block AI bots" (currently 403 to GPTBot = drift). Sister to VettedHome (interiors / KBB vertical). |
| | **FLEET** | **~2,800** | **~2,010** | **~55** | **~1,950 built / ~7,540 target** | |

**Health YMYL ⭐ items** (PeptideClear/HerVitals/ADHD/FitCalcs/BabyData/HomesAndHedge) build on the **editorial model** — no hired reviewer (locked 23 Jun). **🅿️ reskins** (MHQ/FundBiz/BBL) parked until Adam says ship.

## 🔧 Upgrades build queue (Step-2 on-page levers)
> The on-page lever queue, folded together with the money-page/schema audit (other session). Lane = who owns it: **mine** (mechanical/data-driven, safe to run) · **other session** (coordinate, don't clobber) · **Adam/mixed** (off-site or needs a decision). Priority **#1** and **urgent** are flagged. No em dashes.

| Lever | Sites | Lane | Priority |
|---|---|---|---|
| Front-loaded "best for" answer block on money pages | All 6 leadgen money sites (MI · MHQ · FundBiz · BBL · LTD · equity-release); partial on all 6 | mixed (other session started on MI) | **#1** |
| Schema + last-updated stamps sweep (FAQ/Review/Org/Author/Dataset/FinancialService/SoftwareApplication) | fleet-wide | mine (mechanical) | high |
| Schema hygiene specifics: FundBiz +Review · LTD +FinancialService +FAQ | FundBiz (other session) · LTD (mine) | mixed | high |
| Fan-out / PAA sub-query coverage on money pages (Qforia / DataForSEO PAA) | money pages fleet-wide | mine (data-driven) | high |
| "How we make money" + methodology + independence box beside every CTA | fleet-wide leadgen | mine | high |
| "Before you enquire" reassurance + form-safety microcopy above every lead form | fleet-wide leadgen | mine | high |
| Answer-first "Quick Triage + Safety/Legal" block on top guide pages | HomesAndHedge (start), YMYL sites | mine | high |
| Un-gated live comparison tables / real indicative numbers up front | MI (85-provider DB) · MHQ (fee table) · BBL (real rate numbers) | other session / data-gated | medium |
| Tables on tableless head-to-heads | FundBiz /mca/ + /lenders/ (other session) · LTD "X vs Y" pages (mine) | mixed | medium |
| Grok lever: live calculators/quote tools + X/community mentions | fleet-wide (calculators partly done; X/community = off-site) | mixed (Adam/social) | medium |
| MI capsule-tightening: ~64 thin/answer-first capsules to 40-180w liftable answers | MarketInvoice | OTHER SESSION | high (theirs) |
| Bing Webmaster + IndexNow money-page submissions | fleet-wide | mine/Adam | medium |
| LTD Privacy-Policy 404 fix + LTD managed-robots conflict investigation | LTD Turnaround | mine | **urgent** (live trust-killer) |

## Batches
| Code | Status |
|---|---|
| **QA · Anti-slop sweep** (per-site `/antislop-check`, standing gate) | ✅ **ONE-TIME SWEEP COMPLETE — all 13 in-scope sites except BBL + FundBiz (other session's lane), 24 Jun.** All ledger-tracked; daily `--new` delta live. **Clean (0 major):** HomesAndHedge, VettedHome, ADHD Helper, Her Vitals. **Real findings to action (verified, ~50% of raw flags were skeptic FPs):** 🔴 **PeptideClear (16 maj) = URGENT, YMYL** — fabricated/unverifiable health content LIVE: confirmed-fake "Lancet Jan 2026 UK HRT+GLP-1 RCT" (×2 pages), plus "ASA enforcement notice Sept 2025", "April 2026 Wegovy CV indication", uncited "78% women"/"25-40% lean-mass" stats, GHK-Cu product misattribution, vendor purity claims, + PubMed citation-feed noise (selank/ghrp-6). NICE TA1026 flags were FALSE (it IS the real tirzepatide appraisal, 23 Dec 2024 — verified, leave). 🟠 **Kartapay (6)** = wrong finance figures (EEA→UK interchange; "£100 contactless removed Oct 2021" is backwards — it was *introduced* then; FCA decline-reason overclaim; uncited BNPL uplift). 🟠 **LTD-Turnaround (3) + LLB (2)** = hollow/illustrative `/data/` "tracker" pages (fleet pattern → real data or reframe). **DatesAndTimes (1)** = invented "World Cup bank holiday 15 Jun 2026" (fix — it's a data site). FitCalcs (1) minor formula. BabyData (2, pre-launch) = ONS top-50 vs 51-100 mislabel. ⚠️ verify each before fixing |
| **B1** GEO caveats (MHQ/Kartapay) | ✅ **DONE** — verified already clean (nothing to ship) |
| **B2** on-page GEO pass | ✅ MI verified already-done · other mature sites likely same (low headroom) · value only on net-new |
| **B3** MI consolidation | ✅ **DONE + LIVE** (37 industry links + 5 dedupe 301s, 200-verified) |
| **B4** VettedHome tools | ✅ **DONE** — 3 honest tools (cost-to-sell, EPC checker, agent-fee benchmark), held/noindex |
| **B5** VettedHome new pages (~316) | ⏳ queued (BANKED). Incl. **/trades/ kitchen & bathroom FITTER cluster** (bathroom fitters 6,600, kitchen fitters 5,400, near-me variants, installation, wet-room, per-town leaves, installer how/cost). Data → trades-types/geo/services.ts, staged-release. Research: `~/sortedproperty/docs/trades-kitchen-bathroom-scope.md`. ⚠️ **FITTER/installer intent ONLY** — the whole-kitchen/bathroom **company + showroom + design + "new kitchen cost"** authority/leadgen belongs to **TrustedInteriors** (sister site, currently HELD); research banked at iCloud `Research/home-improvement/RESEARCH_KITCHENS_BATHROOMS_2026-06-22.md`. Do NOT build the company/design side on VettedHome. |
| **B6** ADHD screener + women-w-ADHD + RTC | ✅ **already built** (ASRS, RTC checker, cost-tool suite, women pillar, RTC-vs-private-vs-NHS) — live |
| **B7** LLB TIER-3 guides + OG | ✅ **DONE + LIVE** (10 guides, og-default) |
| **B8** citation data-assets (datesandtimes/babydata) | ✅ **DONE + LIVE** — datesandtimes bank-holidays (+ JSON/CSV/iCal downloads) + babydata ONS top-100 |
| ~~B8b fitcalcs calculators~~ | ❌ **WITHDRAWN — false gap** (calcs live under /diet + /running). fitcalcs has 18 calculators, exceeds target |
| **B9** PeptideClear content | ⏳ queued |
| **B10** PeptideClear technical | ⏳ queued |
| **B11** make passage-shape stick (tooling) | ✅ **DONE** — `passage-shape-gate.py` wired into `fleet-validate.sh` + regression #16 |
| **B12** **FundBiz** business-credit-cards cluster (Ltd-framed, risk wording: representative APR, for-limited-companies, subject-to-status). ~15–20k/mo, £55–98 CPC. BBL gets the "declined → loan" funnel | ⏸ parked — proportionate compliance check |
| **B13** MHQ payments cards (expense/corporate/prepaid) + **form cross-sell** ("also interested in?") | ⏸ **parked — FCA gate** (form add needs Supabase column first) |
| **⭐ LEAD BUILDS** | **— say the code, I run it —** |
| **B14** MerchantHQ contract-exit hub (pillar + 14 provider cancel guides + cancellation templates) | ✅ **DONE + LIVE** (23 Jun) |
| **B15** PeptideClear next-gen GLP-1 hub (retatrutide / CagriSema / survodutide; "in trials, not UK-legal" framing) | ⏳ ready |
| **B16** FundBiz refinance / "stuck in a contract" hub + BBL MCA escalator-trap guide (interlinked) | ⏳ ready · FundBiz/BBL 🅿️ reskin parked → build off main |
| **B17** VettedHome spray-foam-removal crisis hub + cost guide *(my lane)* | ⏳ ready |
| **B18** BabyData ONS name-trend visualiser *(my lane)* | ⏳ ready |
| **B19** ADHD Helper Right-to-Choose navigation hub (editorial model) | ⏳ ready |
| **B20** Her Vitals menopause / perimenopause evidence hub (editorial model) | ⏳ ready |
| **B21** HomesAndHedge answer-first Quick-Triage + safety/legal boxes *(my lane)* | ⏳ ready |
| **B22** Kartapay "business loan, no UK credit history" PL + RO + fix EN-header bleed | 🟢 **EN-bleed fix BANKED** on `dev-b22-kartapay-langfix` (24 Jun) — footer/nav labels now lang-aware (PL/RO); needs a native PL/RO spot-check before merge to main (Kartapay doctrine). New "no-credit-history" PL/RO pages NOT built yet (need native content). |
| **B23** MarketInvoice SERP cleanup: consolidate "barclays invoice finance" (10→1) + prune southall dupes | ✅ **DONE + LIVE (24 Jun)** — removed thin `/alternatives/barclays-invoice-finance/`, 301'd to `/providers/barclays/` (no chain), verified live. Southall dupes: none found (already clean). Verified Barclays still offers IF before acting. |
| **B24–B30** data-asset bank (VettedHome BUS-grant / heat-pump-cost / EPC-band-C · DatesAndTimes SPA-timetable / clock-change · BabyData child-benefit-HICBC / birth-rate) | 🟢 **BANKED (25 Jun)**, all sourced (Ofgem/DESNZ/EST/MCS/EHS/HMRC/ONS), gated 0-major, noindex, on dev branches. Drip needs a `/data/` index + nav + figure re-verify. Manifest: `~/control-panel/DATA-ASSET-BANK-2026-06-25.md`. |
| **B31** FundBiz 4 guides (personal guarantee / is-business-lending-FCA-regulated / partner-signed-PG-house-risk / late-Companies-House-filing → loan call-in) | 🟢 **BANKED (27 Jun)** — real legal grounding, noindex, pushed to origin. Other session's site. |
| ~~**B32** MI + MHQ question sets~~ | ❌ **CANCELLED (verify-first)** — both sites' `/questions/` already dense (would duplicate). |
| **B33** LTD Turnaround 4 insolvency Q-pages (s127 wages after petition / director redundancy via RPS / director-loan-or-BBL repay = s239 preference / liquidation & personal mortgage) | 🟢 **BANKED, HELD (27 Jun)** — Insolvency Act 1986 grounding + "take advice from Licensed IP" disclaimers. **Gated on Adam naming the Licensed IP** (`SITE.author.reviewer __TODO__`) before drip. Pushed to origin. |
| **B34** Kartapay 6 guides | ✅ **DEPLOYED LIVE 28 Jun** — ⚠️ pages are **indexable not noindex** (flag to review). Pushed to origin. |
| **B35** VettedHome questions | ✅ **DEPLOYED LIVE 28 Jun** — noindex (correct), 0 unreadable, 200s. |
| **B36** BBL banked | 🟢 **BANKED (other session)** — antislop flagged factual fixes (PERG cite, BoE base rate), **not shipped**. |
| **B37** HomesAndHedge renter-disrepair Q-pages | 🟢 **BANKED (27 Jun)** — pushed to origin. Needs Claude finishing pass (named-editor + verify Renters'-Rights-Act / Awaab dates). |
| **B38** HerVitals 7 Q-pages + menopause hub + HRT tracker | 🟢 **BANKED (27 Jun)** — pushed to origin. Needs Claude finishing pass (Adam-Parker named-editor + verify "6-month unscheduled bleeding" line). **No hired clinician** (editorial model, 22 Jun). |
| **B39** ADHD Helper RTC / shared-care guides | 🟢 **BANKED (27 Jun)** — pushed to origin. Needs Claude finishing pass (named-editor + a CLAUDE.md FAQPage-policy conflict to reconcile). |
| **B40** FitCalcs 6 guides | 🟢 **BANKED** (banner site / other session). |
| **B41** DatesAndTimes 6 guides | 🟢 **BANKED** (banner site / other session). |
| **B42** BabyData 7 guides | 🟢 **BANKED** (banner site / other session). |
| **B43** TrustedInteriors 7 Q-pages + site-index hub | 🟢 **BANKED, HELD pre-launch (27 Jun)** — pushed to origin. Blocked: owner Ltd entity + CF "Block AI bots" OFF. Site itself is live on apex. |
| **FAQPage RETROFIT + stale-rule reconcile** (across all 12 banked branches) | ✅ **DONE (27 Jun)** — FAQPage is WANTED (Bing/AI, reversed 22 Jun); added real visible + JSON-LD FAQ to banked Q-pages that skipped it; reconciled the stale "no-FAQPage" fleet-lint HARD-fail (`FLEET_LINT_STRICT=1`) fleet-wide → info/conditional. Was a deploy landmine in ~7 repos. |

## 📦 BANKED REGISTER — the bank/drip pile (where all the banked stuff is)
> Model (Adam, 18 Jun): upgrades → main; **new pages → BANK + drip-feed, never dump.** Two tiers: **🟢 BANKED** = built + ready to push · **🔵 BANKED NEXT** = scoped/queued, not built yet. Verified via git branches + prelaunch flags + release waves, 23 Jun.

# 🟢 BANKED — built, ready to push

**A. Ready-to-push lead builds (dev branches, gate-green, push when ready). ✅ ALL passed the adversarial anti-slop review (23 Jun): 9-build skeptic pass → 8 minor-fixes + 1 clean (BabyData), ZERO majors/kills. Every fix applied + committed (incl. real factual/legal catches: FundBiz APR maths, HomesAndHedge glue-trap/Awaab's law, VettedHome false template line, PeptideClear uncited £45m). Banked clean, ready to drip:**
- ✅ **B15 PeptideClear GLP-1 hub + CagriSema → LIVE** (confirmed on the live URL 26 Jun; "banked" label was stale) → `dev-b15-peptideclear-glp1`
- ⏳ B16 FundBiz refinance hub → `dev-b16-fundbiz-refinance` (`23043bf`) — HELD (interlinked w/ BBL)
- ⏳ B16 BBL MCA-factor-rate-trap guide → `dev-b16-bbl-mca-trap` (`cccdd9f`) — HELD (all BBL on hold)
- ⏳ B17 VettedHome spray-foam hub → `dev-b17-vettedhome-sprayfoam` (`20f3c84`) — HELD (wave-3 gated, not a clean deploy)
- ✅ **B18 BabyData name-trend visualiser → DEPLOYED LIVE 26 Jun** (`/names/trends/`)
- ✅ **B19 ADHD RTC hub → LIVE** (confirmed 26 Jun)
- ✅ **B20 Her Vitals menopause hub → LIVE** (confirmed 26 Jun)
- ✅ **B21 HomesAndHedge triage + safety/legal boxes → DEPLOYED LIVE 26 Jun**
- ⏳ LLB Theme-A 4 retirement-mortgage guides (held) → `dev-llb-theme-a-retirement`
- *(B15/B16/LLB agents hit a git/Bash sandbox block — I committed + gate-verified them in-session.)*

**A2. 27–29 Jun banked content tranche — built, gated (0 antislop majors), noindex, NOW PUSHED TO ORIGIN (no longer laptop-only):**
- 🟢 **B31 FundBiz** 4 guides → on dev branch (origin). Other session's site.
- ✅ **B34 Kartapay** 6 guides → **DEPLOYED LIVE 28 Jun** (⚠️ indexable, not noindex — review).
- ✅ **B35 VettedHome** questions → **DEPLOYED LIVE 28 Jun** (noindex, correct).
- 🟢 **B33 LTD Turnaround** 4 insolvency Q-pages → `dev-b33` (origin). **HELD** on named Licensed IP.
- 🟢 **B36 BBL** banked (other session) — antislop PERG-cite + BoE-base-rate fixes pending, not shipped.
- 🟢 **B37 HomesAndHedge** renter-disrepair → `dev-b37` (origin). Finishing pass pending.
- 🟢 **B38 HerVitals** 7 Q + menopause hub + HRT tracker → `dev-b38` (origin). Finishing pass pending.
- 🟢 **B39 ADHD Helper** RTC / shared-care → `dev-b39` (origin). Finishing pass + FAQ-config fix pending.
- 🟢 **B40 FitCalcs · B41 DatesAndTimes · B42 BabyData** 6/6/7 guides → banked (banner sites / other session).
- 🟢 **B43 TrustedInteriors** 7 Q + site-index hub → `dev-b43` (origin). **HELD pre-launch.**
- **Backup pass (29 Jun):** pushed previously laptop-only branches to origin — company-rescue (main + dev-b33), hervitals (dev-b38), trustedinteriors (dev-b43), homesandhedge (main + dev-b37), adhdhelper (dev-b39), sortedproperty (main). PeptideClear live source `dev-b29-mhra-data` also pushed (main stays the 6-behind trap — do NOT deploy main).

**B. Big banked SITE (the major one): 2nd Invoice-Finance site** (`~/invoicefinance-site`) — **167 pages built, NOT live.** Awaiting your 5 go-live decisions (brand/domain, owning Ltd, CF account, author, lender panel).

**C. Held on live sites (built + deployed but hidden):**
- VettedHome — 3 tools (cost-to-sell, EPC, agent-fee) noindex/held + the wave-3 spray-foam hub (LIVE_THROUGH_WAVE=2, so wave 3+ stays dark until bumped).

**D. Banked feature / content branches (finance + peptide — older, need triage before push):**
- PeptideClear: `citation-refresh/2026-06-22` (reviewed, ready) + 3 older citation-refresh branches (May 27 / Jun 1 / Jun 8 — likely superseded) + `feat/book-entity-asset`
- MerchantHQ: `feat/niche-batch-2-26may`, `feat/niche-batch-3-26may`, `feat/pl-ro-expansion-briefs` + `dev-ticker-tidy` (accessibility/search/site-index/stats work I preserved)
- Kartapay: `feat/behavioural-tracking`, `feat/easy-data-tools`

**E. Banked reskins (design, parked till you say ship):** MI `dev-navy-teal-reskin` · BBL `restyle-pilot` · FundBiz `dev-rolex-reskin` · MHQ `dev-ticker-tidy`.

**F. Committed, not yet deployed (safe, my lane):** FitCalcs + BabyData analytics-parity + ad-safety commits (a quick wrangler push when you want).

# 🔵 BANKED NEXT — scoped/queued, not built yet (the drip queue)

**📂 QUEUED CONTENT STORED IN THE REPOS (the per-site banks — build-ready, just not built):**
- **MerchantHQ `~/cardmachines/briefs/`** — 36 briefs → **15 already built, ~19 still queued** (verified 23 Jun). The queued ones are mostly **vernacular community pages** (-pa Punjabi / -bn Bengali / -gu Gujarati: corner-shop, takeaway, jewellery, pharmacy, taxi, Birmingham/Leicester/Wembley/Southall) + worldpay-cancel/leave (now covered by B14 exit hub) + 2 plan docs. **Vernacular ones need native-quality copy — flag, don't auto-build.**
- **Kartapay `~/kartapay/briefs/`** — ~48 PL/RO briefs → **most already built, ~4 still queued** (verified). Built-out is largely done; remaining need native PL/RO QA.
- **LLB `~/equity-release/docs/TARGET-BACKLOG.md`** — the explicit **banked target list**: **30 rows marked "BANK" (to build) vs 17 "BUILT✅(held)"** (verified), with volumes/SERP-status/suggested-page across the whole later-life-borrowing space + `CONTENT-ROADMAP.md` + `EXPANSION-low-comp-angles.md`. *(Theme-A retirement/pensioner-mortgage rows being built this session, banked.)*
- **Per-site `docs/BUILD-IDEAS.md` + `IDEAS-BRIEF.md`** — queued ideas/strategy on **PeptideClear, FundBiz, Her Vitals (+clinical-tools), ADHD Helper, HomesAndHedge**. PeptideClear also has `docs/PEPTIDECLEAR_BACKLOG_HANDOFF.md`.
- **VettedHome `~/sortedproperty/docs/`** — `findatradey-trades-play.md` + `trades-kitchen-bathroom-scope.md` (= B5).
- **iCloud `claude/Research/`** — the niche-attack harvests + per-niche build maps (source material: equity-release, supplements, home-services, kartapay-keyword-attack, niche-attack batches, etc.).

**G. Coded + ready to build (say the code):** B5 VettedHome kitchens/bathrooms · B15 PeptideClear GLP-1 hub · B16 FundBiz/BBL refinance · B22 Kartapay no-credit-history loan · B23 MI SERP cleanup.
**H. Grow-brief ⏸ HOLD bets (need your go / live-data validation first):** MI recourse-vs-non-recourse tool + hidden-fees catalogue + sector deep-hubs · MHQ hidden-fee calculator + settlement matrix · PeptideClear legality pillar + CoA guide · Her Vitals brand-comparison index + form/dose guides · ADHD private-cost + by-region FOI data · VettedHome heat-pump/cavity-wall + by-trade×town rollout · banner data-assets (SMP calc, working-days API). Full per-site list in the GROW-BRIEF doc.

## Build log (what shipped, with real deploy status)
- **29 Jun · anti-slop SWEEP + cleanup** — swept 1,359 live pages → 219 MAJORS, clustered on the programmatic MI `/vs/` + MHQ `/best/by-trade-and-city/` `/trade/` `/vs/` templates. Root causes (not 219 fixes): fabricated 4.x/5 ratings w/ no methodology (ASA/FCA + EEAT), category errors (iwoca/Funding Circle/Swoop/Capitalise/Allianz Trade mislabelled as IF rivals + likely-hallucinated "Bibby acquired Aldermore WCF 2023" + Kriya/Allica/Skipton/Novuna claims), MHQ template bleed (wrong-trade watch-outs, broken "Same as the underlying acquirer on a same as..." variable, leaked internal notes), missing FCA referral-fee disclosure. **CLEANUP IN PROGRESS** (ratings removed, facts verify-first). FALSE POSITIVES: "future date 2026-xx" flags (today IS 29 Jun 2026) + "Copy for AI" widget (intended). Also: **2nd-IF site** built right, all gates pass, invisible "Get a quote" button fixed (contrast 4→0), component future-proofed, committed `fix-answercapsule-prop` (banked, config-only launch pending Adam's 5 decisions). **LTD Turnaround** LIVE empty-capsule bug on `/data/company-insolvency-by-type/` being fixed.
- **29 Jun** — answer-blocks column corrected (was a broken ~1% tally; capsules are fleet-wide). Real per-site counts computed from source (class-in-pages + class-in-content-collections + AnswerCapsule component usages): MI 650, Peptide 267, FundBiz 138, Kartapay 137, MHQ 126, BBL 115, HerVitals 80, ADHD 50, LTD 41, H&H 36, BabyData 36, FitCalcs 35, DatesAndTimes 33, VettedHome 19, TrustedInteriors 18, plus 2nd-IF 170. Real gaps flagged: LLB (0 capsules across 125 pages), 2nd-IF-site (170 present but empty-prop bug renders them blank), TrustedInteriors (18, thin/pre-launch).
- **29 Jun** — folded the money-page/schema audit (other session) into the Upgrades build queue: front-loaded best-for (#1), PAA fan-out, schema hygiene (FundBiz Review / LTD FinancialService+FAQ), Grok calculators+mentions lever.
- **29 Jun · fleet · backup pass** — pushed all previously laptop-only branches to origin (company-rescue main + dev-b33, hervitals dev-b38, trustedinteriors dev-b43, homesandhedge main + dev-b37, adhdhelper dev-b39, sortedproperty main, peptideclear dev-b29-mhra-data). Nothing is laptop-only any more. ✅
- **29 Jun · LTD Turnaround · IndexNow** — built `scripts/indexnow-submit.cjs` + postbuild hook, submitted 92 URLs to Bing (200). Committed `feat/ltd-indexnow`. ✅
- **28 Jun · Kartapay · B34** — 6 guides → **DEPLOYED LIVE** (0 unreadable, 200s), branch pushed. ⚠️ pages indexable, not noindex (review). ✅
- **28 Jun · VettedHome · B35** — questions → **DEPLOYED LIVE** (noindex, 0 unreadable). ✅
- **28 Jun · MerchantHQ · contrast** — last hard contrast fail fixed (fleet-core AIComprehension "Quick Reference" `text-xs gray-400` 2.49:1, overridden in site `global.css`) → **DEPLOYED LIVE**, gate 0 unreadable; main pushed. ✅
- **28 Jun · banner ×4 · AdSense remediation** — HomesAndHedge / BabyData / FitCalcs / DatesAndTimes **SHIPPED LIVE** through build → contrast-gate → deploy → live-verify: Adam-Parker named-editor `/authors/adam-parker/` (Person + ORCID), Privacy / Contact / Editorial-policy pages, footer legal nav, oliver→adam 301, fake "registered reviewer/midwife" claims stripped. Caught + preserved DatesAndTimes "World Cup BH" line (verified real via gov.scot, a prior commit had wrongly deleted it). Patched a latent fleet-core AuthorBox "Last reviewed" `text-gray-400` 2.45:1 contrast bug. **PENDING ADAM: resubmit each to AdSense.** ✅
- **27 Jun · FAQPage retrofit + stale-rule reconcile** — added real visible + JSON-LD FAQ to the banked B31/B33/B34/B36/B40/B41/B42/B43 Q-pages that had skipped it; reconciled the stale "no-FAQPage" fleet-lint HARD-fail (`FLEET_LINT_STRICT=1`, a deploy landmine in ~7 repos) → info/conditional. FAQPage is WANTED (Bing/AI). ✅
- **27 Jun · banked content tranche** — B31 (FundBiz 4) · B33 (LTD 4, held) · B37 (H&H) · B38 (HerVitals 7 + hub + tracker) · B39 (ADHD) · B40/B41/B42 (banner 6/6/7) · B43 (TrustedInteriors 7 + hub, held) built (verify-first, real sources), gated 0-major, noindex, committed to dev branches. B32 (MI+MHQ Q-sets) CANCELLED as duplicative. ✅
- **24 Jun (pm) — anti-slop MAJOR remediation** — PeptideClear (YMYL) fabrications removed + LIVE (fake Lancet RCT, wrong Wegovy CV date->July 2024, ASA notice, GHK-Cu product error); premature banked-B15 deploy reverted + main reconciled with origin/pushed. LTD Turnaround 3 hollow /data/ trackers reframed + LIVE. DatesAndTimes "World Cup BH" verified REAL (Scotland gov.uk) = no fix. Kartapay contactless+tipping factfix BANKED on dev-b22. REMAINING (FLEET_INBOX): PeptideClear wave-2 citation/vendor, Kartapay interchange, LLB 2 /data/ majors. ~50% of skeptic flags were FPs (verify-first essential). ✅
- **24 Jun — anti-slop sweeps + fixes LIVE** — MI + MHQ full sweeps reviewed; real bugs fixed + live: MI non-IF mislabel (Allianz/Funding Circle, `9963454`), MHQ Zettle price + trade label (`e135e38`/`67125d9`). **B23** barclays consolidation LIVE (`5e7d2a6`, 301 verified). **B22** Kartapay EN-bleed footer/nav fix BANKED on dev (`c8443e6`, needs native spot-check). Smaller-site sweeps: H&H + VettedHome 0 major; LTD-Turnaround 3 hollow `/data/` pages (logged). `/antislop-check` skill built + daily `--new` delta cron live. ✅
- **⚠️ Open finding (LTD Turnaround)** — `/data/director-disqualifications/`, `/data/late-payment-index/`, `/data/strike-off-objections/` claim to be data trackers but show no figures (hollow over-claim + repeated padding). Fix = populate with real Insolvency Service / Payment Practices Reporting data, or reframe so they don't promise data they lack. Not auto-fixed (would mean inventing numbers).
- **B7 · LLB** — 10 TIER-3 guides + og-default → `b51310d`, wrangler-deployed, **LIVE**. ✅
- **B3 · MI** — 37 industry funnels (`e80877b`) + 5 dedupe 301s (`e47ab9d`) → **LIVE** (200-verified). ✅
- **B4 · VettedHome** — 3 tools: cost-to-sell (`da3fd6f`) + EPC + fee benchmark (`de839a9`) → built, held/noindex. ✅
- **B8 · display sites** — datesandtimes + babydata data-assets verified built + LIVE; fitcalcs 18 calcs (exceeds target). ✅
- **B11 · passage-shape gate** — `passage-shape-gate.py` audits `.answer-capsule` for AI-liftability; wired + registered #16. ✅
- **FAQPage REVERSED + MI LIVE** (22–23 Jun) — Google's deprecation is display-only; **Bing/Brave/Copilot still parse it** + Bing is a primary fleet channel. Re-enabled on genuine FAQ pages → **326 MI pages live** (`d360db3`). Rules + regression #1 flipped. ✅
- **DatesAndTimes downloads** (22–23 Jun) — bank-holiday JSON/CSV/iCal endpoints + Dataset `distribution` → merged main, **wrangler-deployed, 200-verified LIVE**. ✅
- **MI brand + bank-exit** (23 Jun) — visible operator/identity line + answer-first bank-exit capsule → **LIVE** (`e058e03`). 5 dashboard items marked done. Brand-term ranking = low-ROI (legacy brand). ✅
- **Reviewer lock** (23 Jun) — health named-reviewer recs **LOCKED OFF** (editorial model). ✅
- **B15/B16/LLB banked** (23 Jun) — PeptideClear GLP-1 hub + CagriSema, FundBiz refinance + BBL MCA-trap pair, LLB 4 retirement guides — built (verify-first), gate-green, committed to dev branches. ✅
- **⚖️ ANTI-SLOP REVIEW + FIXES** (23 Jun, ultracode workflow) — 9 banked builds adversarially reviewed (1 skeptic each + verifier on majors): **8 minor-fixes, 1 clean, 0 major/kill**. All fixes applied + committed on dev branches. Real catches: FundBiz MCA-APR maths was contradictory/wrong (fixed); HomesAndHedge glue-trap law + Awaab's-Law scope wrong (fixed); VettedHome scams page had a false template line + mismatched H2s (fixed); PeptideClear uncited £45m figure (removed); cross-page templating de-duplicated on LLB/ADHD/HerVitals/VettedHome. The guardrail working as intended — caught before any drip. ✅
- **MHQ ⭐ contract-exit hub** (23 Jun) — pillar `/cancel-card-machine-contract/` + 14 per-provider `/cancel/[slug]/` guides (Worldpay, Barclaycard, Dojo…), grounded in verified `uk-acquirers` contract terms (no fabricated fees) + cancellation-letter templates + FAQPage/ItemList schema. Built off main (independent of the parked reskin), wrangler-deployed, **200-verified LIVE** + IndexNow-submitted (910 URLs → Bing). Verify-first: switching-help was a service-pitch, not a how-to-cancel → genuinely net-new. ✅

## Pending merges (reviewed, not yet merged)
- **PeptideClear citation refresh** (`citation-refresh/2026-06-22`) — 44 PubMed papers reviewed: **~34 keep / ~10 reject** (selank false-match · kpv author-initial · cerebrolysin retractions). **Merge blocked** by active WIP + 404-sweep conflict; plan = compounds.json-only with rejects dropped once free.

## Blocked on Adam / off-site
PeptideClear **affiliate list** · off-site authority · research-peptides **narrowing decision** · SEOCompare Clarity + IndexNow · CF Turnstile keys · FormSubmit per-origin · MHQ Medium handle · **LLB completion** (Richard sign-off + s.21 + operating Ltd + legal values + GA4/Clarity IDs + flip) · **rates snapshot** (compliance) · **2nd IF site go-live** (5 decisions: domain/brand · owning Ltd + CH no. · CF account · author · lender panel) · **non-health trust items** (LTD named IP · Kartapay native PL/RO QA · VettedHome vetting depth) · **🅿️ reskins** (MHQ/FundBiz/BBL — say when to ship).
> ⛔ Health named-reviewer recs are **LOCKED OFF** (editorial model) — NOT a blocker.

---
---

# 📚 DETAIL / AUDIT / REFERENCE (below the plan)

## 🔬 FLEET AUDIT — 23 Jun 2026 (errors · live state · push-or-hold · posting)
> Sources: FLEET_REALITY 07:43 (14 live, all PASS) · deploy-health 07:30 (all healthy) · `fleet-audit.sh --build` · per-repo git state. **SEOCompare + rank4ai excluded.** Most sites deploy via **wrangler from local**, so "commits ahead of GitHub" = a backup gap, NOT a live gap.

| # | Site | Live | Gate (hard) | Built but NOT live → your call | Auto-posts | Top verified to-do |
|--:|---|:--:|---|---|---|---|
| 1 | MarketInvoice | ✅ | clean | — | **daily** 7–17h | ~64 thin capsules; public 85-provider DB |
| 2 | MerchantHQ | ✅ | clean | 🟡 `dev-ticker-tidy` reskin WIP (3) | youtube only | un-gated fee table + methodology |
| 3 | PeptideClear | ✅ | clean | 🟡 1 + citation-refresh branch | **full engine** | /medical vs /research split; GLP-1 hub |
| 4 | FundBiz | ✅ | clean | 🟡 `dev-rolex-reskin` WIP (1) | **daily** | research→rescue split; 17 decline guides |
| 5 | BestBusinessLoans | ✅ | 🔴 **FAIL** 398w capsule wall | 🟡 `restyle-pilot` WIP (2) | **daily** | real rate numbers; capsule fix (INBOX'd) |
| 6 | Kartapay | ✅ | clean | — | none | ⚠️ EN headers in /pl//ro/ finance pages |
| 7 | VettedHome | ✅ | clean | 🟢 **1 (tracking) — safe push** | none | "How We Vet"; review schema; cost bands |
| 8 | LTD Turnaround | ✅ | 🟠 2 a11y | 🟠 8 unpushed→GitHub (live via wrangler) | none | named IP; verify privacy-404; a11y labels |
| 9 | ADHD Helper | ✅ | clean | — | none | ⚠️ **not in FLEET_REALITY** (add check); RTC hub |
| 10 | Her Vitals | ✅ | clean | — | none | ⚠️ **not in FLEET_REALITY** (add check); menopause hub |
| 11 | Later Life Borrowing | ✅ | clean | 🟠 26 unpushed→GitHub (live via wrangler) | none | remove "finalising" notice; compliance flip |
| 12 | 2nd IF site | ❌ **not live** | 2 hollow | n/a — pre-launch | none | 5 go-live decisions; port 85-provider DB |
| 13 | HomesAndHedge | ✅ | clean | — | none | Quick-Triage + safety boxes; photography |
| 14 | datesandtimes | ✅ | clean | ✅ **DEPLOYED LIVE** (downloads + tracking) | none | — |
| 15 | fitcalcs | ✅ | clean | 🟢 **2 (tracking + AdSlot) — safe push** | none | verify formula accuracy |
| 16 | babydata | ✅ | clean | 🟢 **2 (tracking + AdSlot) — safe push** | none | ONS name-trend visualiser (⭐) |

**Legend:** 🟢 my lane, safe to deploy · 🟡 other-session reskin/WIP (holding) · 🟠 live via wrangler, just unpushed to GitHub (backup gap).

### 🚀 Recommended PUSH now (safe, my lane, gate-green)
A fleet-wide analytics-parity + ad-safety pass committed but not deployed: **datesandtimes** (✅ done) · **fitcalcs** · **babydata** · **VettedHome**. One wrangler batch.

### ⏸ HOLD (deliberate)
3 reskins mid-flight (MHQ/FundBiz/BBL — other-session WIP). 2nd IF site (5 decisions).

### 🗓️ Posting schedules
- **Auto-posting:** MarketInvoice (daily 7–17h), BestBusinessLoans (daily :30), FundBiz (daily :45), **PeptideClear** (blog + questions + deep-dive + citation-refresh + weekly — heaviest), MerchantHQ (youtube only).
- **NO scheduled posting:** Kartapay, VettedHome, ADHD, Her Vitals, HomesAndHedge, datesandtimes, fitcalcs, babydata, LTD, LLB.
- **Enhancement opportunity:** rank-hungry content sites with no cadence = **ADHD Helper, Her Vitals, HomesAndHedge** (display/calculator sites + LLB don't need one).
- **Monitoring gap:** ADHD + Her Vitals live but absent from FLEET_REALITY — add checks.

### 🔴 Real errors (everything else is advisory WARN)
- **BBL** — 398-word capsule wall (only hard FAIL; INBOX'd, on `restyle-pilot`).
- **LTD Turnaround** — 2 a11y FAILs + privacy-404 to verify.
- **2nd IF site** — 2 hollow pages (not live).
- Soft WARNs: passage-shape capsule-tightening (175 on MI), minor a11y, prelaunch sitemap-noindex (expected).

## 🔭 ALL-SITES BUILD BRIEF — folded in (22 Jun, 6-engine review). Mostly on-site FIXES. Verify live first.
### Recurring fleet-wide patterns (do once → roll across)
| # | Pattern | Type |
|--:|---|---|
| F1 | ⛔ **IGNORE named-reviewer recs on HEALTH sites** (locked 23 Jun) — editorial model (Oliver Mackman + literature-review), NOT hired clinicians. *(Non-health trust items separate: LTD IP, Kartapay native QA, VettedHome vetting.)* | closed decision |
| F2 | Un-gated comparison table / real numbers up front (MI public DB, MHQ fee matrix, BBL "see lender quote") | component + content |
| F3 | "How we make money" + methodology + independence proof beside every CTA | fix |
| F4 | Schema (Dataset/Review/Person/FinancialProduct/SoftwareApplication) + last-updated stamps | mechanical fix |
| F5 | Bing Webmaster + IndexNow (feeds Copilot/ChatGPT) | fix |
| F6 | Answer-first capsules / Quick-Triage blocks (= the passage-shape lever) | fix |
| F7 | Trust/safety/legal boxes on YMYL (LLB, LTD, HomesAndHedge) | fix |
| F8 | FundBiz↔BBL "Research-to-Rescue" funnel split (de-cannibalise) | restructure |

### ⚠️ URGENT on-site fixes it surfaced (verify live first)
- **LTD Turnaround — Privacy Policy 404** (trust killer on a distressed-director site) — verify + fix.
- **Kartapay — English headers bleeding into /pl/ & /ro/ finance pages** — purge/translate.
- **LLB — "still being finalised" preview notice still live** — remove before promoting.
- **Banner data-accuracy (verify):** FitCalcs formula, BabyData ONS labelling/SMP currency, DatesAndTimes substitute-days.

## 📄 Linked build-plan docs
- **⭐ `~/control-panel/fleet-review-prompts/FLEET-SUGGESTIONS-LIST.md`** (24 Jun) — the clean per-site MASTER build list: data assets · tools · content/question pages · authority anchor, for all 19 sites (Finterra + ResilienceBuilder excluded). Cross-engine collated (GPT-5/Gemini/Qwen/Grok), ⭐ = top picks. Bottom has the status split (build-now / YMYL-hold-the-expert / greenfield-bank) + cross-fleet shared engines. Full sourcing + verify/conflict flags + expert audit in `CITATION-MOAT-HANDOFF-2026-06-24.md`. **This is the build queue to work from next.**
- **`~/control-panel/INVOICE_FINANCE_BUILD_PLAN.md`** — MI (#1) + 2nd IF site (#12): MI plumbing (Bing WMT, citation checks, ItemList, sector×turnover, lead-qual); 2nd-IF (85-provider DB, embedded-finance, halal, lead pipeline).
- **`~/control-panel/fleet-review-prompts/_BUILD-BRIEF-ALL-SITES.md`** — 6-engine FIX review (above).
- **`~/control-panel/fleet-review-prompts/_GROW-BRIEF-ALL-SITES.md`** — niche-attack ⭐ BUILD NOW + ⏸ HOLD per site (don't trust volumes).
- **`HANDOVER-discovery-growth.md` + `HANDOVER-niche-attack-ALL.md`** — full validated set; #1 rule = verify-not-already-live-first (EV-charger lesson).
- **`~/sortedproperty/docs/kbb-kitchens-bathrooms-research.md`** → VettedHome B5.
- **`~/rank4ai-dashboard/business-credit-cards-niche-attack.md`** → B12/B13.

## 🛠️ Brief-execution order (my lane first, away from active sessions)
DatesAndTimes ✅ → BabyData (⭐ name-trend visualiser) → FitCalcs → HomesAndHedge (⭐ Quick-Triage) → VettedHome (⭐ spray-foam) → ADHD (⭐ RTC) → Her Vitals (⭐ menopause). Finance + Kartapay = now also workable (other session closed). SEOCompare grow skipped (niche-attack not run).

## Deploy discipline (Adam, 22–24 Jun)
Dev branch · wrangler (auth = token file `~/.cloudflare-dashboard-token` + account id; `npm run deploy` is indexing-only) · never auto-push main · ask before every deploy · verify-first per item · don't clobber. Display sites = wrangler from local (no auto-build). MI + SEOCompare = git-autobuild from main.
**🧹 Anti-slop gate (standing, 24 Jun):** every new/changed page passes `/antislop-check` (engine `~/fleet-tools/antislop_spotcheck.py`, model claude-sonnet-4-6) BEFORE drip — `--pages` on the built page, or the ultracode adversarial workflow for a batch. Daily `--new` delta runs automatically. **Always verify a flagged factual error against a live source before editing copy — the skeptic over-flags (~50% of concrete claims wrong: false "future date" stamps, uncited≠fabricated, occasional hallucinated quotes).**
