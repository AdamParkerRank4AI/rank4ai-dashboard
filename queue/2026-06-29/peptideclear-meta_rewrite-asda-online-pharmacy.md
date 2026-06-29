---
status: draft
site: peptideclear
type: meta_rewrite
target_query: asda online pharmacy
target_url: /pharmacies/
current_state: |
  Title: "UK GLP-1 Pharmacies: Wegovy and Mounjaro Online | PeptideClear"
  Meta: auto-generated ~190 chars, truncates in SERPs.
  Position: 18.0, impressions: 111, clicks: 0, CTR: 0%
  The /pharmacies/ page lists UK GPhC-registered pharmacies (Phlo, Pharmacy2U,
  SimplyMeds, Boots Online Doctor, Asda Online Doctor) for GLP-1 prescription routes.
  Asda Online Doctor is mentioned in the directory listing.
proposed_change: |
  Title (no change — well-structured):
  "UK GLP-1 Pharmacies: Wegovy and Mounjaro Online | PeptideClear"

  Meta (new — 153 chars):
  "Compare UK online pharmacies for GLP-1 weight-loss prescriptions including Asda Online Doctor, Boots, Phlo and Pharmacy2U. GPhC-registered, editorial review."

  Implementation: find the meta description prop in
  src/pages/pharmacies/index.astro and replace with the new string above.
  (Do NOT add a clinical recommendation — editorial directory framing only.)
why: |
  "asda online pharmacy" gets 111 impressions at position 18.0 with 0 clicks.
  This is a branded navigational query from patients who want to access Asda's
  GLP-1 online prescription service. PeptideClear's /pharmacies/ page already covers
  Asda Online Doctor in its directory, so the site is legitimately ranking — it just
  isn't winning the click because the meta doesn't mention Asda by name.
  Adding "Asda Online Doctor" explicitly to the meta description directly matches
  the search intent. At 111 impressions on a new site, this could deliver 5-10 clicks
  per month from a single meta edit.
  Key compliance note: keep framing as "editorial directory comparison", not a
  recommendation of Asda for any specific person's treatment.
---
