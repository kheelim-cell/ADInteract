"""
Compute developer track record scores from ADREC transaction data.

Score breakdown (100 pts total):
  Market Dominance   50 pts — sales volume (25), project breadth (15), district diversity (10)
  Safety / Quality   50 pts — delivery rate (20), resale liquidity (15), price stability (15)

  Quality metrics are designed for new investors:
    Delivery rate   — % of off-plan projects with secondary market activity (proxy for completion)
    Resale liquidity — secondary market transaction volume (can you exit?)
    Price stability  — inverse of PSF coefficient of variation (consistent pricing = lower risk)

Outputs: static/data/developer_scores.json

Run from repo root:
  python scripts/compute_developer_scores.py
"""

import json
import math
from pathlib import Path

import pandas as pd

REPO_ROOT      = Path(__file__).parent.parent
TX_PATH        = REPO_ROOT / "static" / "data" / "transactions.parquet"
SC_PATH        = REPO_ROOT / "static" / "data" / "service_charges.json"
DEV_MAP_PATH   = Path(__file__).parent / "data" / "developer_mapping.json"
OUT_PATH       = REPO_ROOT / "static" / "data" / "developer_scores.json"


def load_data():
    tx = pd.read_parquet(TX_PATH)
    with open(SC_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    sc = raw["projects"] if isinstance(raw, dict) else raw
    return tx, sc


def build_project_developer_map(sc: list) -> dict:
    """Merge developer_mapping.json (all 245 pipeline projects) with service_charges.json fallback."""
    mapping = {}

    # Seed from service_charges (lower priority)
    for entry in sc:
        proj = entry.get("project_name", "").strip().lower()
        dev  = entry.get("developer_name", "").strip()
        if proj and dev:
            mapping[proj] = dev

    # Override/extend with the scraped+hardcoded developer mapping (higher priority)
    if DEV_MAP_PATH.exists():
        with open(DEV_MAP_PATH, encoding="utf-8") as f:
            dev_map = json.load(f)
        added = 0
        for proj_name, dev in dev_map.items():
            if dev and dev != "Unknown":
                key = proj_name.strip().lower()
                if key not in mapping:
                    added += 1
                mapping[key] = dev
        print(f"  developer_mapping.json: {len(dev_map)} entries ({added} new beyond service_charges)")
    else:
        print(f"  Warning: {DEV_MAP_PATH} not found — run fetch_developer_mapping.py first")

    return mapping


def compute_scores(tx: pd.DataFrame, proj_to_dev: dict) -> list:
    tx = tx.copy()
    tx["proj_key"]       = tx["project_name"].fillna("").str.strip().str.lower()
    tx["developer_name"] = tx["proj_key"].map(proj_to_dev)
    tx = tx[tx["developer_name"].notna() & (tx["developer_name"] != "")]

    results = []

    for dev, grp in tx.groupby("developer_name"):
        projects      = grp["project_name"].dropna().unique()
        total_tx      = len(grp)
        project_count = len(projects)

        dev_districts  = grp["district"].dropna().unique()
        district_count = len(dev_districts)

        # ── Delivery rate (proxy: % of off-plan projects with secondary sales) ─
        offplan_projects = set(
            grp[grp["sale_type"] == "off-plan"]["project_name"].dropna().unique()
        )
        delivered_projects = set(
            tx[
                (tx["sale_sequence"] == "secondary")
                & (tx["project_name"].isin(offplan_projects))
            ]["project_name"].dropna().unique()
        )
        delivery_rate = (
            len(delivered_projects) / len(offplan_projects) * 100
            if offplan_projects else None
        )

        # ── Resale liquidity (secondary tx volume across all their projects) ──
        secondary_tx = len(
            tx[
                (tx["sale_sequence"] == "secondary")
                & (tx["project_name"].isin(set(grp["project_name"].dropna().unique())))
            ]
        )

        # ── Price stability (inverse of PSF coefficient of variation) ─────────
        psf_data = grp[grp["rate_per_sqft"] > 0]["rate_per_sqft"]
        price_stability_pct = None
        if len(psf_data) >= 10:
            cv = psf_data.std() / psf_data.mean()   # coefficient of variation
            # CV of 0 = perfectly stable (100%), CV of 1+ = very volatile (0%)
            price_stability_pct = max(0, (1 - cv)) * 100

        # ── Market Dominance (50 pts) ─────────────────────────────────────────
        # Sales volume (25 pts): log-normalised, 5000 tx = full score
        scale_score     = min(25, (math.log10(max(1, total_tx)) / math.log10(5000)) * 25)
        # Project breadth (15 pts): 20+ projects = full score
        breadth_score   = min(15, (project_count / 20) * 15)
        # District diversity (10 pts): 5+ districts = full score
        diversity_score = min(10, (district_count / 5) * 10)

        # ── Safety / Quality (50 pts) ─────────────────────────────────────────
        # Delivery rate (20 pts): 80%+ projects delivered = full score
        delivery_score = 0.0
        if delivery_rate is not None:
            delivery_score = min(20, (delivery_rate / 80) * 20)
        else:
            delivery_score = 10.0  # neutral if no off-plan history

        # Resale liquidity (15 pts): log-normalised, 500 secondary tx = full score
        liquidity_score = min(15, (math.log10(max(1, secondary_tx)) / math.log10(500)) * 15)

        # Price stability (15 pts): 80%+ stability score = full score
        stability_score = 0.0
        if price_stability_pct is not None:
            stability_score = min(15, (price_stability_pct / 80) * 15)
        else:
            stability_score = 7.5  # neutral if insufficient data

        composite = (
            scale_score + breadth_score + diversity_score
            + delivery_score + liquidity_score + stability_score
        )

        results.append({
            "developer_name":    dev,
            "project_count":     int(project_count),
            "total_tx":          int(total_tx),
            "district_count":    int(district_count),
            "delivery_rate":     round(delivery_rate, 1) if delivery_rate is not None else None,
            "secondary_tx":      int(secondary_tx),
            "price_stability":   round(price_stability_pct, 1) if price_stability_pct is not None else None,
            "composite_score":   round(composite, 1),
            "score_breakdown": {
                "dominance":  round(scale_score + breadth_score + diversity_score, 1),
                "delivery":   round(delivery_score, 1),
                "liquidity":  round(liquidity_score, 1),
                "stability":  round(stability_score, 1),
            },
        })

    return sorted(results, key=lambda x: x["composite_score"], reverse=True)


def main():
    print("Loading data...")
    tx, sc = load_data()
    print(f"  Transactions: {len(tx):,}")
    print(f"  Service charge entries: {len(sc)}")

    proj_to_dev = build_project_developer_map(sc)
    print(f"  Project->developer mappings: {len(proj_to_dev)}")

    scores = compute_scores(tx, proj_to_dev)
    print(f"  Developers scored: {len(scores)}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)

    print(f"\nOutput: {OUT_PATH}")
    print("\nTop 5 developers:")
    for i, d in enumerate(scores[:5], 1):
        b = d["score_breakdown"]
        print(f"  {i}. {d['developer_name']} — {d['composite_score']}/100")
        print(f"     dominance={b['dominance']}  delivery={b['delivery']}  liquidity={b['liquidity']}  stability={b['stability']}")


if __name__ == "__main__":
    main()
