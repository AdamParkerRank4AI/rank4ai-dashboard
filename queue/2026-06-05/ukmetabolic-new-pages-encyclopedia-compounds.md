---
status: draft
site: ukmetabolic
type: new_pages
target_queries:
  - "nad plus uk"
  - "glutathione injection uk"
  - "thymosin alpha 1 uk"
  - "foxo4-dri senolytic"
  - "5-amino-1mq uk"
  - "ss-31 elamipretide uk"
target_urls:
  - /research-peptides/nad-plus/
  - /research-peptides/glutathione/
  - /research-peptides/thymosin-alpha-1/
  - /research-peptides/foxo4-dri/
  - /research-peptides/5-amino-1mq/
  - /research-peptides/ss-31/
current_state: |
  These 6 slugs are registered in encyclopedia-compounds.ts and served by
  [slug].astro, so the pages EXIST in the build. They were confirmed orphans
  in the 2026-06-05 crawl. Today's fix (research-peptides/index.astro update)
  has added hub links to all 6, so they will no longer be orphans after the
  next Cloudflare Pages deploy. However, the encyclopedia CONTENT on each
  page may be thin or stub-level; each needs a full editorial write-up before
  they rank.
proposed_change: |
  Full editorial write-up for each of the 6 compounds, following the established
  encyclopedia template:
  - 200-word answer capsule (mechanism, evidence tier, UK regulatory status)
  - Evidence grade pill (animal-only / mixed / human-rct / mechanistic)
  - UK retailers section (which of the 6 UK retailers stock this compound)
  - Regulatory framing paragraph (MHRA tier, no health claims, research-use framing)
  - EvidenceGrade + QuickSummary components already available in fleet-core

  Priority order (by search volume potential):
  1. /research-peptides/glutathione/ (high OTC volume, IV drip clinics angle)
  2. /research-peptides/nad-plus/ (longevity + anti-ageing cluster, high intent)
  3. /research-peptides/thymosin-alpha-1/ (immune health, growing awareness)
  4. /research-peptides/ss-31/ (mitochondrial disease, niche but growing)
  5. /research-peptides/5-amino-1mq/ (NNMT inhibitor, research audience)
  6. /research-peptides/foxo4-dri/ (senolytic, specialist audience)

why: >
  Hub links are now live after today's fleet fix. Getting the encyclopedia
  content up to full depth will make these pages rankable. NAD+ and glutathione
  in particular have high UK search volume (est. 5,000-15,000/month for NAD+
  related queries, 2,000-8,000 for IV glutathione). The PeptideClear research-
  use framing and MHRA context is differentiated vs thin retail pages. Author:
  Oliver Mackman. No dosing, no health claims, no human-use protocols per site rules.

author: Oliver Mackman
---
