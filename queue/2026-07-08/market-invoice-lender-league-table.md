---
status: draft
site: market-invoice
type: new_page
target_query: uk invoice finance lenders comparison
target_url: https://marketinvoice.co.uk/data/uk-invoice-finance-lender-league-table/
current_state: |
  Page BUILT but NEVER DEPLOYED. Source: ~/compare-invoice-finance/src/pages/data/uk-invoice-finance-lender-league-table/
  (referenced in FLEET_INBOX as P1 "deploy the built Lender League Table — fastest AIO-citation win").
  The page exists in the repo; it just hasn't been pushed live.
proposed_change: |
  This is a DEPLOYMENT task, not a content draft. Steps:
  1. cd ~/compare-invoice-finance
  2. Verify the page builds cleanly: npm run build
  3. Check the page has valid schema (DataFeed / Dataset / Article)
  4. Verify no em-dashes in the content
  5. npm run deploy (or push to main and let CF auto-build)
  6. Submit URL to GSC URL Inspection + IndexNow
  
  The Lender League Table is described in the FLEET_INBOX as the "fastest AIO-citation win"
  for MI. It's a curated ranking of UK invoice finance lenders by rate/advance/setup time —
  exactly the kind of comparative neutral-data page that AI engines cite.
why: |
  FLEET_INBOX P1: "deploy the built Lender League Table (data/uk-invoice-finance-lender-league-table/,
  never deployed, fastest AIO-citation win)". This page already exists in source but has never been
  deployed. It could be live today with a single push. AIO-citation priority: MI is the site
  most likely to gain AI-search citations in the invoice finance vertical, and a curated
  ranked table is exactly the format AI engines extract and cite.
---
