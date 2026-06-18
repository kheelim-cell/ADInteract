"""
check_freshness.py
------------------
Checks that the latest transaction date in the parquet is no more than
MAX_LAG_DAYS behind today. Exits 1 (fails the CI step) when stale so
GitHub sends an email and the run turns red.

Also writes scripts/data/freshness_report.txt summarising the lag —
uploaded as a CI artifact for manual inspection.

Run:
    python scripts/check_freshness.py
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

META_JSON  = Path("static/data/meta.json")
PARQUET    = Path("static/data/transactions.parquet")
REPORT_OUT = Path("scripts/data/freshness_report.txt")
MAX_LAG_DAYS = 2   # flag if latest transaction is >2 calendar days behind today


def main():
    today = date.today()

    # ── Read latest date ───────────────────────────────────────────────────
    latest_date = None
    source      = "unknown"

    if META_JSON.exists():
        try:
            meta = json.loads(META_JSON.read_text())
            raw  = meta.get("dateRange", {}).get("max", "")
            if raw:
                latest_date = date.fromisoformat(raw)
                source = "meta.json"
        except Exception as e:
            print(f"  Warning: could not parse meta.json: {e}")

    if latest_date is None and PARQUET.exists():
        try:
            df = pd.read_parquet(PARQUET, columns=["sale_date"])
            df["sale_date"] = pd.to_datetime(df["sale_date"])
            latest_date = df["sale_date"].max().date()
            source = "parquet"
        except Exception as e:
            print(f"  Warning: could not read parquet: {e}")

    if latest_date is None:
        msg = f"FRESHNESS FAIL: Could not determine latest transaction date (no meta.json or parquet)"
        print(msg, file=sys.stderr)
        REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
        REPORT_OUT.write_text(msg)
        sys.exit(1)

    # ── Compute lag ────────────────────────────────────────────────────────
    lag_days = (today - latest_date).days
    # Skip weekends: ADREC doesn't register on Fri/Sat, so allow extra lag
    # Count business days (Sun–Thu in UAE calendar)
    business_lag = 0
    d = latest_date + timedelta(days=1)
    while d <= today:
        if d.weekday() not in (4, 5):   # 4=Friday, 5=Saturday
            business_lag += 1
        d += timedelta(days=1)

    status = "OK" if business_lag <= MAX_LAG_DAYS else "STALE"
    report = (
        f"Freshness check — {today}\n"
        f"  Latest transaction date : {latest_date}  (source: {source})\n"
        f"  Today                   : {today}\n"
        f"  Calendar lag            : {lag_days} day(s)\n"
        f"  Business-day lag (UAE)  : {business_lag} day(s)\n"
        f"  Threshold               : {MAX_LAG_DAYS} business days\n"
        f"  Status                  : {status}\n"
    )

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(report)
    print(report)

    if status == "STALE":
        print(
            f"\n*** DATA STALE ***\n"
            f"Latest transaction date is {latest_date} — {business_lag} UAE business day(s) behind today ({today}).\n"
            f"This usually means the ADREC scraper failed to download new data.\n"
            f"Action: check the 'Fetch ADREC export' step logs and adrec-debug artifact.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Data is fresh — pipeline healthy.")


if __name__ == "__main__":
    main()
