-- ============================================================================
-- FLEET ANALYTICS — BigQuery transformation for Looker Studio
-- Run once GA4->BQ + GSC->BQ exports are flowing (data lands ~24h after linking).
-- Replace ${PROJECT} with your BigQuery project id (the 'rank4ai' project you
-- linked GA4 to). Each GA4 property exports to its own dataset analytics_<id>.
-- The GSC bulk export lands in a 'searchconsole' dataset keyed by site_url.
-- ============================================================================

-- 1) GA4 daily sessions/users per site (UNION across the 17 property datasets).
--    A property dataset only exists once that site's GA4->BQ link has run, so
--    comment out any site you haven't linked yet or it errors on a missing table.
CREATE OR REPLACE VIEW `${PROJECT}.fleet_analytics.ga4_daily` AS
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'MarketInvoice' AS site, 'marketinvoice.co.uk' AS domain, 'lead-gen' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_531285218.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'Best Business Loans' AS site, 'bestbusinessloans.ai' AS domain, 'lead-gen' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_538202642.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'FundBiz' AS site, 'fundbiz.co.uk' AS domain, 'lead-gen' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_538211877.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'MerchantHQ' AS site, 'merchanthq.co.uk' AS domain, 'lead-gen' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_538211285.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'Kartapay' AS site, 'kartapay.co.uk' AS domain, 'lead-gen' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_538191589.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'LTD Turnaround' AS site, 'ltdturnaround.co.uk' AS domain, 'lead-gen' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_543028960.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'Later Life Borrowing' AS site, 'laterlifeborrowing.co.uk' AS domain, 'lead-gen' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_543036235.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'VettedHome' AS site, 'vettedhome.co.uk' AS domain, 'lead-gen' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_543009885.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'Homes and Hedge' AS site, 'homesandhedge.co.uk' AS domain, 'banner' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_543067090.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'FitCalcs' AS site, 'fitcalcs.co.uk' AS domain, 'banner' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_542994782.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'BabyData' AS site, 'babydata.co.uk' AS domain, 'banner' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_543102438.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'Dates and Times' AS site, 'datesandtimes.co.uk' AS domain, 'banner' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_543047906.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'PeptideClear' AS site, 'peptideclear.co.uk' AS domain, 'health' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_538285241.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'ADHD Helper' AS site, 'adhdhelper.co.uk' AS domain, 'health' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_543011387.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'HerVitals' AS site, 'hervitals.co.uk' AS domain, 'health' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_543081822.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'SEO Compare' AS site, 'seocompare.co.uk' AS domain, 'seo-other' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_532266658.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date
UNION ALL
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    'Rank4AI' AS site, 'rank4ai.co.uk' AS domain, 'seo-other' AS category,
    COUNT(DISTINCT CONCAT(user_pseudo_id, CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') AS STRING))) AS sessions,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM `${PROJECT}.analytics_526657151.events_*`
  WHERE _TABLE_SUFFIX NOT LIKE 'intraday_%'
  GROUP BY event_date;

-- 2) GSC daily clicks/impressions/position per site (one export, filter by url).
CREATE OR REPLACE VIEW `${PROJECT}.fleet_analytics.gsc_daily` AS
SELECT
  data_date AS date,
  REGEXP_REPLACE(REGEXP_REPLACE(site_url,'^https?://',''),'/$','') AS domain,
  SUM(clicks) AS clicks,
  SUM(impressions) AS impressions,
  SAFE_DIVIDE(SUM(sum_top_position), SUM(impressions)) + 1 AS avg_position
FROM `${PROJECT}.searchconsole.searchdata_site_impression`
GROUP BY date, domain;

-- 3) THE table Looker connects to — GA4 (real visits) + GSC (search), per site/day.
CREATE OR REPLACE VIEW `${PROJECT}.fleet_analytics.fleet_daily` AS
SELECT
  COALESCE(g.date, s.date) AS date,
  g.site, g.category,
  COALESCE(g.domain, s.domain) AS domain,
  g.sessions AS real_visits,      -- GA4 sessions = the honest traffic number
  g.users,
  s.clicks AS google_clicks,
  s.impressions AS google_impressions,
  ROUND(s.avg_position,1) AS google_avg_position
FROM `${PROJECT}.fleet_analytics.ga4_daily` g
FULL OUTER JOIN `${PROJECT}.fleet_analytics.gsc_daily` s
  ON g.domain = s.domain AND g.date = s.date;

-- 4) (optional) Index coverage per site from the GSC URL export — for indexed-vs-actual.
-- CREATE OR REPLACE VIEW `${PROJECT}.fleet_analytics.gsc_index` AS
-- SELECT REGEXP_REPLACE(REGEXP_REPLACE(site_url,'^https?://',''),'/$','') AS domain,
--   COUNTIF(is_anonymized_discover=false) AS rows  -- placeholder; real index status
-- FROM `${PROJECT}.searchconsole.searchdata_url_impression` GROUP BY domain;
