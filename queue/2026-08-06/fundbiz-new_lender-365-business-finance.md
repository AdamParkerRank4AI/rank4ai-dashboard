---
status: draft
site: fundbiz
type: new_lender
target_query: 365 business finance
target_url: https://www.fundbiz.co.uk/lenders/365-business-finance/
current_state: |
  No page exists. The query "365 business finance" currently ranks at position 19.1
  (page 2) with 150 impressions and 0 clicks — entirely from incidental proximity
  on existing pages.
proposed_change: |
  Add a new entry to src/data/lenders.ts for 365 Business Finance, which auto-generates
  /lenders/365-business-finance/ via the existing [slug].astro route.

  Suggested lenders.ts entry:
  {
    slug: "365-business-finance",
    name: "365 Business Finance",
    legalName: "365 Business Finance Ltd",
    companyNumber: "07122125",
    founded: "2010",
    foundedYear: 2010,
    url: "https://365businessfinance.co.uk",
    productType: "Merchant Cash Advance",
    ticketRange: "£10,000 to £400,000",
    typicalRate: "1.12 to 1.20 factor rate",
    decisionTime: "24 hours",
    softSearchOnly: true,
    ltdOnly: true,
    fcaRegulated: false,
    ratingOverall: 3.8,
    ratingTransparency: 3.5,
    ratingEligibility: 4.0,
    ratingSpeed: 4.5,
    ratingDecline: 3.5,
    ratingTrustpilot: 4.2,
    ratingTrustpilotN: 600,
    summary: "365 Business Finance is a UK merchant cash advance provider that funds SMEs
    based on projected card turnover rather than credit history. It is aimed at
    businesses with a minimum of six months of card processing, and repayments are
    collected as a fixed percentage of daily card sales rather than fixed monthly
    instalments. This makes repayment flexible when revenue fluctuates.",
    pros: [
      "No fixed monthly repayments: payment scales with card revenue",
      "Funds to £400,000 for established businesses",
      "Soft credit check at application stage",
      "Suitable for businesses declined by traditional lenders"
    ],
    cons: [
      "MCA factor rate (1.12+) can be more expensive than a term loan",
      "Requires minimum 6 months card processing history",
      "Limited companies and LLPs only (no sole traders)",
      "Not FCA regulated — no FOS recourse"
    ],
    bestFor: [
      "Hospitality and retail with high card turnover",
      "Businesses declined elsewhere due to adverse credit",
      "SMEs that need flexibility on repayment timing"
    ],
    weakAt: [
      "Cash-heavy businesses with low card processing volumes",
      "Businesses wanting fixed monthly costs",
      "Sole traders and partnerships under 4"
    ],
    lastReviewed: "2026-08-06"
  }

  VERIFY BEFORE SHIPPING: confirm Companies House number 07122125 belongs to
  365 Business Finance Ltd (check companieshouse.gov.uk). Adjust ratings and
  Trustpilot count to actual current data.
why: >
  "365 business finance" has 150 impressions at position 19.1 with 0 clicks.
  There is no dedicated page on fundbiz for this lender. The impressions are
  coming from passing mentions on other pages. A dedicated lender review page
  at /lenders/365-business-finance/ with the title "365 Business Finance Review
  2026" would immediately serve this brand-lookup intent and realistically
  move from position 19 to position 5-10.

  365 Business Finance is a natural fit for fundbiz: it is MCA-focused, aimed
  at Ltd/LLP businesses, and well-suited to post-decline applicants — exactly
  the positioning fundbiz is building for. Adding it also strengthens the MCA
  section's breadth (complementary to iwoca, Aldermore etc).

  Companion queries in the data to watch:
  - "365 merchant cash advance" — 34 impressions, pos 17.4
  - "aldermore commercial mortgages" — 75 impressions, pos 18.2 (separate page needed)

  Both will benefit once a dedicated lender section is stronger. Prioritise
  365 Business Finance first (highest impression count of the two).
---
