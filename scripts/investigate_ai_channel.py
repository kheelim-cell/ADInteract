"""
investigate_ai_channel.py
--------------------------
ONE-OFF investigation script — not wired into any scheduled workflow.

Pulls the GA4 "AI Assistant" channel's session/engagement numbers and the
landing pages behind them, to find out what's already working before
changing anything. Prints JSON to stdout (read via the Actions run log) —
writes nothing to the repo, calls no write APIs.

Run via .github/workflows/investigate-ai-channel.yml (workflow_dispatch
only). Reuses the same credentials/property as fetch_growth_metrics.py.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from fetch_growth_metrics import _ga4_credentials, GA4_PROPERTY_ID  # noqa: E402

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest,
)


def main() -> None:
    client = BetaAnalyticsDataClient(credentials=_ga4_credentials())
    property_path = f"properties/{GA4_PROPERTY_ID}"
    date_range = DateRange(start_date="28daysAgo", end_date="today")

    # 1. Confirm channel grouping + exact source/medium values GA4 is bucketing
    #    as "AI Assistant" — don't assume the label, verify it.
    channels = client.run_report(RunReportRequest(
        property=property_path,
        date_ranges=[date_range],
        dimensions=[Dimension(name="sessionDefaultChannelGroup"),
                    Dimension(name="sessionSource"),
                    Dimension(name="sessionMedium")],
        metrics=[Metric(name="sessions"), Metric(name="engagementRate"),
                 Metric(name="averageSessionDuration"), Metric(name="engagedSessions")],
        order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        limit=25,
    ))
    channel_rows = [
        {
            "channel_group": r.dimension_values[0].value,
            "source": r.dimension_values[1].value,
            "medium": r.dimension_values[2].value,
            "sessions": int(r.metric_values[0].value),
            "engagement_rate": round(float(r.metric_values[1].value) * 100, 2),
            "avg_session_duration_sec": round(float(r.metric_values[2].value), 1),
            "engaged_sessions": int(r.metric_values[3].value),
        }
        for r in channels.rows
    ]

    # 2. Landing pages specifically behind the AI Assistant channel group.
    landing_pages = client.run_report(RunReportRequest(
        property=property_path,
        date_ranges=[date_range],
        dimensions=[Dimension(name="landingPagePlusQueryString"),
                    Dimension(name="sessionSource")],
        metrics=[Metric(name="sessions"), Metric(name="engagementRate"),
                 Metric(name="averageSessionDuration")],
        dimension_filter={
            "filter": {
                "field_name": "sessionDefaultChannelGroup",
                "string_filter": {"value": "AI Assistant", "match_type": "EXACT"},
            }
        },
        order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        limit=30,
    ))
    page_rows = [
        {
            "page": r.dimension_values[0].value,
            "source": r.dimension_values[1].value,
            "sessions": int(r.metric_values[0].value),
            "engagement_rate": round(float(r.metric_values[1].value) * 100, 2),
            "avg_session_duration_sec": round(float(r.metric_values[2].value), 1),
        }
        for r in landing_pages.rows
    ]

    print("=== ALL CHANNEL GROUPS (top 25 by sessions, 28d) ===")
    print(json.dumps(channel_rows, indent=2))
    print()
    print('=== LANDING PAGES — sessionDefaultChannelGroup == "AI Assistant" (28d) ===')
    print(json.dumps(page_rows, indent=2))


if __name__ == "__main__":
    main()
