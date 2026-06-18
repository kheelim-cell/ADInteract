"""
transform_rental.py
-------------------
Reads scripts/data/rental_raw.json produced by fetch_rental.py and outputs:
  • static/data/rental.parquet   — normalized Parquet for DuckDB-WASM
  • static/data/rental_meta.json — filter dropdown options + last_updated

Run:
    python scripts/transform_rental.py
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# ─── Paths ─────────────────────────────────────────────────────────────────────
INPUT_JSON    = Path("scripts/data/rental_raw.json")
OUTPUT_DIR    = Path("static/data")
OUTPUT_PARQUET = OUTPUT_DIR / "rental.parquet"
OUTPUT_META   = OUTPUT_DIR / "rental_meta.json"
# ───────────────────────────────────────────────────────────────────────────────

# Canonical sort order for layouts (used for meta.json ordering)
LAYOUT_ORDER = [
    "all beds",
    "studio",
    "1 bed",
    "2 beds",
    "3 beds",
    "4 beds",
    "5 beds",
]

# Canonical typology normalisation (source strings can vary)
TYPOLOGY_ALIASES = {
    "all property types": "All property types",
    "apartment / duplex":  "Apartment / Duplex",
    "apartment":           "Apartment / Duplex",
    "duplex":              "Apartment / Duplex",
    "villa":               "Villa",
    "townhouse":           "Villa",
}

RENT_TYPE_ALIASES = {
    "all types": "All types",
    "new":       "New",
    "renew":     "Renew",
    "renewal":   "Renew",
}


def normalise_str(s) -> str | None:
    """Strip and title-case a string value, return None if blank/null."""
    if s is None:
        return None
    v = str(s).strip()
    if not v:
        return None
    return v.title()  # "AL REEM ISLAND" → "Al Reem Island"


def normalise_layout(s) -> str | None:
    v = normalise_str(s)
    if not v:
        return None
    return v.lower().strip()  # keep as lowercase ("2 beds") to match LAYOUT_ORDER


def normalise_typology(s) -> str | None:
    v = normalise_str(s)
    if not v:
        return None
    key = v.lower()
    return TYPOLOGY_ALIASES.get(key, v)


def normalise_rent_type(s) -> str | None:
    v = normalise_str(s)
    if not v:
        return None
    key = v.lower()
    return RENT_TYPE_ALIASES.get(key, v)


def sort_layouts(layouts: list[str]) -> list[str]:
    """Return layouts sorted by canonical order, with unknowns at the end."""
    known = [l for l in LAYOUT_ORDER if l in layouts]
    unknown = sorted(set(layouts) - set(known))
    return known + unknown


def main() -> None:
    print("[transform_rental] === Rental Index Transform ===")

    if not INPUT_JSON.exists():
        print(f"⚠ {INPUT_JSON} not found — fetch_rental.py produced no file. Rental parquet unchanged.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load raw JSON ──────────────────────────────────────────────────────
    raw: list[dict] = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
    print(f"[transform_rental] Loaded {len(raw):,} raw records")

    df = pd.DataFrame(raw)

    # ── Rename columns ─────────────────────────────────────────────────────
    rename_map = {
        "project_id":       "project_id",
        "project_name":     "project_name",
        "project_number":   "project_number",
        "municipality":     "municipality",
        "municipality_id":  "municipality_id",
        "district":         "district",
        "district_id":      "district_id",
        "community":        "community",
        "community_id":     "community_id",
        "typology":         "typology",
        "layout":           "layout",
        "lower_rent_value": "lower_rent",
        "avg_rent_value":   "median_rent",
        "upper_rent_value": "upper_rent",
        "year":             "year",
        "rent_type":        "rent_type",
    }
    # Keep only columns that exist in the data
    existing = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=existing)

    # ── String normalisation ───────────────────────────────────────────────
    for col in ["project_name", "municipality", "district", "community"]:
        if col in df.columns:
            df[col] = df[col].apply(normalise_str)

    if "typology" in df.columns:
        df["typology"] = df["typology"].apply(normalise_typology)
    if "layout" in df.columns:
        df["layout"] = df["layout"].apply(normalise_layout)
    if "rent_type" in df.columns:
        df["rent_type"] = df["rent_type"].apply(normalise_rent_type)

    # ── Numeric coercion ───────────────────────────────────────────────────
    for col in ["lower_rent", "median_rent", "upper_rent"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    for col in ["project_id", "municipality_id", "district_id", "community_id"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # ── Drop rows with no usable rent data ────────────────────────────────
    before = len(df)
    df = df.dropna(subset=["median_rent", "year"])
    print(f"[transform_rental] Dropped {before - len(df):,} rows (null median_rent or year)")

    # ── Final column order ─────────────────────────────────────────────────
    final_cols = [
        "project_id",
        "project_name",
        "municipality",
        "district",
        "community",
        "typology",
        "layout",
        "lower_rent",
        "median_rent",
        "upper_rent",
        "year",
        "rent_type",
    ]
    final_cols = [c for c in final_cols if c in df.columns]
    df = df[final_cols]

    print(f"[transform_rental] Clean rows: {len(df):,}")

    # ── Write Parquet ──────────────────────────────────────────────────────
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(
        table,
        OUTPUT_PARQUET,
        compression="zstd",
        compression_level=9,
    )
    print(f"[transform_rental] Wrote Parquet → {OUTPUT_PARQUET}  ({OUTPUT_PARQUET.stat().st_size / 1024:.1f} KB)")

    # ── Build meta.json ────────────────────────────────────────────────────
    def unique_sorted(series) -> list:
        return sorted(series.dropna().unique().tolist())

    layouts_raw = unique_sorted(df["layout"]) if "layout" in df.columns else []
    layouts_ordered = sort_layouts(layouts_raw)

    years_raw = unique_sorted(df["year"]) if "year" in df.columns else []
    years = [int(y) for y in years_raw if y is not None]

    meta = {
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "rowCount": int(len(df)),
        "years": years,
        "latestYear": max(years) if years else None,
        "districts": unique_sorted(df["district"]) if "district" in df.columns else [],
        "municipalities": unique_sorted(df["municipality"]) if "municipality" in df.columns else [],
        "communities": unique_sorted(df["community"]) if "community" in df.columns else [],
        "projects": unique_sorted(df["project_name"]) if "project_name" in df.columns else [],
        "typologies": unique_sorted(df["typology"]) if "typology" in df.columns else [],
        "layouts": layouts_ordered,
        "rentTypes": unique_sorted(df["rent_type"]) if "rent_type" in df.columns else [],
    }

    OUTPUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[transform_rental] Wrote meta → {OUTPUT_META}")
    print(f"  years={meta['years']}, districts={len(meta['districts'])}, projects={len(meta['projects'])}")

    print("[transform_rental] Done.")


if __name__ == "__main__":
    main()
