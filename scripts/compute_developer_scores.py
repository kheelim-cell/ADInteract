"""
Compute developer track record scores from ADREC transaction data.

Outputs: static/data/developer_scores.json

Run from repo root:
  python scripts/compute_developer_scores.py
"""

import json
import os
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).parent.parent
TX_PATH = REPO_ROOT / "static" / "data" / "transactions.parquet"
SC_PATH = REPO_ROOT / "src" / "lib" / "data" / "service_charges.json"
OUT_PATH = REPO_ROOT / "static" / "data" / "developer_scores.json"


def load_data():
    tx = pd.read_parquet(TX_PATH)
    with open(SC_PATH, encoding="utf-8") as f:
        sc = json.load(f)
    return tx, sc


def build_project_developer_map(sc: list) -> dict:
    """Map project_name (lowercased, stripped) → developer_name."""
    mapping = {}
    for entry in sc:
        proj = entry.get("project_name", "").strip().lower()
        dev = entry.get("developer_name", "").strip()
        if proj and dev:
            mapping[proj] = dev
    return mapping


def compute_scores(tx: pd.DataFrame, proj_to_dev: dict) -> list:
    tx = tx.copy()
    tx["proj_key"] = tx["project_name"].fillna("").str.strip().str.lower()
    tx["developer_name"] = tx["proj_key"].map(proj_to_dev)
    tx = tx[tx["developer_name"].notna() & (tx["developer_name"] != "")]

    results = []

    for dev, grp in tx.groupby("developer_name"):
        projects = grp["project_name"].dropna().unique()
        total_tx = len(grp)
        project_count = len(projects)

        # PSF premium: median PSF of dev's projects vs median PSF of their districts
        psf_data = grp[grp["rate_per_sqft"] > 0]["rate_per_sqft"]
        dev_median_psf = psf_data.median() if len(psf_data) >= 5 else None

        # District median PSF for same districts
        dev_districts = grp["district"].dropna().unique()
        district_psf = tx[
            tx["district"].isin(dev_districts) & (tx["rate_per_sqft"] > 0)
        ]["rate_per_sqft"].median()

        psf_premium_pct = None
        if dev_median_psf and district_psf and district_psf > 0:
            psf_premium_pct = ((dev_median_psf - district_psf) / district_psf) * 100

        # Secondary market ratio: % of their off-plan units re-sold as secondary
        offplan_projects = set(
            grp[grp["sale_type"] == "off-plan"]["project_name"].dropna().unique()
        )
        secondary_in_offplan = len(
            tx[
                (tx["sale_sequence"] == "secondary")
                & (tx["project_name"].isin(offplan_projects))
            ]
        )
        total_offplan = len(grp[grp["sale_type"] == "off-plan"])
        secondary_market_ratio = (
            (secondary_in_offplan / total_offplan * 100) if total_offplan >= 5 else None
        )

        # Composite score (0–100)
        # PSF premium (30 pts): normalise +20% = 100 pts
        psf_score = 0.0
        if psf_premium_pct is not None:
            psf_score = max(0, min(30, (psf_premium_pct / 20) * 30))

        # Secondary market ratio (25 pts): higher ratio = more demand for resale = better
        sec_score = 0.0
        if secondary_market_ratio is not None:
            sec_score = max(0, min(25, (secondary_market_ratio / 50) * 25))

        # Pipeline velocity (25 pts): use project_count & total_tx as proxy
        # More projects with consistent sales = higher velocity
        velocity_score = min(25, (project_count / 10) * 25)

        # Scale (20 pts): log-normalised total tx, up to 1000 tx = 20 pts
        import math
        scale_score = min(20, (math.log10(max(1, total_tx)) / math.log10(1000)) * 20)

        composite = psf_score + sec_score + velocity_score + scale_score

        results.append({
            "developer_name": dev,
            "project_count": int(project_count),
            "total_tx": int(total_tx),
            "psf_premium_pct": round(psf_premium_pct, 1) if psf_premium_pct is not None else None,
            "secondary_market_ratio": round(secondary_market_ratio, 1) if secondary_market_ratio is not None else None,
            "pipeline_velocity": round(velocity_score / 25 * 100, 1),
            "composite_score": round(composite, 1),
        })

    return sorted(results, key=lambda x: x["composite_score"], reverse=True)


def main():
    print("Loading data...")
    tx, sc = load_data()

    print(f"  Transactions: {len(tx):,}")
    print(f"  Service charge entries: {len(sc)}")

    proj_to_dev = build_project_developer_map(sc)
    print(f"  Project→developer mappings: {len(proj_to_dev)}")

    scores = compute_scores(tx, proj_to_dev)
    print(f"  Developers scored: {len(scores)}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)

    print(f"Output: {OUT_PATH}")
    if scores:
        top = scores[0]
        print(f"Top developer: {top['developer_name']} (score {top['composite_score']})")


if __name__ == "__main__":
    main()
