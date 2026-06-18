"""
compute_district_scores.py
--------------------------
Dual-scoring model for Abu Dhabi districts.

Districts are classified by market maturity using all-time ADREC data:
  - ready_pct > 60%  → Yield & Stability score  (mature secondary market)
  - ready_pct < 40%  → Growth & Early-Cycle score (pre-completion / new freehold)
  - 40–60%           → Both scores computed

YIELD & STABILITY (100 pts total):
  1. Price momentum   — ready txns only, last 12m vs prior 12m          30 pts
  2. Gross rental yield — ADREC rent registrations / sale price          25 pts
  3. Liquidity        — recency-weighted (3m vs 9m rolling avg)          20 pts
  4. Price stability  — inverse CoV of quarterly PSF over 24m            15 pts
  5. Appreciation     — ready PSF / off-plan PSF ratio                   10 pts

GROWTH & EARLY-CYCLE (100 pts total):
  1. Off-plan velocity — last 6m vs prior 6m off-plan count              30 pts
  2. Off-plan momentum — % change in off-plan PSF, last 12m vs prior     25 pts
  3. Appreciation      — ready PSF / off-plan PSF (where data exists)    20 pts
  4. Developer activity — unique project count growth, last 12m vs prior 15 pts
  5. Market entry       — off-plan tx in last 3m vs 3m rolling avg       10 pts

Run after transform.py + transform_rental.py in CI.
"""

import json
import os
import re
from datetime import datetime, timezone

import numpy as np
import pandas as pd

PARQUET_TX     = "static/data/transactions.parquet"
PARQUET_RENTAL = "static/data/rental.parquet"
OUTPUT         = "src/lib/data/district_scores.json"

