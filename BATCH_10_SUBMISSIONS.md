# Batch 10 — Awesome-list + directory submissions (manual, ~30 min)

External entity-corroboration submissions. Each is a GitHub PR or Product Hunt launch you have to do under your account — I've prepped the exact content to paste so you don't have to draft anything.

Estimated time: 30-40 minutes total. Each PR is a 2-line addition.

---

## 1 · llmstxt.directory — Pydantic-maintained registry (3 entries)

**URL:** https://github.com/PydanticAI/llmstxt-directory (or current canonical — check the README)

**Action:** open a PR adding all 3 sites at once. Edit `data/sites.yaml` (or whatever data file the registry uses) and add:

```yaml
- name: Rank4AI
  url: https://www.rank4ai.co.uk
  llmstxt: https://www.rank4ai.co.uk/llms.txt
  llmsfull: https://www.rank4ai.co.uk/llms-full.txt
  category: ai-search-agency
  description: UK AI search agency that helps businesses get recommended by ChatGPT, Claude, Gemini, Perplexity, Copilot and Google AI.

- name: Market Invoice
  url: https://marketinvoice.co.uk
  llmstxt: https://marketinvoice.co.uk/llms.txt
  llmsfull: https://marketinvoice.co.uk/llms-full.txt
  category: finance-comparison
  description: UK's whole of market invoice finance comparison — 85 verified factoring and discounting providers.

- name: SEOCompare
  url: https://seocompare.co.uk
  llmstxt: https://seocompare.co.uk/llms.txt
  llmsfull: https://seocompare.co.uk/llms-full.txt
  category: seo-agency-comparison
  description: UK's independent comparison of AI search optimisation agencies and tools — ChatGPT, Gemini, Perplexity, AI Overviews visibility.
```

PR title: `Add Rank4AI, Market Invoice, SEOCompare`
PR body: `Adds 3 UK sites with llms.txt + llms-full.txt to the directory.`

---

## 2 · nichochar/open-llmstxt — same content, different repo

**URL:** https://github.com/nichochar/open-llmstxt

Same 3 entries, format adapted to whatever `data/` schema that repo uses. Check the README for the contribution format.

---

## 3 · awesome-llms-txt (community-maintained list)

**URL:** https://github.com/elder-plinius/awesome-llms-txt (or current canonical)

Edit `README.md` and add 3 lines under the appropriate section (likely "Companies" or "Examples"):

```markdown
- [Rank4AI](https://www.rank4ai.co.uk/llms.txt) — UK AI search agency
- [Market Invoice](https://marketinvoice.co.uk/llms.txt) — UK invoice finance comparison
- [SEOCompare](https://seocompare.co.uk/llms.txt) — UK AI search agency comparison directory
```

---

## 4 · awesome-generative-engine-optimization (Rank4AI as GEO agency)

**URL:** https://github.com/sindresorhus/awesome (or the topic-specific GEO list — search github.com for "awesome-generative-engine-optimization")

Add under "Agencies" section in README:

```markdown
- [Rank4AI](https://www.rank4ai.co.uk) — UK AI search agency. Five Signal Model framework covering Identity Clarity, Subject Authority, Meaning Architecture, Ecosystem Validation, Signal Consistency. 1,400+ UK business audits.
```

---

## 5 · awesome-generative-engine-optimization (SEOCompare as comparison tool)

Same repo as #4. Add under "Tools" or "Directories" section:

```markdown
- [SEOCompare](https://seocompare.co.uk) — UK independent comparison of AI search optimisation agencies and tools. 115+ agencies rated on 12 criteria including ChatGPT / Gemini / Perplexity / AI Overviews coverage.
```

---

## 6 · Product Hunt — Rank4AI agency launch

**URL:** https://www.producthunt.com/posts/new

**Title:** Rank4AI · UK AI Search Agency
**Tagline:** Get your business recommended by ChatGPT, Claude, Gemini, Perplexity, Copilot and Google AI
**Topics:** AI · SEO · Marketing
**Pricing:** Paid
**Launch URL:** https://www.rank4ai.co.uk
**Pitch (in the description box):**
```
Rank4AI is a UK AI search agency that helps businesses get recommended when buyers ask ChatGPT, Claude, Gemini, Perplexity, Copilot or Google AI for a recommendation in their category.

We use the Five Signal Model — a framework for AI search visibility built from 1,400+ UK business audits across all six major AI platforms. The five signals: Identity Clarity, Subject Authority, Meaning Architecture, Ecosystem Validation, Signal Consistency.

What's different:
- AI search exclusively (no SEO retainers, no PPC)
- UK-only focus
- Free AI Search Visibility Audit at https://www.rank4ai.co.uk/free-audit/
```

**Maker comment (post on launch day):**
```
We started Rank4AI after watching one or two businesses dominate AI recommendations while everyone else became invisible. Traditional SEO didn't predict it. Six AI platforms, five signal layers, and a lot of audit data later, this is what we found out about AI search visibility for UK businesses.
```

---

## 7 · Product Hunt — SEOCompare matcher tool launch

**Title:** SEOCompare · Compare AI Search Agencies
**Tagline:** Independent UK comparison of 115+ AI search optimisation agencies
**Topics:** SEO · AI · Marketing · Business
**Pricing:** Free
**Launch URL:** https://seocompare.co.uk

**Pitch:**
```
SEOCompare is the UK's independent comparison of AI search optimisation agencies and tools — for businesses choosing a partner for ChatGPT, Gemini, Perplexity, and AI Overviews visibility.

115+ agencies rated on 12 criteria: platform coverage, methodology, pricing clarity, case studies, schema expertise, content strategy, technical AI SEO, client communication, contract terms, geographic reach, industry focus, innovation. Updated monthly.

Try the agency matcher: https://seocompare.co.uk/agency-matcher/
```

---

## Order to do them in

1. Product Hunt R4 + SC first — launch days are time-sensitive (best Tuesday/Wednesday morning UK time for upvote momentum)
2. awesome-llms-txt + llmstxt.directory + open-llmstxt next — these are passive citation harvesting
3. awesome-generative-engine-optimization last — only relevant if list is active

---

## Tracking

After each submission lands, mark it on the master CHANGELOG (`iCloud/claude/astro/plan/CHANGELOG.md`) with:
- Site
- Submission target
- PR URL or Product Hunt launch URL
- Date

That makes the next entity-coherence run pick up the new sameAs candidates if you add the listing URL to `Organization.sameAs` in each site's schema.
