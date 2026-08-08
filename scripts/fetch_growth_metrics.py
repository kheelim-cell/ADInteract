"""
fetch_growth_metrics.py
------------------------
Weekly growth metrics snapshot: GA4 traffic + real Supabase signup numbers.

Writes marketing/analytics/growth_metrics.json, committed to the repo by
.github/workflows/growth-metrics.yml. This is meant to be what the (still
to be rescoped) growth report reads from, instead of Khee copy-pasting GA4
numbers by hand into a report shell.

Why GA4 + Supabase, and not GA4 alone: this app has no custom `sign_up`
event wired up anywhere (checked src/app.html and the component tree —
only the automatic pageview/session events plus one custom `share` event
exist). GA4 has no way to know when someone completes Google sign-in.
Supabase auth.users is the actual source of truth for signups, so that's
where this script gets them, via the Auth Admin API using the same
service-role key send_weekly_digest.py already uses.

The `share` event's `method` parameter (whatsapp/copylink/etc.) isn't
queryable via the API either — it's not registered as a GA4 custom
dimension (Admin → Custom definitions). This script pulls the total share
count, which works today; a per-method breakdown needs that one-time
registration step first.

Required env vars — GA4 and Supabase sections degrade independently; either
missing just means a null section in the output, not a failed run:
  GA4_CREDENTIALS_JSON        — GA4 service-account JSON, granted Viewer on
                                 the property (Analytics Admin → Property
                                 Access Management). Falls back to
                                 GOOGLE_CREDENTIALS_JSON if unset — the same
                                 "adinteract-data" service account already
                                 used for Sheets access (send_weekly_digest.py,
                                 data-refresh.yml) can be reused here; it just
                                 needs the extra Viewer grant on the GA4
                                 property, not a separate service account or
                                 a separately-pasted key.
  GA4_PROPERTY_ID              — numeric GA4 property ID (Admin → Property
                                 Settings) — NOT the G-XXXXXXX measurement ID.
  SUPABASE_URL                 — reuses the existing VITE_SUPABASE_URL value
  SUPABASE_SERVICE_ROLE_KEY    — already configured; see send_weekly_digest.py

Usage:
  python scripts/fetch_growth_metrics.py
"""

import base64
import json
import os
import tempfile
from datetime import datetime, timezone

import requests

OUT_PATH = "marketing/analytics/growth_metrics.json"

# Falls back to the existing Sheets service-account credential — see module
# docstring. GA4_CREDENTIALS_JSON only needs to be set separately if you
# genuinely want a dedicated service account instead of reusing "adinteract-data".
GA4_CREDENTIALS_JSON = (
    os.environ.get("GA4_CREDENTIALS_JSON", "").strip()
    or os.environ.get("GOOGLE_CREDENTIALS_JSON", "").strip()
)
GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID", "").strip()

SUPABASE_URL          = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")


# ── GA4 ──────────────────────────────────────────────────────────────────────
def _ga4_credentials():
    """Same raw-JSON-or-base64 parsing send_weekly_digest.py uses for Sheets."""
    from google.oauth2.service_account import Credentials

    if GA4_CREDENTIALS_JSON.startswith("{"):
        info = json.loads(GA4_CREDENTIALS_JSON)
    else:
        padded = GA4_CREDENTIALS_JSON + "=" * (4 - len(GA4_CREDENTIALS_JSON) % 4)
        info = json.loads(base64.b64decode(padded).decode())

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(info, tmp)
    tmp.close()
    creds = Credentials.from_service_account_file(
        tmp.name, scopes=["https://www.googleapis.com/auth/analytics.readonly"]
    )
    os.unlink(tmp.name)
    return creds


