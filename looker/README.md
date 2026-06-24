# Fleet Looker Studio + BigQuery — setup

The hybrid traffic/search layer (alongside the custom fleet dashboard). GA4 + GSC
export to BigQuery; `fleet_views.sql` cleans them into one per-site-per-day table;
Looker Studio charts it. Built 24 Jun 2026.

## Status / prerequisites
1. ✅ GA4 properties exist for all 17 fleet sites (created 24 Jun).
2. ⏳ **GA4 → BigQuery** export linked per property (PeptideClear done; link the rest:
   GA4 Admin → Product links → BigQuery links → project **rank4ai** → EU → Daily).
3. ⏳ **GSC → BigQuery** bulk export (Search Console → Settings → Bulk data export →
   project **rank4ai** → dataset `searchconsole`). Per property; money sites first.
4. Each GA4 link auto-creates a dataset `analytics_<propertyId>`; first daily export
   lands **~24h after linking** (no backfill — forward only).

## Apply the SQL (once data is flowing)
1. In BigQuery (project **rank4ai**), create a dataset **`fleet_analytics`** (location: EU).
2. Open `fleet_views.sql`, replace every `${PROJECT}` with the rank4ai project id
   (BigQuery → project dropdown → the id string, e.g. `rank4ai-xxxxxx`).
3. **Comment out any site whose GA4→BQ link hasn't run yet** (its `analytics_<id>`
   dataset won't exist → the UNION errors). Uncomment as each link goes live.
4. Run the file. It builds 3 views: `ga4_daily`, `gsc_daily`, and **`fleet_daily`**
   (the joined one Looker uses: real_visits=GA4 sessions, google_clicks/impressions/
   position from GSC, per site, per day, tagged by category lead-gen/banner/health).

## Build the Looker Studio report
1. lookerstudio.google.com → Create → Data source → **BigQuery** → project rank4ai →
   `fleet_analytics` → **`fleet_daily`**.
2. Suggested pages (mirrors the custom board):
   - **Fleet overview** — scorecards: total real_visits (30d), google_clicks, google_impressions;
     time-series of real_visits by category (lead-gen/banner/health).
   - **Per-site** — table: site · real_visits · google_clicks · impressions · avg_position,
     with a date-range control + a category filter.
   - **Search** — impressions→clicks→position trend per site.
3. Definitions match the custom dashboard so numbers reconcile: **real_visits = GA4
   sessions** (the honest traffic number, NOT the old bot-inflated fleet_bot_hits).

## Notes
- This complements, does not replace, the custom board (which keeps leads / AI-citations
  / audits — those live in Supabase, not BigQuery).
- Indexed-vs-actual pages: comes from the GSC URL export (view #4, stubbed in the SQL) —
  finish it once `searchdata_url_impression` is populated.
