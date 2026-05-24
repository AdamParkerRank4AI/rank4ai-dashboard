---
status: draft
site: market-invoice
type: cannibalisation_consolidation
priority: medium
target_data_file: cannibalisation.json (sites.market-invoice.top)
current_state: |
  MI has 9 cannibalised queries. Two clear patterns:

  PATTERN A — Barclays family (4 queries) split between:
     - /blog/did-barclays-stop-invoice-finance/  (better for "stop" / informational query)
     - /alternatives/barclays-invoice-finance/   (better for "alternatives" commercial intent)
     - /providers/barclays/                       (provider profile)

  The 3 are LEGITIMATELY DIFFERENT INTENTS but Google is treating them as
  overlapping. Currently /blog/did-barclays-stop/ ranks higher (pos 9.5-12.6)
  than /alternatives/barclays/ (pos 13-19). For the commercial-intent
  queries ("barclays invoice finance", "barclays invoice factoring") the
  /alternatives/ page should be canonical because the user is shopping
  for alternatives, not researching "did they stop".

  PATTERN B — Branded-own ("marketinvoice", "best invoice finance providers
  uk 2026", "marketinvoice reviews", "market invoice loss rates") split
  across homepage + /best/ + various pages. This is fine — branded-own
  cannibalisation usually self-resolves and shouldn't be aggressively
  consolidated (homepage NEEDS to rank for own brand).
proposed_change: |
  Pattern A fix:
    /blog/did-barclays-stop-invoice-finance/ — keep canonical (it's the
    answer for that exact informational query).

    /alternatives/barclays-invoice-finance/ — strengthen by:
    - Adding an internal link from /blog/did-barclays-stop/ to
      /alternatives/barclays-invoice-finance/ with anchor text "alternatives
      to Barclays" — pulls commercial-intent users to the right page.
    - Make sure the alternatives page title leads with "Alternatives to
      Barclays Invoice Finance: Compare UK Lenders 2026" (already updated
      yesterday — verify).

    /providers/barclays/ — defensible (provider profile, different intent).
    Add canonical rel pointing to itself + internal link from
    /alternatives/barclays-invoice-finance/ → /providers/barclays/ as
    "Full Barclays review" footnote.

  Pattern B: leave alone. Branded-own cannibalisation is healthy.

  Bonus: noise query "bibby financial services -site:reddit.com..." is a
  research operator query, not a real visitor query. Filter from
  cannibalisation analysis — the noise filter is already in
  classify_queries.py but not yet in detect_cannibalisation.py. Add it.
why: |
  MI is correctly differentiating informational vs commercial vs provider-
  profile intents. The fix is to strengthen internal-link routing between
  them so Google sees a clear hierarchy: blog (info) → alternatives
  (commercial) → providers (profile). Don't 301 or canonical-collapse.
needs_human_input: |
  None — agent can ship internal-link additions safely.
---
