---
status: draft
site: ukmetabolic
type: internal_link
target_query: "peptide questions UK"
target_url: /questions/
current_state: /questions/ is a confirmed orphan (2026-06-05 crawl). No inbound internal links. Page exists and builds, just invisible to crawlers following links.
proposed_change: |
  Add a "Questions & answers" card to the PeptideClear homepage hub section.
  Also add a text link in the /glossary/ page intro prose: "...or browse the
  questions archive for reader-submitted queries."

  Minimum fix (one line in homepage):
    <a href="/questions/" class="block rounded-xl border ...">
      <p class="font-bold text-brand mb-2">Questions answered</p>
      <p class="text-xs text-slate-500">Reader Q&A on UK peptides, collagen, GLP-1 eligibility, and research-use framing.</p>
    </a>

why: >
  /questions/ had 0 inbound links in the 2026-06-05 crawl. Google cannot
  discover or index it via standard crawl. This is a single-line fix on the
  homepage cards section. Fixes the orphan, adds a second topical hub signal
  to the homepage, and is safe to push to main with no build risk.

author: Oliver Mackman
---
