"""
transform.py
------------
Reads the raw ADREC CSV (scripts/data/adrec_raw.csv), cleans and
transforms it, then writes:
  - static/data/transactions.parquet   (ZSTD compressed, DuckDB-WASM compatible)
  - static/data/meta.json              (row count, date range, dropdown lists)

Transformations applied:
  - SQM → SQFT  (× 10.7639)
  - AED/sqm → AED/sqft
  - Dates parsed to ISO 8601 (YYYY-MM-DD)
  - property_type lowercased and normalised
  - layout mapped to standard labels (studio, 1 bed, 2 beds …)
  - sale_type mapped to: off-plan | ready | court-mandated
  - Rows with no sale_date or price_aed dropped
  - Only the 6 allowed property types retained
"""

import json
import os
from datetime import datetime, timezone

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

INPUT_CSV       = "scripts/data/adrec_raw.csv"
OUTPUT_PARQUET  = "static/data/transactions.parquet"
OUTPUT_META     = "static/data/meta.json"

SQM_TO_SQFT = 10.7639

ALLOWED_PROPERTY_TYPES = {
    "apartment",
    "duplex",
    "townhouse / attached villa",
    "villa",
    "office",
    "retail",
}

# Flexible column mapping — first match wins (case-insensitive)
COLUMN_MAP: dict[str, list[str]] = {
    "sale_date":     ["Sale Application Date", "Registration Date", "Registration",
                      "Date", "Transaction Date"],
    "district":      ["District"],
    "community":     ["Community"],
    "project_name":  ["Project Name", "Project"],
    "asset_class":   ["Asset Class", "Asset Type"],
    "property_type": ["Property Type"],
    "layout":        ["Property Layout", "Layout"],
    "area_sqm":      ["Property Sold Area (SQM)", "Property Sold Area", "Sold Area (sqm)",
                      "Sold Area", "Built-up Area (sqm)"],
    "land_area_sqm": ["Land Plot Ground Area (SQM)", "Land Plot Ground Area",
                      "Plot Area (sqm)", "Plot Area", "Land Area (sqm)"],
    "price_aed":     ["Property Sale Price (AED)", "Property Sale Price",
                      "Sale Price", "Price (AED)", "Price"],
    "sold_share":    ["Property Sold Share", "Sold Share", "Share"],
    "rate_aed_sqm":  ["Rate (AED per SQM)", "Rate ( ب /sqm )", "Rate (AED/sqm)",
                      "Rate ( Ð /sqm )", "Rate (D /sqm)", "Rate"],
    "sale_type":     ["Sale Application Type", "Sale Type"],
    "sale_sequence": ["Sale Sequence", "Sequence"],
}

LAYOUT_MAP = {
    "studio": "studio",
    "0": "studio",
    "1": "1 bed",   "1 bed": "1 bed",   "1br": "1 bed",   "1 bedroom": "1 bed",
    "2": "2 beds",  "2 beds": "2 beds",  "2br": "2 beds",  "2 bedrooms": "2 beds",
    "3": "3 beds",  "3 beds": "3 beds",  "3br": "3 beds",  "3 bedrooms": "3 beds",
    "4": "4 beds",  "4 beds": "4 beds",  "4br": "4 beds",  "4 bedrooms": "4 beds",
    "5": "5 beds",  "5 beds": "5 beds",  "5br": "5 beds",  "5 bedrooms": "5 beds",
}


def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower_map = {c.lower().strip(): c for c in df.columns}
    for cand in candidates:
        match = lower_map.get(cand.lower().strip())
        if match:
            return match
    return None


def normalise_layout(v) -> str:
    if pd.isna(v):
        return "unclassified"
    s = str(v).strip().lower()
    if s in ("", "nan", "unclassified", "n/a", "none"):
        return "unclassified"
    if s in LAYOUT_MAP:
        return LAYOUT_MAP[s]
    # 6+ bedrooms
    try:
        n = int(s.split()[0])
        if n >= 6:
            return "6+ beds"
        if n == 0:
            return "studio"
        return f"{n} bed{'s' if n > 1 else ''}"
    except (ValueError, IndexError):
        pass
    return s


