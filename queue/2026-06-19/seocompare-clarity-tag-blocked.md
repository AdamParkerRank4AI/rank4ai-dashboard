---
status: draft
site: seocompare
type: meta_rewrite
target_query: N/A (infrastructure)
target_url: /
current_state: |
  SEOCompare has CLARITY_ID='' (empty string) in BaseLayout.astro:42.
  Fleet baseline check: clarity_firing=false (Clarity missing).
  This has been open since at least 2026-06-10 per FLEET_INBOX.
  GA4 is firing fine; only Clarity is missing.
proposed_change: |
  ADAM ACTION (2 minutes):
  1. Go to clarity.microsoft.com → SEOCompare project → Setup → Get code
  2. Copy the 10-character project ID (e.g. "abc1234xyz")
  3. Paste it into ~/compareaiseo/src/layouts/BaseLayout.astro where CLARITY_ID=''
  4. Push to main → auto-deploy fires

  Alternatively, message me the ID and I'll wire it in.
why: |
  Clarity gives session recordings and heatmaps. Without it, there's zero visibility
  into how visitors interact with the comparison pages. Given SEOCompare's high bounce
  rate (87.3%), Clarity data is particularly valuable for diagnosing drop-off points.
  This is the simplest outstanding fix on the entire fleet.
---
