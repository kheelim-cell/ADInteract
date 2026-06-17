"""
compute_district_scores.py
--------------------------
Reads static/data/transactions.parquet and writes
static/data/district_scores.json — a per-district investment score (0-100)
composed of four equally-weighted sub-scores (0-25 each):

  1. Price trend   — median psf last 12m vs prior 12m
  2. Volume        — tx count last 12m vs all-district median
  3. Value         — district median psf vs Abu Dhabi overall median
  4. Off-plan      — proportion of off-plan transactions (developer confidence)

Run after transform.py + generate_district_summaries.py in CI.
"""

import json
import os
import re
from datetime import datetime, timezone

import numpy as np
import pandas as pd

PARQUET = "static/data/transactions.parquet"
OUTPUT  = "src/lib/data/district_scores.json"

MIN_TX = 10  # districts with fewer transactions are excluded


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[''']", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def sub_trend(psf_recent: pd.Series, psf_prior: pd.Series) -> tuple[int, str]:
    if len(psf_recent) < 5 or len(psf_prior) < 5:
        return 6, "flat"
    med_r = psf_recent.median()
    med_p = psf_prior.median()
    if med_p == 0:
        return 6, "flat"
    pct = (med_r - med_p) / med_p * 100
    if pct > 10:
        return 25, "up"
    if pct > 5:
        return 18, "up"
    if pct > 0:
        return 12, "up"
    if pct == 0:
        return 6, "flat"
    return 0, "down"


def sub_volume(count: int, all_counts: list[int]) -> int:
    arr = sorted(all_counts)
    q25 = np.percentile(arr, 25)
    q50 = np.percentile(arr, 50)
    q75 = np.percentile(arr, 75)
    if count >= q75:
        return 25
    if count >= q50:
        return 18
    if count >= q25:
        return 12
    return 6


def sub_value(district_med: float, ad_med: float) -> int:
    if ad_med == 0:
        return 12
    diff_pct = (district_med - ad_med) / ad_med * 100  # positive = above AD median (worse value)
    if diff_pct < -20:
        return 25
    if diff_pct < -10:
        return 18
    if abs(diff_pct) <= 10:
        return 12
    if diff_pct <= 20:
        return 6
    return 0


def sub_offplan(offplan_ratio: float) -> int:
    if offplan_ratio >= 0.40:
        return 25
    if offplan_ratio >= 0.25:
        return 18
    if offplan_ratio >= 0.10:
        return 12
    if offplan_ratio >= 0.05:
        return 6
    return 0


def score_color(score: int) -> str:
    if score >= 75:
        return "green"
    if score >= 50:
        return "amber"
    return "red"


def main():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    print(f"Reading {PARQUET}…")
    df = pd.read_parquet(PARQUET)
    df["sale_date"] = pd.to_datetime(df["sale_date"])

    latest = df["sale_date"].max()
    cutoff_12m  = latest - pd.DateOffset(months=12)
    cutoff_24m  = latest - pd.DateOffset(months=24)

    df_12m = df[df["sale_date"] >= cutoff_12m]
    df_prior = df[(df["sale_date"] >= cutoff_24m) & (df["sale_date"] < cutoff_12m)]

    # All-Abu-Dhabi median psf (last 12m, residential only)
    psf_all = df_12m["rate_per_sqft"].dropna()
    psf_all = psf_all[(psf_all > 50) & (psf_all < 20_000)]
    ad_median_psf = float(psf_all.median()) if len(psf_all) >= 10 else 1200.0

    # All districts' 12m counts (for volume percentile)
    districts = sorted(df["district"].dropna().unique())
    all_counts = [
        int(len(df_12m[df_12m["district"] == d]))
        for d in districts
        if d and str(d).strip() not in ("", "nan", "None")
    ]

    results: dict = {}

    for district in districts:
        if not district or str(district).strip() in ("", "nan", "None"):
            continue

        d_12m  = df_12m[df_12m["district"] == district]
        d_prior = df_prior[df_prior["district"] == district]

        if len(d_12m) < MIN_TX:
            continue

        psf_12m = d_12m["rate_per_sqft"].dropna()
        psf_12m = psf_12m[(psf_12m > 50) & (psf_12m < 20_000)]

        psf_prior_s = d_prior["rate_per_sqft"].dropna()
        psf_prior_s = psf_prior_s[(psf_prior_s > 50) & (psf_prior_s < 20_000)]

        # Sub-scores
        s1, trend_dir = sub_trend(psf_12m, psf_prior_s)
        s2 = sub_volume(len(d_12m), all_counts)
        s3 = sub_value(
            float(psf_12m.median()) if len(psf_12m) >= 3 else ad_median_psf,
            ad_median_psf
        )
        offplan_ratio = (
            len(d_12m[d_12m["sale_type"] == "off-plan"]) / len(d_12m)
            if len(d_12m) > 0 else 0
        )
        s4 = sub_offplan(offplan_ratio)

        total = s1 + s2 + s3 + s4

        results[district] = {
            "slug":             slugify(district),
            "district_name":    district,
            "score":            total,
            "score_trend":      s1,
            "score_volume":     s2,
            "score_value":      s3,
            "score_offplan":    s4,
            "trend_direction":  trend_dir,
            "color":            score_color(total),
            "tx_count_12m":     int(len(d_12m)),
            "median_psf_12m":   round(float(psf_12m.median())) if len(psf_12m) >= 3 else None,
            "offplan_pct":      round(offplan_ratio * 100, 1),
            "computed_at":      datetime.now(timezone.utc).isoformat(),
        }

    # Sort by score descending
    sorted_results = dict(
        sorted(results.items(), key=lambda x: x[1]["score"], reverse=True)
    )

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(sorted_results, f, ensure_ascii=False, indent=2)

    print(f"Wrote {OUTPUT}  ({len(sorted_results)} districts)")
    top5 = list(sorted_results.items())[:5]
    for name, s in top5:
        print(f"  {name}: {s['score']}/100 (trend={s['score_trend']}, vol={s['score_volume']}, val={s['score_value']}, offplan={s['score_offplan']})")


if __name__ == "__main__":
    main()
