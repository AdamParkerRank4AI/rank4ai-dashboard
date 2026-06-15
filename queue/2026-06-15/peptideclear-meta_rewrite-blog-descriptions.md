---
status: draft
site: peptideclear
type: meta_rewrite
target_query: "(multiple blog posts)"
target_url: /blog/*
current_state: "9 blog pages flagged by daily audit (2026-06-10) with meta descs 161-184 chars"
proposed_change: "Trim each description to under 150 chars. Proposed values below."
why: >
  Daily audit (2026-06-10) flagged 9 PeptideClear blog pages for meta
  descriptions over 160 chars. Current source frontmatter descriptions are
  138-159 chars, suggesting partial cleanup already happened. Pages at 155-159
  chars are borderline and worth trimming to give a comfortable buffer. Pages
  at 138-152 chars in source may be fine now and only need a fresh audit to
  confirm.
---

## Audit context

The 2026-06-10 audit found these pages over 160 chars (from the live site).
Current source file lengths are lower, suggesting some pages were updated
after the audit. A fresh audit after any deploys will confirm which are
still flagged.

## Pages and proposed descriptions

### /blog/best-nad-supplement-uk/ (source: 159 chars, audit: 182)

Current:
```
Editorial checklist for choosing an NAD+ supplement in the UK: precursor type, third-party testing and UK food-supplement claims rules. No product endorsement.
```

Proposed (136 chars):
```
Choosing an NAD+ supplement in the UK: what to look for on a label. Precursor type, third-party testing and UK food-supplement claims rules.
```

---

### /blog/nad-iv-drip-uk/ (source: 159 chars, audit: 161)

Current:
```
How IV NAD+ works in the UK, where it is offered, what a session involves, and the regulatory and evidence questions to ask before booking. No clinical claims.
```

Proposed (138 chars):
```
How IV NAD+ works in the UK: where it is offered, what a session involves, and the regulatory and evidence questions to ask before booking.
```

---

### /blog/nad-supplement-uk/ (source: 156 chars, audit: 161)

Current:
```
Oral NAD+, NMN and NR explained for UK readers. Why intact NAD+ is poorly absorbed, what the precursor options are, and what to check on a supplement label.
```

Proposed (137 chars):
```
Oral NAD+, NMN and NR for UK readers: why intact NAD+ is poorly absorbed, which precursor options exist, and what to check on a supplement label.
```

---

### /blog/longevity-supplements-uk/ (source: 150 chars, audit: 184)

Current:
```
Editorial map of the UK longevity supplement landscape: NAD+ precursors, how these products are regulated, and why evidence runs behind the marketing.
```

Source is 150 chars (fine). If live site still shows 184, a deploy is needed.
No change to source required unless fresh audit confirms live is still over.

---

### /blog/nad-cost-uk/ (source: 152 chars, audit: 166)

Current:
```
What NAD+ costs in the UK across IV drips, injections and oral supplements. How the price ladder works and why routes are not comparable on price alone.
```

Source is 152 chars (fine). Same note as above.

---

### /blog/iv-drip-uk/ (source: 145 chars, audit: 166)

Source is 145 chars (fine). If live still shows 166, deploy is needed.

---

### /blog/iv-drip-vs-supplement/ (source: 138 chars, audit: 169)

Source is 138 chars (fine). If live still shows 169, deploy is needed.

---

### /blog/best-nmn-supplement-uk/ (source: 138 chars, audit: 172)

Source is 138 chars (fine). Deploy may be needed.

---

### /blog/nad-side-effects-uk/ (source: 148 chars, audit: 172)

Current:
```
What published studies note about NAD+ tolerability across IV, injection and oral precursor routes, with the limits of that evidence clearly stated.
```

Source is 148 chars (fine). Deploy may be needed.

---

## Action

1. Trim the three borderline source descriptions above (best-nad, nad-iv-drip, nad-supplement).
2. Run a fresh audit after the next deploy to confirm all 9 are now under 160.
3. The other 6 pages likely just need their already-shorter source descriptions
   to be live (CF Pages auto-deploys on push, so they should be fine if any
   push has gone to main since 2026-06-10).
