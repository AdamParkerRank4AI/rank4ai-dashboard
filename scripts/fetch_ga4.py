#!/usr/bin/env python3
"""
Fetch GA4 analytics data for dashboard.
"""
import json
import os
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Metric, Dimension, OrderBy,
    Filter, FilterExpression, FilterExpressionList,
)

# Per-handover: AI Assistant channel surfaces directly in GA4 since May 2026.
# We also break out by sessionSource for explicit attribution.
AI_HOSTS = [
    "perplexity.ai",
    "chat.openai.com",
    "chatgpt.com",
    "gemini.google.com",
    "bard.google.com",
    "claude.ai",
    "copilot.microsoft.com",
    "you.com",
    "phind.com",
]

TOKEN_FILE = os.path.expanduser('~/rank4ai-dashboard/scripts/ga4_token.json')
OUTPUT_DIR = os.path.expanduser('~/rank4ai-dashboard/src/data/live')

PROPERTIES = {
    "rank4ai": "526657151",
    "market-invoice": "531285218",
    "seocompare": "532266658",
    "cardmachines": "537291192",        # AcceptCard, G-9Q5QGGE1ZP
    "bestbusinessloans": "538202642",   # G-P7G336KY9C
    "fundbiz": "538211877",             # G-9L5BSC5H1R
    "kartapay": "538191589",            # karta12 account
    "peptideclear": "538285241",        # peptidesa account
    # builderweb: no GA4 property yet (20 May 2026). Add when Oliver wires it.
}


def get_creds():
    with open(TOKEN_FILE) as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data['token'],
        refresh_token=token_data['refresh_token'],
        token_uri=token_data['token_uri'],
        client_id=token_data['client_id'],
        client_secret=token_data['client_secret'],
        scopes=token_data.get('scopes', []),
    )
    # Always force refresh — token often reports valid but returns 401
    from google.auth.transport.requests import Request
    try:
        creds.refresh(Request())
        token_data['token'] = creds.token
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)
    except Exception as e:
        print(f"  Token refresh failed: {e}")
    return creds