MIN_TX = 10      # districts with fewer 12m transactions excluded
PSF_MIN, PSF_MAX = 50, 20_000


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[''']", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def safe_median(series: pd.Series) -> float | None:
    s = series.dropna()
    s = s[(s > PSF_MIN) & (s < PSF_MAX)]
    return float(s.median()) if len(s) >= 3 else None


# ─── Yield & Stability sub-scores ─────────────────────────────────────────────

def ys_momentum(ready_12m: pd.DataFrame, ready_prior: pd.DataFrame) -> tuple[int, float | None, str]:
    """30 pts — % change in ready-market median PSF."""
    psf_r = ready_12m["rate_per_sqft"].dropna()
    psf_r = psf_r[(psf_r > PSF_MIN) & (psf_r < PSF_MAX)]
    psf_p = ready_prior["rate_per_sqft"].dropna()
    psf_p = psf_p[(psf_p > PSF_MIN) & (psf_p < PSF_MAX)]
    if len(psf_r) < 5 or len(psf_p) < 5:
        return 15, None, "flat"
    med_r, med_p = psf_r.median(), psf_p.median()
    if med_p == 0:
        return 15, None, "flat"
    pct = (med_r - med_p) / med_p * 100
    pct_capped = max(-40.0, min(40.0, pct))
    score = int((pct_capped + 40) / 80 * 30)
    direction = "up" if pct > 1 else ("down" if pct < -1 else "flat")
    return score, round(pct, 1), direction


def ys_yield(district: str, rental_df: pd.DataFrame, sale_price_median: float | None) -> tuple[int, float | None]:
    """25 pts — gross rental yield from ADREC rent registrations."""
    if rental_df is None or sale_price_median is None or sale_price_median <= 0:
        return 12, None
    d_rent = rental_df[rental_df["district"] == district]
    if len(d_rent) < 5:
        return 12, None
    # Use latest available year, all layouts, new + renewal contracts
    latest_year = int(d_rent["year"].max())
    d_rent_latest = d_rent[d_rent["year"] == latest_year]
    if len(d_rent_latest) < 3:
        d_rent_latest = d_rent
    med_rent = d_rent_latest["median_rent"].dropna().median()
    if not med_rent or med_rent <= 0:
        return 12, None
    gross_yield = med_rent / sale_price_median * 100
    if gross_yield > 8:
        score = 25
    elif gross_yield > 6:
        score = 22
    elif gross_yield > 4:
        score = 16
    elif gross_yield > 2:
        score = 8
    else:
        score = 2
    return score, round(gross_yield, 1)


def ys_liquidity(d_12m: pd.DataFrame, latest: pd.Timestamp) -> tuple[int, float | None]:
    """20 pts — recency-weighted: last 3m count vs avg 3m count over prior 9m."""
    cutoff_3m = latest - pd.DateOffset(months=3)
    cutoff_12m = latest - pd.DateOffset(months=12)
    last_3m = len(d_12m[d_12m["sale_date"] >= cutoff_3m])
    prior_9m = len(d_12m[(d_12m["sale_date"] >= cutoff_12m) & (d_12m["sale_date"] < cutoff_3m)])
    prior_3m_avg = prior_9m / 3 if prior_9m > 0 else 1
    ratio = last_3m / prior_3m_avg if prior_3m_avg > 0 else 1.0
    score = int(min(20, np.log1p(ratio) / np.log1p(3.0) * 20))
    return score, round(ratio, 2)


def ys_stability(d_24m: pd.DataFrame) -> tuple[int, float | None]:
    """15 pts — inverse CoV of quarterly median PSF over 24m."""
    df = d_24m.copy()
    df = df[df["rate_per_sqft"].between(PSF_MIN, PSF_MAX)]
    if len(df) < 20:
        return 7, None
    df["quarter"] = df["sale_date"].dt.to_period("Q")
    q_meds = df.groupby("quarter")["rate_per_sqft"].median()
    if len(q_meds) < 4:
        return 7, None
    cov = float(q_meds.std() / q_meds.mean()) if q_meds.mean() > 0 else 1.0
    if cov <= 0.05:
        score = 15
    elif cov <= 0.10:
        score = 12
    elif cov <= 0.20:
        score = 8
    elif cov <= 0.30:
        score = 5
    else:
        score = 2
    return score, round(cov, 3)


def appreciation_signal(d_12m: pd.DataFrame, max_pts: int) -> tuple[int, float | None]:
    """Shared: ready PSF / off-plan PSF ratio."""
    ready = d_12m[d_12m["sale_type"] == "ready"]["rate_per_sqft"]
    ready = ready.dropna()
    ready = ready[(ready > PSF_MIN) & (ready < PSF_MAX)]
    offplan = d_12m[d_12m["sale_type"] == "off-plan"]["rate_per_sqft"]
    offplan = offplan.dropna()
    offplan = offplan[(offplan > PSF_MIN) & (offplan < PSF_MAX)]
    if len(ready) < 5 or len(offplan) < 5:
        return max_pts // 2, None
    ratio = float(ready.median() / offplan.median())
    # Normalize: ratio 0.5 → 0 pts, ratio 1.5 → max_pts
    score = int(max(0, min(max_pts, (ratio - 0.5) / 1.0 * max_pts)))
    return score, round(ratio, 2)


# ─── Growth & Early-Cycle sub-scores ──────────────────────────────────────────

def gec_velocity(d_12m: pd.DataFrame, d_prior_6m: pd.DataFrame, latest: pd.Timestamp) -> tuple[int, float | None]:
    """30 pts — off-plan tx count, last 6m vs prior 6m."""
    cutoff_6m = latest - pd.DateOffset(months=6)
    last_6m_op = len(d_12m[(d_12m["sale_date"] >= cutoff_6m) & (d_12m["sale_type"] == "off-plan")])
    prior_6m_op = len(d_prior_6m[d_prior_6m["sale_type"] == "off-plan"])
    if prior_6m_op == 0:
        score = 15 if last_6m_op > 0 else 5
        return score, None
    ratio = last_6m_op / prior_6m_op
    score = int(min(30, ratio / 3.0 * 30))
    return score, round(ratio, 2)


def gec_offplan_momentum(d_12m: pd.DataFrame, d_prior: pd.DataFrame) -> tuple[int, float | None, str]:
    """25 pts — % change in off-plan PSF, last 12m vs prior 12m."""
    op_12m = d_12m[d_12m["sale_type"] == "off-plan"]["rate_per_sqft"].dropna()
    op_12m = op_12m[(op_12m > PSF_MIN) & (op_12m < PSF_MAX)]
    op_prior = d_prior[d_prior["sale_type"] == "off-plan"]["rate_per_sqft"].dropna()
    op_prior = op_prior[(op_prior > PSF_MIN) & (op_prior < PSF_MAX)]
    if len(op_12m) < 5 or len(op_prior) < 5:
        return 12, None, "flat"
    med_r, med_p = op_12m.median(), op_prior.median()
    if med_p == 0:
        return 12, None, "flat"
    pct = (med_r - med_p) / med_p * 100
    pct_capped = max(-40.0, min(40.0, pct))
    score = int((pct_capped + 40) / 80 * 25)
    direction = "up" if pct > 1 else ("down" if pct < -1 else "flat")
    return score, round(pct, 1), direction


def gec_developer_activity(d_12m: pd.DataFrame, d_prior: pd.DataFrame) -> tuple[int, float | None]:
    """15 pts — unique off-plan project count, last 12m vs prior 12m."""
    proj_12m = d_12m[d_12m["sale_type"] == "off-plan"]["project_name"].dropna().nunique()
    proj_prior = d_prior[d_prior["sale_type"] == "off-plan"]["project_name"].dropna().nunique()
    if proj_prior == 0:
        return 8, None
    ratio = proj_12m / proj_prior
    if ratio >= 1.5:
        score = 15
    elif ratio >= 1.0:
        score = 11
    elif ratio >= 0.75:
        score = 7
    else:
        score = 4
    return score, round(ratio, 2)


def gec_market_entry(d_12m: pd.DataFrame, latest: pd.Timestamp) -> tuple[int, float | None]:
    """10 pts — off-plan tx in last 3m vs 3m rolling avg."""
    cutoff_3m = latest - pd.DateOffset(months=3)
    op_12m = d_12m[d_12m["sale_type"] == "off-plan"]
    last_3m = len(op_12m[op_12m["sale_date"] >= cutoff_3m])
    prior_9m = len(op_12m[op_12m["sale_date"] < cutoff_3m])
    prior_3m_avg = prior_9m / 3 if prior_9m > 0 else 1
    ratio = last_3m / prior_3m_avg if prior_3m_avg > 0 else 1.0
    if ratio >= 1.5:
        score = 10
    elif ratio >= 1.0:
        score = 7
    elif ratio >= 0.75:
        score = 4
    else:
        score = 2
    return score, round(ratio, 2)


# ─── Main ──────────────────────────────────────────────────────────────────────

def score_color(score: int) -> str:
    if score >= 75:
        return "green"
    if score >= 50:
        return "amber"
    return "red"


def main():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    print(f"Reading {PARQUET_TX}…")
    df = pd.read_parquet(PARQUET_TX)
    df["sale_date"] = pd.to_datetime(df["sale_date"])

    # Load rental data (optional — gracefully absent)
    rental_df = None
    if os.path.exists(PARQUET_RENTAL):
        print(f"Reading {PARQUET_RENTAL}…")
        rental_df = pd.read_parquet(PARQUET_RENTAL)
        rental_df["district"] = rental_df["district"].str.strip() if "district" in rental_df.columns else None
        print(f"  Rental rows: {len(rental_df):,}")
    else:
        print(f"  {PARQUET_RENTAL} not found — yield scores will be neutral")

    latest     = df["sale_date"].max()
    cutoff_12m = latest - pd.DateOffset(months=12)
    cutoff_24m = latest - pd.DateOffset(months=24)
    cutoff_6m_prior_start = latest - pd.DateOffset(months=18)
    cutoff_6m_prior_end   = latest - pd.DateOffset(months=12)

    df_12m  = df[df["sale_date"] >= cutoff_12m].copy()
    df_prior = df[(df["sale_date"] >= cutoff_24m) & (df["sale_date"] < cutoff_12m)].copy()
    df_24m  = df[df["sale_date"] >= cutoff_24m].copy()
    # prior 6m window (for velocity)
    df_prior_6m = df[(df["sale_date"] >= cutoff_6m_prior_start) & (df["sale_date"] < cutoff_6m_prior_end)].copy()

    districts = sorted(df["district"].dropna().unique())
    results: dict = {}

    for district in districts:
        if not district or str(district).strip() in ("", "nan", "None"):
            continue

        d_12m   = df_12m[df_12m["district"] == district]
        d_prior = df_prior[df_prior["district"] == district]
        d_24m   = df_24m[df_24m["district"] == district]
        d_prior_6m = df_prior_6m[df_prior_6m["district"] == district]

        if len(d_12m) < MIN_TX:
            continue

        # ── Maturity classification ──────────────────────────────────────────
        d_all = df[df["district"] == district]
        ready_all   = len(d_all[d_all["sale_type"] == "ready"])
        offplan_all = len(d_all[d_all["sale_type"] == "off-plan"])
        typed_all   = ready_all + offplan_all
        ready_pct   = (ready_all / typed_all * 100) if typed_all > 0 else 50.0

        if ready_pct > 60:
            score_type = "yield_stability"
        elif ready_pct < 40:
            score_type = "growth_early_cycle"
        else:
            score_type = "both"

        # ── Shared appreciation signal ───────────────────────────────────────
        op_psf   = d_12m[d_12m["sale_type"] == "off-plan"]["rate_per_sqft"]
        op_psf   = op_psf.dropna()
        op_psf   = op_psf[(op_psf > PSF_MIN) & (op_psf < PSF_MAX)]
        ready_psf = d_12m[d_12m["sale_type"] == "ready"]["rate_per_sqft"]
        ready_psf = ready_psf.dropna()
        ready_psf = ready_psf[(ready_psf > PSF_MIN) & (ready_psf < PSF_MAX)]

        # ── Overall trend direction (for display) ────────────────────────────
        all_psf_12m  = d_12m["rate_per_sqft"].dropna()
        all_psf_prior = d_prior["rate_per_sqft"].dropna()
        all_psf_12m  = all_psf_12m[(all_psf_12m > PSF_MIN) & (all_psf_12m < PSF_MAX)]
        all_psf_prior = all_psf_prior[(all_psf_prior > PSF_MIN) & (all_psf_prior < PSF_MAX)]
        if len(all_psf_12m) >= 5 and len(all_psf_prior) >= 5 and all_psf_prior.median() > 0:
            pct_all = (all_psf_12m.median() - all_psf_prior.median()) / all_psf_prior.median() * 100
            trend_dir_overall = "up" if pct_all > 1 else ("down" if pct_all < -1 else "flat")
        else:
            trend_dir_overall = "flat"

        entry: dict = {
            "slug":              slugify(district),
            "district_name":     district,
            "score_type":        score_type,
            "ready_pct_alltime": round(ready_pct, 1),
            "trend_direction":   trend_dir_overall,
            "tx_count_12m":      int(len(d_12m)),
            "median_psf_12m":    round(float(all_psf_12m.median())) if len(all_psf_12m) >= 3 else None,
            "offplan_pct":       round(len(d_12m[d_12m["sale_type"] == "off-plan"]) / len(d_12m) * 100, 1),
            "computed_at":       datetime.now(timezone.utc).isoformat(),
        }

        # ── Yield & Stability ────────────────────────────────────────────────
        if score_type in ("yield_stability", "both"):
            d_ready_12m  = d_12m[d_12m["sale_type"] == "ready"]
            d_ready_prior = d_prior[d_prior["sale_type"] == "ready"]

            s_mom, pct_mom, mom_dir = ys_momentum(d_ready_12m, d_ready_prior)

            sale_price_med = float(d_12m["price_aed"].dropna().median()) if "price_aed" in d_12m.columns and len(d_12m) >= 3 else None
            s_yield, gross_yield = ys_yield(district, rental_df, sale_price_med)

            s_liq, liq_ratio   = ys_liquidity(d_12m, latest)
            s_stab, cov_val    = ys_stability(d_24m)
            s_app, app_ratio   = appreciation_signal(d_12m, max_pts=10)

            ys_total = s_mom + s_yield + s_liq + s_stab + s_app

            entry["ys"] = {
                "total": ys_total,
                "momentum":    {"score": s_mom,   "max": 30, "pct_change":   pct_mom,    "direction": mom_dir},
                "yield":       {"score": s_yield,  "max": 25, "gross_yield_pct": gross_yield},
                "liquidity":   {"score": s_liq,    "max": 20, "recency_ratio": liq_ratio},
                "stability":   {"score": s_stab,   "max": 15, "cov":          cov_val},
                "appreciation":{"score": s_app,    "max": 10, "ratio":        app_ratio},
            }

        # ── Growth & Early-Cycle ─────────────────────────────────────────────
        if score_type in ("growth_early_cycle", "both"):
            s_vel, vel_ratio       = gec_velocity(d_12m, d_prior_6m, latest)
            s_op_mom, op_pct, op_dir = gec_offplan_momentum(d_12m, d_prior)
            s_app_gec, app_ratio_gec = appreciation_signal(d_12m, max_pts=20)
            s_dev, dev_ratio       = gec_developer_activity(d_12m, d_prior)
            s_entry, entry_ratio   = gec_market_entry(d_12m, latest)

            gec_total = s_vel + s_op_mom + s_app_gec + s_dev + s_entry

            entry["gec"] = {
                "total": gec_total,
                "velocity":    {"score": s_vel,     "max": 30, "velocity_ratio":     vel_ratio},
                "momentum":    {"score": s_op_mom,  "max": 25, "pct_change":         op_pct,   "direction": op_dir},
                "appreciation":{"score": s_app_gec, "max": 20, "ratio":              app_ratio_gec},
                "developer":   {"score": s_dev,     "max": 15, "project_growth_ratio": dev_ratio},
                "entry":       {"score": s_entry,   "max": 10, "entry_ratio":        entry_ratio},
            }

        # ── Primary score (used for ranking) ────────────────────────────────
        if score_type == "yield_stability":
            primary = entry["ys"]["total"]
        elif score_type == "growth_early_cycle":
            primary = entry["gec"]["total"]
        else:
            primary = max(entry["ys"]["total"], entry["gec"]["total"])

        entry["score"] = primary
        entry["color"] = score_color(primary)
        results[district] = entry

    # Sort by score descending
    sorted_results = dict(sorted(results.items(), key=lambda x: x[1]["score"], reverse=True))

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(sorted_results, f, ensure_ascii=False, indent=2)

    print(f"Wrote {OUTPUT}  ({len(sorted_results)} districts)")
    for name, s in list(sorted_results.items())[:5]:
        print(f"  {name}: {s['score']}/100  type={s['score_type']}  ready%={s['ready_pct_alltime']}")


if __name__ == "__main__":
    main()