def fetch_ga4_metrics() -> dict | None:
    if not (GA4_CREDENTIALS_JSON and GA4_PROPERTY_ID):
        print("GA4 credentials/property ID not configured — skipping GA4 section.")
        return None

    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            DateRange, Dimension, Filter, FilterExpression, Metric, RunReportRequest,
        )

        client = BetaAnalyticsDataClient(credentials=_ga4_credentials())
        property_path = f"properties/{GA4_PROPERTY_ID}"

        def window(days: int) -> dict:
            date_range = DateRange(start_date=f"{days}daysAgo", end_date="today")

            totals = client.run_report(RunReportRequest(
                property=property_path,
                date_ranges=[date_range],
                metrics=[Metric(name="sessions"), Metric(name="totalUsers"),
                         Metric(name="newUsers")],
            ))
            row = totals.rows[0].metric_values if totals.rows else None
            sessions    = int(row[0].value) if row else 0
            total_users = int(row[1].value) if row else 0
            new_users   = int(row[2].value) if row else 0
            returning_users = max(total_users - new_users, 0)
            returning_pct = (
                round(returning_users / total_users * 100, 1) if total_users else 0.0
            )

            sources = client.run_report(RunReportRequest(
                property=property_path,
                date_ranges=[date_range],
                dimensions=[Dimension(name="sessionSource"), Dimension(name="sessionMedium")],
                metrics=[Metric(name="sessions")],
                order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
                limit=10,
            ))
            top_sources = [
                {
                    "source": r.dimension_values[0].value,
                    "medium": r.dimension_values[1].value,
                    "sessions": int(r.metric_values[0].value),
                }
                for r in sources.rows
            ]

            pages = client.run_report(RunReportRequest(
                property=property_path,
                date_ranges=[date_range],
                dimensions=[Dimension(name="landingPagePlusQueryString")],
                metrics=[Metric(name="sessions")],
                order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
                limit=15,
            ))
            top_pages = [
                {"page": r.dimension_values[0].value, "sessions": int(r.metric_values[0].value)}
                for r in pages.rows
            ]

            # Total share-event count. Per-method breakdown needs the `method`
            # event parameter registered as a GA4 custom dimension first
            # (Admin → Custom definitions) — not done yet, see module docstring.
            share_report = client.run_report(RunReportRequest(
                property=property_path,
                date_ranges=[date_range],
                metrics=[Metric(name="eventCount")],
                dimension_filter=FilterExpression(
                    filter=Filter(
                        field_name="eventName",
                        string_filter=Filter.StringFilter(value="share"),
                    )
                ),
                dimensions=[Dimension(name="eventName")],
            ))
            share_events = (
                int(share_report.rows[0].metric_values[0].value) if share_report.rows else 0
            )

            return {
                "sessions": sessions,
                "total_users": total_users,
                "new_users": new_users,
                "returning_users_pct": returning_pct,
                "share_events": share_events,
                "top_sources": top_sources,
                "top_landing_pages": top_pages,
            }

        return {"period_7d": window(7), "period_30d": window(30)}

    except Exception as e:
        print(f"WARNING: GA4 fetch failed ({e}) — writing null ga4 section.")
        return None


# ── Supabase signups (real ground truth — see module docstring) ─────────────
def fetch_supabase_signups() -> dict | None:
    if not (SUPABASE_URL and SUPABASE_SERVICE_KEY):
        print("Supabase service role key not configured — skipping signups section.")
        return None

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }

    try:
        # Auth Admin API — paginated, service-role only (not exposed via PostgREST).
        users, page = [], 1
        while True:
            resp = requests.get(
                f"{SUPABASE_URL}/auth/v1/admin/users",
                headers=headers,
                params={"page": page, "per_page": 1000},
                timeout=15,
            )
            resp.raise_for_status()
            batch = resp.json().get("users", [])
            users.extend(batch)
            if len(batch) < 1000:
                break
            page += 1

        now = datetime.now(timezone.utc)
        created_ats = []
        for u in users:
            ca = u.get("created_at")
            if not ca:
                continue
            created_ats.append(datetime.fromisoformat(ca.replace("Z", "+00:00")))

        new_7d  = sum(1 for c in created_ats if (now - c).days < 7)
        new_30d = sum(1 for c in created_ats if (now - c).days < 30)

        sub_resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/email_subscribers",
            headers={**headers, "Prefer": "count=exact"},
            params={"select": "email"},
            timeout=15,
        )
        sub_resp.raise_for_status()
        content_range = sub_resp.headers.get("Content-Range", "*/0")
        subscriber_count = int(content_range.split("/")[-1])

        return {
            "total_signups": len(users),
            "new_signups_7d": new_7d,
            "new_signups_30d": new_30d,
            "email_subscribers": subscriber_count,
        }

    except Exception as e:
        print(f"WARNING: Supabase signup fetch failed ({e}) — writing null signups section.")
        return None


def main() -> None:
    metrics = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ga4": fetch_ga4_metrics(),
        "signups": fetch_supabase_signups(),
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
