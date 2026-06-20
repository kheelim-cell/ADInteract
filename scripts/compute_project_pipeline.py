"""
compute_project_pipeline.py
---------------------------
Off-plan project pipeline: per-project registered-sales activity, built
from ADREC transaction data only.

IMPORTANT — what this is NOT: ADREC's transaction export has no field for
total units in a project, so this script cannot compute "% sold" or a
true absorption rate. Anyone who tells you they have that number from this
data source is estimating, not reporting. What we *can* report honestly,
straight from registered transactions:
  - registered_sales_alltime — count of off-plan sale registrations ever seen
  - sales_last_90d / sales_prior_90d — registration velocity, recent vs prior
  - momentum_pct — % change between those two windows (the "is this heating
    up or cooling off" signal)
  - days_since_last_sale — staleness flag (a project with 0 registrations in
    90+ days is either sold out, paused, or quietly struggling — we can't
    tell which, so we just surface the gap)
  - median_price_aed / median_psf — current going rate
  - first_sale_date — when the project entered the market

Run after transform.py in CI.
"""

import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

PARQUET_TX = "static/data/transactions.parquet"
OUTPUT     = "src/lib/data/project_pipeline.json"

MIN_SALES_ALLTIME = 5     # projects with fewer off-plan registrations ever are excluded (too thin to read)
STALE_DAYS        = 120   # no registrations in this many days → flagged stale


def slugify(name: str) -> str:
    s = str(name).lower().strip()
    s = "".join(c if c.isalnum() or c in " -" else "" for c in s)
    return "-".join(s.split())


def main():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    print(f"Reading {PARQUET_TX}…")
    df = pd.read_parquet(PARQUET_TX)
    df["sale_date"] = pd.to_datetime(df["sale_date"])

    op = df[df["sale_type"] == "off-plan"].copy()
    op = op[op["project_name"].notna() & (op["project_name"].astype(str).str.strip() != "")]

    latest = df["sale_date"].max()
    cutoff_90  = latest - pd.DateOffset(days=90)
    cutoff_180 = latest - pd.DateOffset(days=180)

    projects = sorted(op["project_name"].dropna().unique())
    results: list = []

    for project in projects:
        p = op[op["project_name"] == project]
        if len(p) < MIN_SALES_ALLTIME:
            continue

        last_90d  = p[p["sale_date"] >= cutoff_90]
        prior_90d = p[(p["sale_date"] >= cutoff_180) & (p["sale_date"] < cutoff_90)]

        n_last, n_prior = len(last_90d), len(prior_90d)
        if n_prior > 0:
            momentum_pct = round((n_last - n_prior) / n_prior * 100, 1)
        elif n_last > 0:
            momentum_pct = None  # no prior baseline to compare against
        else:
            momentum_pct = None

        last_sale_date = p["sale_date"].max()
        days_since_last_sale = int((latest - last_sale_date).days)

        district = p["district"].mode().iloc[0] if not p["district"].mode().empty else None

        psf = p["rate_per_sqft"].dropna()
        psf = psf[(psf > 50) & (psf < 20_000)]
        price = p["price_aed"].dropna()
        price = price[price > 0]

        if days_since_last_sale > STALE_DAYS:
            status = "stale"
        elif n_prior == 0 and n_last > 0:
            status = "new_launch"
        elif momentum_pct is not None and momentum_pct >= 20:
            status = "accelerating"
        elif momentum_pct is not None and momentum_pct <= -30:
            status = "slowing"
        else:
            status = "steady"

        results.append({
            "slug": slugify(project),
            "project_name": str(project).strip(),
            "district": district,
            "registered_sales_alltime": int(len(p)),
            "sales_last_90d": n_last,
            "sales_prior_90d": n_prior,
            "momentum_pct": momentum_pct,
            "status": status,
            "days_since_last_sale": days_since_last_sale,
            "first_sale_date": p["sale_date"].min().strftime("%Y-%m-%d"),
            "last_sale_date": last_sale_date.strftime("%Y-%m-%d"),
            "median_price_aed": int(price.median()) if len(price) else None,
            "median_psf": int(psf.median()) if len(psf) else None,
        })

    # Rank by recent registration velocity — most active pipelines first
    results.sort(key=lambda r: (r["sales_last_90d"], r["registered_sales_alltime"]), reverse=True)

    total_alltime_sales = int(sum(r["registered_sales_alltime"] for r in results))

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "as_of_date": latest.strftime("%Y-%m-%d"),
        "project_count": len(results),
        "total_registered_sales_alltime": total_alltime_sales,
        "projects": results,
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"Wrote {len(results)} projects to {OUTPUT}")
    accelerating = sum(1 for r in results if r["status"] == "accelerating")
    stale = sum(1 for r in results if r["status"] == "stale")
    print(f"  accelerating: {accelerating}  stale: {stale}")


if __name__ == "__main__":
    main()
