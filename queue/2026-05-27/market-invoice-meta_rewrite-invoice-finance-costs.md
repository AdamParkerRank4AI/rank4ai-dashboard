---
status: draft
site: market-invoice
type: title_rewrite
target_query: invoice finance costs uk
target_url: /guides/costs/
current_state: |
  title: "Invoice Finance Costs UK 2026: Real Fees From 0.5%"
  description: "Full fee breakdown: 0.5-3% service charge plus 1-3% above BoE base (3.75%) discount charge. On £100k of invoices, expect £850-£4,250/month."
proposed_change: |
  title: "Invoice Finance Costs UK 2026: Full Fee Breakdown"
  description: "Invoice finance costs: service charge 0.5-3% of invoice value, plus discount charge 1-3% above BoE base rate. On £100k of invoices, typical monthly cost is £850-£4,250. UK 2026 real-fee guide with worked examples."
why: |
  GSC data: 711 impressions, position 16.1, 0% CTR. Position 16 is page 2; moving to page 1
  requires content signals (out of scope for meta-only fix), but the description can be improved
  to earn more clicks once position improves organically and to support a later title-tag A/B.
  
  The current description is dense with numbers but reads as a raw data dump with no narrative.
  The proposed rewrite structures it as a sentence (costs: X, plus Y; result: Z) and adds
  "worked examples" as a CTR-boosting signal (users trust concrete examples over abstract ranges).
  
  Title change: "Full Fee Breakdown" replaces "Real Fees From 0.5%" — "full" signals comprehensive
  coverage; "real fees from 0.5%" may read as a teaser that undersells the page depth.
  
  File: market-invoice/src/pages/guides/costs.astro
  Change: title and description only.
  
  Note: position 16 means a meta-only fix has limited near-term impact. Priority is lower than
  the how-invoice-finance-works rewrite (pos 9.1). Consider pairing with a content depth check
  on this page in the next session.
---

## Implementation notes

In `market-invoice/src/pages/guides/costs.astro`, update:

```astro
title="Invoice Finance Costs UK 2026: Full Fee Breakdown"
description="Invoice finance costs: service charge 0.5-3% of invoice value, plus discount charge 1-3% above BoE base rate. On £100k of invoices, typical monthly cost is £850-£4,250. UK 2026 real-fee guide with worked examples."
```
