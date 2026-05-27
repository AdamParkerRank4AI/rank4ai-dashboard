---
status: draft
site: market-invoice
type: title_rewrite
target_query: how does invoice finance work
target_url: /guides/how-invoice-finance-works/
current_state: |
  title: "How Does Invoice Finance Work? UK 2026 Step-by-Step Guide"
  description: "Invoice finance releases 70 to 95% of unpaid invoice value within 24 hours. Step-by-step UK guide to factoring vs discounting, real 2026 costs, and how."
proposed_change: |
  title: "How Does Invoice Finance Work? UK Guide 2026"
  description: "Invoice finance releases 70-95% of your unpaid invoice value within 24 hours. UK 2026 guide: how it works step by step, factoring vs discounting, real costs, and who qualifies."
why: |
  GSC data: 827 impressions, position 9.1, 0% CTR. Ranked in top-10 nationally for a high-intent
  informational query with zero clicks. The page is visible but not compelling searchers to click.
  
  Current description ends abruptly at "real 2026 costs, and how" — truncated sentence that reads
  as unfinished. This is likely hurting CTR. The proposed rewrite completes all sentences, adds
  "who qualifies" (high-intent signal for readers evaluating fit), and keeps the key data point
  (70-95%, 24 hours) in the first line for immediate credibility.
  
  Title is strong already; minimal change (moved "Guide 2026" to end for cleaner read).
  
  File: market-invoice/src/pages/guides/how-invoice-finance-works.astro
  Change: title and description props only (frontmatter or Layout call).
---

## Implementation notes

In `market-invoice/src/pages/guides/how-invoice-finance-works.astro`, update the title/description:

```astro
title="How Does Invoice Finance Work? UK Guide 2026"
description="Invoice finance releases 70-95% of your unpaid invoice value within 24 hours. UK 2026 guide: how it works step by step, factoring vs discounting, real costs, and who qualifies."
```

No body copy changes needed. Description fix is the priority — truncated description is the
likely CTR killer here.
