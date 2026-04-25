#!/usr/bin/env python3
"""
Fetch Google Trends data for all clients.
Tracks brand search volume trends and keyword interest over time.
Uses PyTrends (unofficial Google Trends API).

Brand search volume has 0.334 correlation with AI citations — leading indicator.
"""
import json
import os
import time
from datetime import datetime

from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")
OUTPUT = os.path.join(OUTPUT_DIR, "google_trends.json")

# Keywords to track per client
# First keyword is always the brand name (for brand search volume tracking)
CLIENTS = {
    "rank4ai": {
        "brand": "rank4ai",
        "keywords": [
            "ai search visibility",
            "ai seo agency",
            "chatgpt seo",
            "generative engine optimization",
            "ai search optimization",
        ],
    },
    "market-invoice": {
        "brand": "invoice finance",
        "keywords": [
            "invoice factoring",
            "invoice finance UK",
            "business cash flow",
            "trade finance",
            "asset based lending",
        ],
    },
    "seocompare": {
        "brand": "seo agency comparison",
        "keywords": [
            "best seo agency UK",
            "compare seo agencies",
            "ai seo tools",
            "seo agency reviews",
            "geo agency",
        ],
    },
}


def fetch_with_retry(func, max_retries=3):
    """Retry with exponential backoff on rate limit."""
    for attempt in range(max_retries):
        try:
            return func()
        except TooManyRequestsError:
            wait = 60 * (attempt + 1)
            print(f"    Rate limited, waiting {wait}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(wait)
        except Exception as e:
            print(f"    Error: {e}")
            return None
    print(f"    Failed after {max_retries} retries")
    return None


def fetch_interest_over_time(pytrends, keywords, timeframe="today 3-m", geo="GB"):
    """Fetch interest over time for a list of keywords."""
    def _fetch():
        pytrends.build_payload(keywords[:5], cat=0, timeframe=timeframe, geo=geo)
        df = pytrends.interest_over_time()
        if df.empty:
            return []
        result = []
        for date, row in df.iterrows():
            entry = {"date": date.strftime("%Y-%m-%d")}
            for kw in keywords[:5]:
                if kw in row:
                    entry[kw] = int(row[kw])
            result.append(entry)
        return result

    return fetch_with_retry(_fetch) or []


def fetch_related_queries(pytrends, keyword, geo="GB"):
    """Fetch rising and top related queries for a keyword."""
    def _fetch():
        pytrends.build_payload([keyword], cat=0, timeframe="today 3-m", geo=geo)
        related = pytrends.related_queries()

        result = {"rising": [], "top": []}
        if keyword in related:
            rising = related[keyword].get("rising")
            top = related[keyword].get("top")

            if rising is not None and not rising.empty:
                for _, row in rising.head(10).iterrows():
                    result["rising"].append({
                        "query": row["query"],
                        "value": str(row["value"]),
                    })

            if top is not None and not top.empty:
                for _, row in top.head(10).iterrows():
                    result["top"].append({
                        "query": row["query"],
                        "value": int(row["value"]),
                    })
        return result

    return fetch_with_retry(_fetch) or {"rising": [], "top": []}


def main():
    print("Fetching Google Trends data...")
    pytrends = TrendReq(hl="en-GB", tz=0, retries=3, backoff_factor=1)

    all_data = {}

    for client_id, config in CLIENTS.items():
        print(f"\n  {client_id}:")
        brand = config["brand"]
        keywords = config["keywords"]

        client_data = {
            "fetched_at": datetime.now().isoformat(),
            "brand_keyword": brand,
            "keywords": keywords,
        }

        # 1. Brand search volume trend (3 months)
        print(f"    Brand trend: '{brand}'...")
        brand_trend = fetch_interest_over_time(pytrends, [brand], timeframe="today 3-m")
        client_data["brand_trend_3m"] = brand_trend
        if brand_trend:
            values = [d.get(brand, 0) for d in brand_trend]
            client_data["brand_current"] = values[-1] if values else 0
            client_data["brand_avg"] = round(sum(values) / len(values)) if values else 0
            # Trend direction
            if len(values) >= 4:
                first_quarter = sum(values[:len(values)//4]) / max(len(values)//4, 1)
                last_quarter = sum(values[-len(values)//4:]) / max(len(values)//4, 1)
                client_data["brand_direction"] = "rising" if last_quarter > first_quarter * 1.1 else "declining" if last_quarter < first_quarter * 0.9 else "stable"
            else:
                client_data["brand_direction"] = "insufficient_data"
            print(f"      Current: {client_data['brand_current']}, Avg: {client_data['brand_avg']}, Direction: {client_data['brand_direction']}")

        time.sleep(10)

        # 2. Keyword interest comparison (3 months)
        print(f"    Keyword comparison ({len(keywords)} terms)...")
        keyword_trend = fetch_interest_over_time(pytrends, keywords, timeframe="today 3-m")
        client_data["keyword_trends_3m"] = keyword_trend
        time.sleep(10)

        # 3. Rising queries for brand and top keyword
        print(f"    Rising queries for '{brand}'...")
        client_data["brand_related"] = fetch_related_queries(pytrends, brand)
        rising_count = len(client_data["brand_related"].get("rising", []))
        print(f"      {rising_count} rising queries found")
        time.sleep(10)

        if keywords:
            print(f"    Rising queries for '{keywords[0]}'...")
            client_data["keyword_related"] = fetch_related_queries(pytrends, keywords[0])
            rising_count = len(client_data["keyword_related"].get("rising", []))
            print(f"      {rising_count} rising queries found")
            time.sleep(10)

        # 4. Brand trend (12 months for longer view)
        print(f"    12-month brand trend...")
        brand_trend_12m = fetch_interest_over_time(pytrends, [brand], timeframe="today 12-m")
        client_data["brand_trend_12m"] = brand_trend_12m
        time.sleep(10)

        all_data[client_id] = client_data

    # Save
    with open(OUTPUT, "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"\nSaved → {OUTPUT}")


if __name__ == "__main__":
    main()
