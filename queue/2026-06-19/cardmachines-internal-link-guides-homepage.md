---
status: draft
site: cardmachines
type: meta_rewrite
target_query: card machine guides
target_url: /guides/
current_state: |
  MHQ has 7 /guides/ pages. /guides/ IS linked from the BaseLayout footer nav and mobile
  nav. Despite this, GSC data shows 0 impressions for the /guides/ pattern. These are
  likely new pages not yet indexed.
proposed_change: |
  Add a "Guides" section to the homepage between the terminal reviews section and the footer.
  Brief card-style grid with links to the 7 guide pages:
  - How to choose a card machine
  - Card machine costs explained
  - How to switch card machine providers
  - etc.

  Also: check that the /guides/ index page exists and renders all 7 children (some guide
  indexes are auto-generated and may miss new slugs if the template isn't updated).
why: |
  Homepage-level links carry more PageRank than footer links. If /guides/ only gets
  footer-level links, the 7 pages beneath it may rank poorly because the crawl signal
  is weak. A section on the homepage takes 15 minutes to add and would send a much
  stronger signal to Google that these pages are important content.
---