def fetch_property(client, property_id, site_id):
    prop = f"properties/{property_id}"

    # Last 30 days overview
    overview = client.run_report(RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
            Metric(name="screenPageViews"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
        ],
    ))

    overview_data = {
        "active_users": 0,
        "sessions": 0,
        "pageviews": 0,
        "bounce_rate": 0.0,
        "avg_session_duration": 0.0,
    }
    if overview.rows:
        row = overview.rows[0]
        overview_data = {
            "active_users": int(row.metric_values[0].value),
            "sessions": int(row.metric_values[1].value),
            "pageviews": int(row.metric_values[2].value),
            "bounce_rate": round(float(row.metric_values[3].value) * 100, 1),
            "avg_session_duration": round(float(row.metric_values[4].value), 1),
        }

    # Top pages
    pages_report = client.run_report(RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        dimensions=[Dimension(name="pagePath")],
        metrics=[
            Metric(name="screenPageViews"),
            Metric(name="activeUsers"),
        ],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)],
        limit=20,
    ))

    top_pages = []
    for row in pages_report.rows:
        top_pages.append({
            "path": row.dimension_values[0].value,
            "pageviews": int(row.metric_values[0].value),
            "users": int(row.metric_values[1].value),
        })

    # Traffic sources
    sources_report = client.run_report(RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="activeUsers"),
        ],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
        limit=10,
    ))

    sources = []
    for row in sources_report.rows:
        sources.append({
            "channel": row.dimension_values[0].value,
            "sessions": int(row.metric_values[0].value),
            "users": int(row.metric_values[1].value),
        })

    # Daily traffic (last 30 days)
    daily_report = client.run_report(RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        dimensions=[Dimension(name="date")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
        ],
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))],
    ))

    daily = []
    for row in daily_report.rows:
        daily.append({
            "date": row.dimension_values[0].value,
            "users": int(row.metric_values[0].value),
            "sessions": int(row.metric_values[1].value),
        })

    # Countries
    countries_report = client.run_report(RunReportRequest(
        property=prop,
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        dimensions=[Dimension(name="country")],
        metrics=[Metric(name="activeUsers")],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)],
        limit=10,
    ))

    countries = []
    for row in countries_report.rows:
        countries.append({
            "country": row.dimension_values[0].value,
            "users": int(row.metric_values[0].value),
        })

    # --- AI traffic (new May 2026 GA4 capability) ---
    # 1. AI Assistant channel total (last 7d + prior 7d for delta)
    def ai_channel_count(start, end):
        try:
            r = client.run_report(RunReportRequest(
                property=prop,
                date_ranges=[DateRange(start_date=start, end_date=end)],
                dimensions=[Dimension(name="sessionDefaultChannelGroup")],
                metrics=[Metric(name="sessions"), Metric(name="activeUsers")],
            ))
            for row in r.rows:
                ch = row.dimension_values[0].value
                if ch == "AI Assistant" or ch == "AI Search":
                    return {
                        "channel_label": ch,
                        "sessions": int(row.metric_values[0].value),
                        "users": int(row.metric_values[1].value),
                    }
        except Exception as e:
            return {"channel_label": None, "sessions": 0, "users": 0, "error": str(e)}
        return {"channel_label": None, "sessions": 0, "users": 0}

    ai_7d = ai_channel_count("7daysAgo", "today")
    ai_prior_7d = ai_channel_count("14daysAgo", "8daysAgo")
    delta_pct = None
    if ai_prior_7d.get("sessions", 0) > 0:
        delta_pct = round(
            (ai_7d.get("sessions", 0) - ai_prior_7d.get("sessions", 0))
            / ai_prior_7d.get("sessions", 1) * 100, 1
        )

    # 2. AI source breakdown (sessionSource matches AI hosts) — last 30 days
    ai_sources = []
    try:
        ai_src_report = client.run_report(RunReportRequest(
            property=prop,
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
            dimensions=[Dimension(name="sessionSource")],
            metrics=[Metric(name="sessions"), Metric(name="activeUsers")],
            dimension_filter=FilterExpression(
                or_group=FilterExpressionList(expressions=[
                    FilterExpression(filter=Filter(
                        field_name="sessionSource",
                        string_filter=Filter.StringFilter(
                            match_type=Filter.StringFilter.MatchType.CONTAINS,
                            value=host,
                            case_sensitive=False,
                        ),
                    )) for host in AI_HOSTS
                ]),
            ),
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=15,
        ))
        for row in ai_src_report.rows:
            ai_sources.append({
                "source": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
            })
    except Exception as e:
        ai_sources = [{"error": str(e)}]

    # 3. Top landing pages — filtered to AI Assistant channel (last 30 days)
    top_ai_landing = []
    try:
        ai_landing_report = client.run_report(RunReportRequest(
            property=prop,
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
            dimensions=[Dimension(name="landingPagePlusQueryString")],
            metrics=[Metric(name="sessions"), Metric(name="activeUsers")],
            dimension_filter=FilterExpression(filter=Filter(
                field_name="sessionDefaultChannelGroup",
                string_filter=Filter.StringFilter(
                    match_type=Filter.StringFilter.MatchType.CONTAINS,
                    value="AI",
                    case_sensitive=False,
                ),
            )),
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=10,
        ))
        for row in ai_landing_report.rows:
            top_ai_landing.append({
                "path": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
            })
    except Exception as e:
        top_ai_landing = [{"error": str(e)}]

    return {
        "site_id": site_id,
        "property_id": property_id,
        "fetched_at": datetime.now().isoformat(),
        "period": "last_30_days",
        "overview": overview_data,
        "top_pages": top_pages,
        "sources": sources,
        "daily": daily,
        "countries": countries,
        "ai_assistant": {
            "last_7d": ai_7d,
            "prior_7d": ai_prior_7d,
            "delta_pct": delta_pct,
            "sources_30d": ai_sources,
            "top_landing_pages_30d": top_ai_landing,
        },
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    creds = get_creds()
    client = BetaAnalyticsDataClient(credentials=creds)

    all_data = {}
    for site_id, property_id in PROPERTIES.items():
        if not property_id:
            print(f"Skipping GA4 data for {site_id} (no property ID set yet).")
            continue
        print(f"Fetching GA4 data for {site_id} (property {property_id})...")
        try:
            data = fetch_property(client, property_id, site_id)
            all_data[site_id] = data
            print(f"  Users: {data['overview'].get('active_users', 0)}")
            print(f"  Sessions: {data['overview'].get('sessions', 0)}")
            print(f"  Pageviews: {data['overview'].get('pageviews', 0)}")
        except Exception as e:
            print(f"  Error: {e}")

    output_file = os.path.join(OUTPUT_DIR, "ga4.json")
    with open(output_file, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
