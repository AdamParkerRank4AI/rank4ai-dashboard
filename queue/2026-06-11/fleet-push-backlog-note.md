---
status: needs-human
type: ops-note
title: "Git push backlog: 3 repos have large unpushed commit queues"
date: 2026-06-11
---

## What happened

The remote fleet-review environment cannot push large git payloads through the local proxy
(HTTP 503 on send-pack for payloads above ~500KB). This has caused commit backlogs to
accumulate in three repos. Today's meta desc fixes were pushed directly via GitHub API
(mcp__github__push_files), but the accumulated commits from previous sessions are not yet
on origin.

## Repos affected

### ukmetabolic (PeptideClear)
- **23 commits** ahead of origin/main (local only)
- ~60 files changed, 4675 insertions
- Notable content: /statistics/ page, /research/ hub, UK Peptide Transparency Index study,
  new best/* pages (BPC-157, ipamorelin, MOTS-c, tesamorelin, sermorelin, TB-500),
  /explained/* pages (GLP-1 and hair loss, hype vs reality, how semaglutide works, etc.),
  Oliver Mackman ORCID wired into author schema, half-life calculator, fleet gate
  improvements, PreferredSource + ExpertCounterOpinion components
- **Action**: `cd ~/ukmetabolic && git push -u origin main` from your Mac (no proxy limit)

### market-invoice
- **50 commits** ahead of origin/main (local only)
- ~202 files changed (94 are auto-generated market-activity JSON files)
- Notable content: market-activity interactive chart data (2004-2026 JSON), lead submit
  function at /api/mi-lead-submit.ts, docs/BUILD-IDEAS.md, fleet-core patch v0.8.1,
  _redirects, fleet gate improvements, daily stat content auto-publishes
- **Action**: `cd ~/compare-invoice-finance && git push -u origin main` from your Mac

### cardmachines (MerchantHQ)
- **50 commits** ahead of origin/main (local only)
- ~47 files changed
- Notable content: x-default hreflang on English pages, broker vs direct-acquirer comparison
  table, GEO advisory schemaCore BreadcrumbList fixes on hub pages, fleet gate improvements
  (GEO data-formats warn gate, freshness check, /explained/ classifier), fleet-core v0.6.7
  DataAsText + ExpertCounterOpinion on calculator/stats pages
- **Action**: `cd ~/cardmachines && git push -u origin main` from your Mac

## Why today's fixes still deployed

The 11 meta desc fixes (9 PeptideClear, 1 Market Invoice, 1 MerchantHQ) were pushed
directly to GitHub origin via the GitHub API, bypassing the proxy. CF Pages picked these
up and is rebuilding now.

The backlogged commits are safe in the local repos in this remote environment. They will
persist until you push them or the environment is recycled.

## Recommendation

Push all three from your Mac in one terminal session. The proxy limitation is specific to
the remote Claude environment; your local Mac git push has no such limit.
---
