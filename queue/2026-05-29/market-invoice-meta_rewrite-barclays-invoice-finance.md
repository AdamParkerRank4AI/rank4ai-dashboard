---
status: draft
site: market-invoice
type: meta_rewrite
target_query: barclays invoice finance
target_url: /providers/barclays/
current_state: |
  title: "Barclays Invoice Finance 2026: Rates, Eligibility, Reviews"
  description: "Barclays invoice finance for UK businesses from £500k turnover. Confidential discounting rates, eligibility, setup speed and how it compares in 2026."
proposed_change: |
  title: "Barclays Invoice Finance 2026: Rates, Eligibility, How It Compares"
  description: "Barclays invoice finance: confidential discounting from £500k turnover, base+1.5-3% pricing, 10-15 day setup. How Barclays compares to Close Brothers, HSBC, and Aldermore. Independent review 2026."
why: |
  GSC data: "barclays invoice finance" pos 12.3, 26 imps, 0% CTR.
  Position 12 (bottom of page 1 or top of page 2) with zero CTR suggests the snippet is not
  earning clicks despite reasonable placement.

  The current description is generic: "Barclays invoice finance for UK businesses from £500k
  turnover. Confidential discounting rates, eligibility, setup speed and how it compares in 2026."
  It gives no specific data that differentiates the snippet from competitors in the SERP.

  The proposed description leads with specific, scannable data points that a searcher evaluating
  Barclays will immediately recognise as useful: the £500k turnover threshold, the pricing range
  (base+1.5-3%), and the setup timeline (10-15 days). These are factual numbers already confirmed
  in the page body. Including competitor names (Close Brothers, HSBC, Aldermore) matches the
  "how it compares" intent and earns clicks from users in the evaluation stage.

  Title tweak: "Reviews" is lower intent than "How It Compares" for someone actively evaluating
  Barclays against alternatives.

  File to edit: market-invoice/src/pages/providers/barclays.astro
  Lines to change: `const title` and `const description` variables (lines 10-11).
---

## Implementation notes

In `market-invoice/src/pages/providers/barclays.astro`, update lines 10-11:

```astro
const title = "Barclays Invoice Finance 2026: Rates, Eligibility, How It Compares"
const description = "Barclays invoice finance: confidential discounting from £500k turnover, base+1.5-3% pricing, 10-15 day setup. How Barclays compares to Close Brothers, HSBC, and Aldermore. Independent review 2026.";
```

Verify the pricing figures (base+1.5-3%, service charge 0.3-0.7%) are still accurate against
the FAQ copy on the same page before publishing. Author: Oliver Mackman.
