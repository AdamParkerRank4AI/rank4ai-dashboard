# Dashboard Redesign Spec

Status: AGREED, 3 Jun 2026. Decisions locked (see below). Nothing built yet.

## Decisions locked (3 Jun 2026)
1. **AI Search is its own 6th per-brand group** (readiness + citations pulled out of Ecosystem).
2. **Ops/plumbing lives in a separate "Fleet Ops / Health" tab**, off the overview.
3. **Brand row = 5 numbers:** status pill, visits (7d), clicks, leads, health light. AI citations stay one click deeper.
4. **Status switch stops fetching:** pre-launch + paused sites skip daily audits and API pulls (accept history gaps while parked).


Goal in one line: make both dashboards read as "here are my brands, here's how each is doing, click in for the 5 things that matter". Today it reads as one long mixed scroll of brand data and ops plumbing, with 18 flat per-brand tabs and fake controls.

---

## 0. The two dashboards (the constraint, confirmed)

There is ONE repo (`~/rank4ai-dashboard`) and ONE `index.astro`. It is built TWICE:

| Build | env | Brands shown | Deploys to |
|---|---|---|---|
| **rank4ai** | `DASHBOARD=current` | rank4ai, resiliencebuilder | rank4ai-dashboard.pages.dev |
| **fleet** | `DASHBOARD=fleet` | the other 16 brands | fleet-dashboard-1nt.pages.dev (canonical) |

An `isFleet` flag already gates the fleet-only tiles. **Keep this split.** The redesign improves the shared shell, so both dashboards get the new structure automatically; only the brand-set filter differs. No code fork.

Side fix to confirm: the deploy workflow pushes to project `fleet-dashboard`, but the canonical live URL is `fleet-dashboard-1nt`. Nail down which project is real and point the workflow at it, so we stop deploying to a possibly-orphaned project.

---

## 1. The three levels (what Adam asked for)

1. **Fleet overview** — one screen, every brand a row, scannable. Brand data only. Ops plumbing moves out.
2. **Lifecycle control** — a real status switch per brand (pre-launch / live / paused) that things actually obey.
3. **Per-brand** — 18 flat tabs collapsed into 5 clear groups.

---

## 2. Level 1: Fleet Overview

### Principle
The overview shows BRANDS, not the machinery that feeds them. Every system-plumbing panel moves to a separate "Ops / Health" view (a tab, or a collapsed section at the bottom).

### One row per brand
Each brand = one row with a real **status pill** + the numbers that matter at a glance:

`[status pill] Brand · visits (7d trend) · clicks · leads · health light · last change`

Click the row to expand top recs + top queries (the quick-view already does this; we keep that).

### The 28 current panels, triaged

KEEP on overview (brand-level, glanceable):
- Search funnels (Google / Bing / AI)
- Fleet quick view (becomes the one-row-per-brand table above)
- Wins This Week
- AI Traffic (30d)
- Recommendations & Issues (summary)
- Site Changes (changelog feed)
- The brand grid (see below)

MOVE to "Ops / Health" (system plumbing, not brand performance):
- Build live (build stamp)
- Deploy parity / drift detector
- Fleet baseline checklist
- Data feeds (freshness)
- Title truncation linter
- CLAUDE.md drift detector
- llms.txt validator
- System Status (the 7-point GA4/GSC/Crawl/etc checklist)
- Entity coherence (moves, but ALSO feeds the new Ecosystem loop, see §5)

MERGE / RETIRE (duplication):
- "Fleet Channel Overview" duplicates the per-brand channel cards and the quick view. Retire or fold into the funnels banner.
- "AI bot intelligence" + "Cloudflare AI Crawl Control" both show bot hits. Merge into one bot panel.
- "Content freshness" + "Syndication tracker" → keep but as fleet-only, lower down.

### One brand grid, not two
Today: "Client Sites" (full) + "Our Sites" (80% opacity, "Staging"). Replace with ONE grid where the **status pill** does the work of telling live from pre-launch from paused. No more two-grid confusion.

---

## 3. Level 2: Real lifecycle control

