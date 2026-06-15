---
status: draft
site: market-invoice
type: title_rewrite
target_query: "barclays invoice finance"
target_url: /providers/barclays/
current_state: "Barclays Invoice Finance 2026: Rates, Eligibility, Reviews"
proposed_change: "Barclays Invoice Finance UK 2026: Rates, Status and Alternatives"
why: >
  67 impressions at position 16.2 with 0% CTR. A companion blog post
  ("did barclays stop invoice finance") exists in the repo, which signals
  that a large share of searchers are trying to establish whether Barclays
  still offers invoice finance. Adding "Status" to the title captures that
  intent, and "Alternatives" pulls in the high-commercial-intent tail
  (users who discover Barclays is unavailable or unsuitable). Adding "UK"
  signals geographic relevance to UK searchers.
---

## Context

The repo already has `/blog/did-barclays-stop-invoice-finance.astro`
which covers the question directly. The provider page at `/providers/barclays/`
is the commercial-intent target. Merging "Status" intent into the provider
page title can capture both informational and comparison clicks from the same
query.

Barclays moved their invoice finance product to larger clients only (approx
£1m+ turnover). Many SME searchers arrive expecting to use Barclays and need
to be redirected to alternatives. A title that signals "we cover this" lifts
click intent.

## Proposed title

```
Barclays Invoice Finance UK 2026: Rates, Status and Alternatives
```

65 chars. Adds "UK" (geographic signal), replaces "Eligibility, Reviews"
with "Status and Alternatives" (intent match for searchers who suspect
Barclays may not be available to them).

## Change required

Edit `/src/pages/providers/barclays.astro`:

```astro
const title = "Barclays Invoice Finance UK 2026: Rates, Status and Alternatives"
```

No body copy changes needed unless the page does not currently cover
the status question (whether Barclays still actively offers invoice finance
to SMEs). If the body lacks this, add a short factual paragraph at the top.
