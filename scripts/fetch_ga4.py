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
    RunReportRequest, DateRange, Metric, Dimension, OrderBy
)

TOKEN_FILE = os.path.expanduser('~/rank4ai-dashboard/scripts/ga4_token.json')
OUTPUT_DIR = os.path.expanduser('~/rank4ai-dashboard/src/data/live')

PROPERTIES = {
    "rank4ai": "526657151",
    "market-invoice": "531285218",
    "seocompare": "532266658",
}


def get_creds():
    with open(TOKEN_FILE) as f:
        token_data = json.load(f)
    return Credentials(
        token=token_data['token'],
        refresh_token=token_data['refresh_token'],
        token_uri=token_data['token_uri'],
        client_id=token_data['client_id'],
        client_secret=token_data['client_secret'],
        scopes=token_data.get('scopes', []),
    )


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

    overview_data = {}
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
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    creds = get_creds()
    client = BetaAnalyticsDataClient(credentials=creds)

    all_data = {}
    for site_id, property_id in PROPERTIES.items():
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