def normalise_sale_type(v) -> str:
    if pd.isna(v):
        return "unknown"
    s = str(v).strip().lower()
    if "off" in s or "plan" in s:
        return "off-plan"
    if "ready" in s or "complet" in s or "resale" in s or "second" in s:
        return "ready"
    if "court" in s or "mandated" in s or "judicial" in s:
        return "court-mandated"
    return s


def normalise_sequence(v) -> str:
    if pd.isna(v):
        return "unknown"
    s = str(v).strip().lower()
    if "primary" in s or "first" in s or "1st" in s or "new" in s:
        return "primary"
    if "secondary" in s or "resale" in s or "second" in s:
        return "secondary"
    return s


def transform():
    os.makedirs("static/data", exist_ok=True)

    print(f"Reading {INPUT_CSV}…")
    df = pd.read_csv(INPUT_CSV, low_memory=False)
    print(f"  Raw rows: {len(df):,}  |  Columns: {list(df.columns)}")

    # ── Map columns ────────────────────────────────────────────────────────
    mapped: dict[str, pd.Series] = {}
    for out_col, candidates in COLUMN_MAP.items():
        src = find_col(df, candidates)
        if src:
            mapped[out_col] = df[src]
            print(f"  {out_col:16s} ← '{src}'")
        else:
            mapped[out_col] = pd.Series([None] * len(df))
            print(f"  {out_col:16s} ← NOT FOUND  (tried: {candidates[:3]})")

    out = pd.DataFrame(mapped)

    # ── Parse dates ────────────────────────────────────────────────────────
    # Google Sheets Drive-export emits dates as M/D/YYYY (US locale), so
    # dayfirst=False is correct.  ADREC exports ISO (YYYY-MM-DD) which is
    # unambiguous regardless of this flag.
    out["sale_date"] = pd.to_datetime(
        out["sale_date"], dayfirst=False, errors="coerce"
    ).dt.date

    # ── Drop rows with no date / price ─────────────────────────────────────
    # Google Sheets exports numbers with thousands separators (e.g. "3,314,610")
    # Strip commas from all numeric columns before parsing.
    for num_col in ("price_aed", "area_sqm", "land_area_sqm", "sold_share", "rate_aed_sqm"):
        if num_col in out.columns:
            out[num_col] = (
                out[num_col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.strip()
            )

    out["price_aed"] = pd.to_numeric(out["price_aed"], errors="coerce")

    # Diagnostic: show breakdown before dropping
    null_dates  = out["sale_date"].isna().sum()
    null_prices = out["price_aed"].isna().sum()
    print(f"  Null dates: {null_dates:,}  |  Null/zero prices: {null_prices:,}")

    before = len(out)
    out = out.dropna(subset=["sale_date", "price_aed"])
    out = out[out["price_aed"] > 0]
    print(f"  Dropped {before - len(out):,} rows (null date/price). Remaining: {len(out):,}")

    # ── Drop today's provisional/unconfirmed transactions ──────────────────
    today = datetime.now(timezone.utc).date()
    before = len(out)
    out = out[out["sale_date"] < today]
    print(f"  Dropped {before - len(out):,} rows (today={today}, provisional). Remaining: {len(out):,}")

    # ── Normalise property_type & filter to allowed set ───────────────────
    out["property_type"] = out["property_type"].astype(str).str.strip().str.lower()
    before = len(out)
    out = out[out["property_type"].isin(ALLOWED_PROPERTY_TYPES)]
    print(f"  Dropped {before - len(out):,} rows (excluded property types). Remaining: {len(out):,}")

    # ── Unit conversions ───────────────────────────────────────────────────
    out["area_sqft"]      = pd.to_numeric(out["area_sqm"],      errors="coerce") * SQM_TO_SQFT
    out["land_area_sqft"] = pd.to_numeric(out["land_area_sqm"], errors="coerce") * SQM_TO_SQFT

    # AED/sqft from rate column (rate_aed_sqm ÷ 10.7639)
    out["rate_per_sqft"] = pd.to_numeric(out["rate_aed_sqm"], errors="coerce") / SQM_TO_SQFT

    # Fallback: derive from price / area
    mask = out["rate_per_sqft"].isna() & out["area_sqft"].notna() & (out["area_sqft"] > 0)
    out.loc[mask, "rate_per_sqft"] = out.loc[mask, "price_aed"] / out.loc[mask, "area_sqft"]

    # ── Normalise categorical fields ───────────────────────────────────────
    out["layout"]        = out["layout"].apply(normalise_layout)
    out["sale_type"]     = out["sale_type"].apply(normalise_sale_type)
    out["sale_sequence"] = out["sale_sequence"].apply(normalise_sequence)

    # Clean strings
    for col in ("district", "community", "project_name", "asset_class"):
        out[col] = out[col].astype(str).str.strip().replace({"nan": "", "None": ""})

    # Title-case display strings: "AL REEM ISLAND" → "Al Reem Island"
    # Applied after strip/replace so empty strings are skipped cleanly.
    def _title(v: str) -> str:
        return v.title() if v else v

    for col in ("district", "community", "project_name"):
        out[col] = out[col].apply(_title)

    # ── Build final DataFrame ──────────────────────────────────────────────
    final = pd.DataFrame({
        "sale_date":      pd.to_datetime(out["sale_date"]),
        "district":       out["district"],
        "community":      out["community"],
        "project_name":   out["project_name"],
        "asset_class":    out["asset_class"],
        "property_type":  out["property_type"],
        "layout":         out["layout"],
        "area_sqft":      pd.to_numeric(out["area_sqft"],      errors="coerce"),
        "land_area_sqft": pd.to_numeric(out["land_area_sqft"], errors="coerce"),
        "price_aed":      pd.to_numeric(out["price_aed"],      errors="coerce"),
        "sold_share":     pd.to_numeric(out["sold_share"],      errors="coerce").fillna(1.0),
        "rate_per_sqft":  pd.to_numeric(out["rate_per_sqft"],  errors="coerce"),
        "sale_type":      out["sale_type"],
        "sale_sequence":  out["sale_sequence"],
    }).dropna(subset=["sale_date", "price_aed"])

    print(f"  Final row count: {len(final):,}")

    # ── Write Parquet (ZSTD compressed) ────────────────────────────────────
    table = pa.Table.from_pandas(final, preserve_index=False)
    pq.write_table(table, OUTPUT_PARQUET, compression="zstd")
    size_mb = os.path.getsize(OUTPUT_PARQUET) / 1_048_576
    print(f"  Wrote {OUTPUT_PARQUET}  ({size_mb:.1f} MB)")

    # ── Write meta.json ────────────────────────────────────────────────────
    def clean_list(series: pd.Series) -> list:
        return sorted({
            str(v).strip()
            for v in series.dropna().unique()
            if str(v).strip() not in ("", "nan", "None")
        })

    meta = {
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "rowCount":    int(len(final)),
        "dateRange": {
            "min": str(final["sale_date"].min().date()),
            "max": str(final["sale_date"].max().date()),
        },
        "districts":     clean_list(final["district"]),
        "communities":   clean_list(final["community"]),
        "propertyTypes": clean_list(final["property_type"]),
        "layouts":       clean_list(final["layout"]),
        "projects":      clean_list(final["project_name"]),
    }

    with open(OUTPUT_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    print(f"  Wrote {OUTPUT_META}")
    print("Transform complete.")


if __name__ == "__main__":
    transform()