### The problem
`siteStatus` today only changes how brands are grouped on screen. The toggle on the settings page writes nothing. Fetchers ignore it. "Press live / not live" is currently a mirage.

### The fix
Make status a real, written switch with three states:

- **pre-launch** — building, not public yet (golf-tech, women's health, etc.)
- **live** — public, fully tracked
- **paused** — was live, now parked

Make it obeyed in three places:
1. **Overview filter** — pill colour + which section a brand sits in.
2. **Fetchers** — skip pre-launch/paused sites so we stop burning audit/API calls on them (this is the real win).
3. **Per-brand header** — the status shown + the toggle to change it.

Where it's written: `clients.json` `siteStatus` becomes the single source of truth, edited through the toggle (a tiny write endpoint or a committed change), and the fetchers read it before running.

---

## 4. Level 3: 18 tabs to 6 groups

All 18 sections render real data today (good). We are GROUPING them, not rebuilding them.

| New group | Rolls up (existing tabs) | What Adam called it |
|---|---|---|
| **Performance** | traffic, search-performance, leads, wins | "traffic, clicks, good things" |
| **Recommendations** | recommendations, competitors, content-plan | "recommendations etc" |
| **Health** | site-speed, uptime, crawl-activity, daily-audit | "site speed etc" |
| **The Site** | site-manager, page-compliance, site-structure, site-tree | "the site, content, everything perfect" |
| **AI Search** | ai-readiness, ai-citations | the differentiator, its own headline (locked decision 1) |
| **Ecosystem** | entity-stack (+ the sameAs loop, §5) | "3rd party links, FB profile, sameAs" |

Notes:
- `site-structure` vs `site-tree` overlap → become two views inside "The Site", or merge.
- `vernacular` → lives under "The Site" or "Recommendations" as a sub-view (low priority, only a few sites use it).

Implementation is light: `sections.json` gains a `group` field; the per-brand nav renders 5 group tabs, each group lists its sub-sections. The section pages themselves don't change.

---

## 5. Ecosystem loop closure (the sameAs check)

### Today (60% there, wire missing in the middle)
- `entity_stack.json` = the build PLAN for Oliver (where profile URLs get pasted; mostly empty, only MerchantHQ done).
- `check_entity_coherence.py` = a real verifier, but it reads the LIVE site's schema sameAs (4 sites only) and HEAD-checks those URLs.
- **Nothing connects them.** When Oliver pastes a Facebook URL into the stack, nothing checks it is (a) live and (b) actually present in the site's sameAs.

### The close
When a profile URL is added to a brand's entity stack, auto-check and show two lights:
1. **Live?** HTTP 200-399 (reuse the existing liveness logic, including the bot-blocked allowance for LinkedIn/X/etc).
2. **In sameAs?** Is this exact URL present in the live site's schema.org sameAs array?

Then the Ecosystem tab shows, per profile: `live ✓/✗ · in sameAs ✓/✗`, and flags the two failure modes:
- URL in stack but NOT in site sameAs → "add to schema".
- URL in site sameAs but dead → "fix or remove".

This extends `check_entity_coherence.py` to read entity_stack URLs too and cross-reference, writing one combined `entity_coherence.json` the Ecosystem tab consumes. Roll it out to all brands, not just the 4.

---

## 6. Build order (each phase shippable on its own)

1. **Overview split** — move the 8 plumbing panels to an Ops view, merge the dup channel/bot panels, collapse to one brand grid with status pills. Biggest clarity win, lowest risk. (Touches `index.astro` only.)
2. **Per-brand grouping** — add `group` to `sections.json`, render 5 group tabs. No data changes.
3. **Real status switch** — make `siteStatus` written + obeyed by overview and fetchers.
4. **Ecosystem loop** — extend the coherence script + Ecosystem tab, roll out fleet-wide.

---

## 7. Decisions (all answered 3 Jun 2026)

1. AI Search → its own 6th group. RESOLVED.
2. Ops → separate tab. RESOLVED.
3. Brand row → status, visits, clicks, leads, health (AI citations one click deeper). RESOLVED.
4. Status switch → stops fetching on pre-launch/paused. RESOLVED.

See "Decisions locked" at the top.
