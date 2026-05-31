"""
generate_district_summaries.py
-------------------------------
Reads static/data/transactions.parquet and writes
src/lib/data/district_summaries.json — a per-district stats object
used at SvelteKit build time to:
  1. Enumerate /area/[district] routes for prerendering (entries())
  2. Populate SEO prose on each district page

Run after transform.py in the GitHub Actions data refresh workflow.
"""

import json
import os
import re

import pandas as pd

PARQUET = "static/data/transactions.parquet"
OUTPUT  = "src/lib/data/district_summaries.json"


def slugify(name: str) -> str:
    """'Al Reem Island' → 'al-reem-island', "'Asharij" → 'asharij'"""
    s = name.lower()
    s = re.sub(r"[''']", "", s)          # remove apostrophes
    s = re.sub(r"[^a-z0-9]+", "-", s)   # non-alphanumeric → hyphen
    return s.strip("-")

# Layouts we actually name in prose (skip commercial + unclassified)
RESIDENTIAL_LAYOUTS = {"studio", "1 bed", "2 beds", "3 beds", "4 beds", "5 beds", "5+ beds", "6+ beds"}


def fmt_aed(n: float) -> str:
    """Format a number as compact AED string, e.g. 2500000 → 'AED 2.5M'"""
    if n >= 1_000_000:
        return f"AED {n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"AED {n / 1_000:.0f}K"
    return f"AED {n:.0f}"


def main():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    print(f"Reading {PARQUET}…")
    df = pd.read_parquet(PARQUET)
    df["sale_date"] = pd.to_datetime(df["sale_date"])

    # Last 12 months from the most recent sale in the dataset
    latest = df["sale_date"].max()
    cutoff_12m = latest - pd.DateOffset(months=12)

    df_12m = df[df["sale_date"] >= cutoff_12m]

    summaries: dict = {}
    districts = sorted(df["district"].dropna().unique())

    for district in districts:
        if not district or str(district).strip() in ("", "nan", "None"):
            continue

        d_all = df[df["district"] == district]
        d_12m = df_12m[df_12m["district"] == district]

        # Fall back to all-time if no recent data
        d_ref = d_12m if len(d_12m) >= 5 else d_all

        # Skip districts with effectively no data
        if len(d_all) < 3:
            continue

        # PSF — filter extreme outliers
        psf = d_ref["rate_per_sqft"].dropna()
        psf = psf[(psf > 50) & (psf < 20_000)]

        price = d_ref["price_aed"].dropna()
        price = price[price > 0]

        # Top residential layouts by volume
        top_layouts = (
            d_ref[d_ref["layout"].isin(RESIDENTIAL_LAYOUTS)]
            .groupby("layout")
            .size()
            .sort_values(ascending=False)
            .head(3)
            .index
            .tolist()
        )

        summaries[district] = {
            "slug":            slugify(district),
            "tx_count_all":    int(len(d_all)),
            "tx_count_12m":    int(len(d_ref)),
            "median_psf":      round(float(psf.median()))          if len(psf)   >= 3 else None,
            "p10_psf":         round(float(psf.quantile(0.10)))    if len(psf)   >= 10 else None,
            "p90_psf":         round(float(psf.quantile(0.90)))    if len(psf)   >= 10 else None,
            "median_price":    round(float(price.median()))        if len(price) >= 3 else None,
            "top_layouts":     top_layouts,
            "is_12m":          len(d_12m) >= 5,
            "last_sale":       str(d_all["sale_date"].max().date()),
        }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)

    print(f"Wrote {OUTPUT}  ({len(summaries)} districts)")


if __name__ == "__main__":
    main()
