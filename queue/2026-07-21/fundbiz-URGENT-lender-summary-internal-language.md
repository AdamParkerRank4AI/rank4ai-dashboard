---
status: draft
site: fundbiz
type: meta_rewrite
target_query: (affects all lender pages)
target_url: /lenders/*
current_state: |
  src/pages/lenders/[slug].astro line 14:
    const description = `${lender.summary.slice(0, 155)}`;
  The lender.summary field for 365 Business Finance contains:
    "Panel direct MCA lender we route to for £25k+ card-flow advances where the
     applicant wants a no-broker-fee structure. We also send case-by-case post-decline
     files here when missed payments or recent CCJs sit in the file but the card flow
     remains strong. Best fit for hospitality..."
  This is internal broker routing language and should NEVER appear as a public meta description.
proposed_change: |
  OPTION A (recommended): Add a `metaDescription` field to the Lender type in lenders.ts.
    In [slug].astro, change line 14 to:
      const description = lender.metaDescription ?? `${lender.summary.slice(0, 155)}`;
    Then audit ALL lenders.ts entries and add metaDescription overrides for any entry
    whose summary contains internal routing language.

  OPTION B (quick fix for 365 Business Finance only): Add a reviewMeta or metaDescription
    to the 365-business-finance entry:
      metaDescription: '365 Business Finance provides merchant cash advance from £10k to £500k
      for UK Ltd companies. Factor rate 1.10 to 1.40, 24 to 48 hour decisions, no minimum
      monthly fee. Compare on FundBiz.'

  Affected lenders to check urgently (those with internal routing language):
  - 365-business-finance (confirmed affected)
  - Any lender whose summary starts with "Panel", "Route to", "We route", "Case-by-case"
why: |
  Google indexes meta descriptions. If Google is crawling and indexing "Panel direct MCA
  lender we route to..." as the description for the 365 Business Finance page, this is
  appearing in the SERP snippet for users searching "365 business finance". This is:
  1. Confusing to end users who don't understand internal broker language
  2. A possible reason for the 0% CTR at position 19.1 (100% skip-over rate)
  3. A potential quality signal issue if Google sees site descriptions as internal jargon

  This should be fixed before any other title/description optimization on the lender pages.
---
