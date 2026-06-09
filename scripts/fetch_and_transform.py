#!/usr/bin/env python3
"""
ADInteract Data Pipeline — Fetch & Transform
Reads Abu Dhabi property transaction data from Google Sheets (or local CSV),
transforms it, and outputs Parquet, CSV, and JSON metadata files.
"""

import argparse
import csv
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import pyarrow as pa
import pyarrow.parquet as pq


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SPREADSHEET_ID = "1c9Xc6qsXfTwmnZ4gGMwvyCQ3bTDXBIO9ZyfnfwMl3tw"
SHEET_NAME = "AD Transactions"

SQM_TO_SQFT = 10.7639

SOURCE_COLUMNS = [
    "Asset Class",
    "Property Type",
    "Sale Application Date",
    "Property Sold Area (SQM)",
    "Land Plot Ground Area (SQM)",
    "Property Layout",
    "District",
    "Community",
    "Project Name",
    "Property Sale Price (AED)",
    "Property Sold Share",
    "Rate (AED per SQM)",
    "Sale Application Type",
    "Sale Sequence",
]

OUTPUT_COLUMNS = [
    "sale_date",
    "district",
    "community",
    "project_name",
    "asset_class",
    "property_type",
    "layout",
    "area_sqft",
    "land_area_sqft",
    "price_aed",
    "sold_share",
    "rate_per_sqft",
    "sale_type",
    "sale_sequence",
]


# ---------------------------------------------------------------------------
# Google Sheets fetching
# ---------------------------------------------------------------------------

def fetch_from_google_sheets() -> list[list[str]]:
    """Fetch all rows from the Google Sheet via gspread."""
    import gspread
    from google.oauth2.service_account import Credentials

    print("[1/5] Authenticating with Google Sheets API...")

    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    creds_file = os.environ.get("GOOGLE_CREDENTIALS_FILE")

    if creds_json:
        # Write JSON string to a temp file for gspread
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        tmp.write(creds_json)
        tmp.close()
        creds_path = tmp.name
    elif creds_file:
        creds_path = creds_file
    else:
        print("ERROR: Set GOOGLE_CREDENTIALS_JSON or GOOGLE_CREDENTIALS_FILE", file=sys.stderr)
        sys.exit(1)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    credentials = Credentials.from_service_account_file(creds_path, scopes=scopes)
    gc = gspread.authorize(credentials)

    print("[2/5] Opening spreadsheet and reading data...")
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet(SHEET_NAME)
    all_values = worksheet.get_all_values()

    # Clean up temp file if we created one
    if creds_json:
        os.unlink(creds_path)

    return all_values


def fetch_from_local_csv(csv_path: str) -> list[list[str]]:
    """Read all rows from a local CSV file."""
    print(f"[1/5] Reading local CSV: {csv_path}")
    print("[2/5] Parsing CSV data...")

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        return list(reader)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_date(raw: str) -> str | None:
    """Try to parse a date string into YYYY-MM-DD format."""
    raw = raw.strip()
    if not raw:
        return None

    # Try common formats
    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    # If it looks like a date with time
    for fmt in ("%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def parse_float(raw: str) -> float | None:
    """Parse a string to float, returning None for empty/invalid values."""
    raw = raw.strip().replace(",", "")
    if not raw or raw == "-" or raw.lower() == "n/a":
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def parse_int(raw: str) -> int | None:
    """Parse a string to int, returning None for empty/invalid values."""
    val = parse_float(raw)
    if val is None:
        return None
    return int(val)


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def transform_rows(raw_rows: list[list[str]]) -> list[dict]:
    """Transform raw sheet rows into cleaned dicts with output column names."""
    if not raw_rows:
        print("ERROR: No data received", file=sys.stderr)
        sys.exit(1)

    header = raw_rows[0]
    data_rows = raw_rows[1:]
    print(f"[3/5] Transforming {len(data_rows):,} rows...")

    # Build column index map
    col_map = {}
    for i, h in enumerate(header):
        col_map[h.strip()] = i

    # Verify required source columns exist
    missing = [c for c in SOURCE_COLUMNS if c not in col_map]
    if missing:
        print(f"WARNING: Missing columns: {missing}", file=sys.stderr)
        # Try to continue with what we have

    def get(row: list[str], col_name: str) -> str:
        idx = col_map.get(col_name)
        if idx is None or idx >= len(row):
            return ""
        return row[idx]

    records = []
    skipped = 0

    for row in data_rows:
        # Parse price and date first — skip if either is missing
        price_raw = get(row, "Property Sale Price (AED)")
        price_aed = parse_float(price_raw)
        if price_aed is None or price_aed <= 0:
            skipped += 1
            continue

        sale_date = parse_date(get(row, "Sale Application Date"))
        if sale_date is None:
            skipped += 1
            continue

        # Parse areas
        area_sqm = parse_float(get(row, "Property Sold Area (SQM)"))
        area_sqft = round(area_sqm * SQM_TO_SQFT, 2) if area_sqm else None

        land_sqm = parse_float(get(row, "Land Plot Ground Area (SQM)"))
        land_area_sqft = round(land_sqm * SQM_TO_SQFT, 2) if land_sqm else None

        # Calculate rate per sqft
        rate_per_sqft = None
        if area_sqft and area_sqft > 0:
            rate_per_sqft = round(price_aed / area_sqft, 2)

        # Normalize text fields
        sale_type = get(row, "Sale Application Type").strip().lower()
        layout = get(row, "Property Layout").strip().lower()
        district = get(row, "District").strip()
        community = get(row, "Community").strip()
        project_name = get(row, "Project Name").strip()
        asset_class = get(row, "Asset Class").strip()
        property_type = get(row, "Property Type").strip()

        sold_share = parse_float(get(row, "Property Sold Share"))
        sale_sequence = get(row, "Sale Sequence").strip().lower()

        records.append({
            "sale_date": sale_date,
            "district": district,
            "community": community,
            "project_name": project_name,
            "asset_class": asset_class,
            "property_type": property_type,
            "layout": layout if layout else "unclassified",
            "area_sqft": area_sqft,
            "land_area_sqft": land_area_sqft,
            "price_aed": price_aed,
            "sold_share": sold_share,
            "rate_per_sqft": rate_per_sqft,
            "sale_type": sale_type,
            "sale_sequence": sale_sequence,
        })

    print(f"    Kept {len(records):,} rows, skipped {skipped:,}")
    return records


# ---------------------------------------------------------------------------
# Output generation
# ---------------------------------------------------------------------------

def write_outputs(records: list[dict], output_dir: str) -> None:
    """Write Parquet, CSV, meta.json, and summary.json to output_dir."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"[4/5] Writing output files to {out}/...")

    # --- Build PyArrow table ---
    columns = {col: [] for col in OUTPUT_COLUMNS}
    for r in records:
        for col in OUTPUT_COLUMNS:
            columns[col].append(r.get(col))

    schema = pa.schema([
        pa.field("sale_date", pa.string()),
        pa.field("district", pa.string()),
        pa.field("community", pa.string()),
        pa.field("project_name", pa.string()),
        pa.field("asset_class", pa.string()),
        pa.field("property_type", pa.string()),
        pa.field("layout", pa.string()),
        pa.field("area_sqft", pa.float64()),
        pa.field("land_area_sqft", pa.float64()),
        pa.field("price_aed", pa.float64()),
        pa.field("sold_share", pa.float64()),
        pa.field("rate_per_sqft", pa.float64()),
        pa.field("sale_type", pa.string()),
        pa.field("sale_sequence", pa.string()),
    ])

    arrays = []
    for field in schema:
        col_data = columns[field.name]
        if field.type == pa.float64():
            arrays.append(pa.array(col_data, type=pa.float64()))
        elif field.type == pa.int32():
            arrays.append(pa.array(col_data, type=pa.int32()))
        else:
            arrays.append(pa.array(col_data, type=pa.string()))

    table = pa.table(arrays, schema=schema)

    # --- Write Parquet ---
    parquet_path = out / "transactions.parquet"
    pq.write_table(table, parquet_path, compression="zstd")
    parquet_size = parquet_path.stat().st_size / (1024 * 1024)
    print(f"    transactions.parquet ({parquet_size:.1f} MB)")

    # --- Write CSV ---
    csv_path = out / "transactions.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(records)
    csv_size = csv_path.stat().st_size / (1024 * 1024)
    print(f"    transactions.csv ({csv_size:.1f} MB)")

    # --- Build meta.json ---
    dates = sorted(set(r["sale_date"] for r in records if r["sale_date"]))
    districts = sorted(set(r["district"] for r in records if r["district"]))
    communities = sorted(set(r["community"] for r in records if r["community"]))
    property_types = sorted(set(r["property_type"] for r in records if r["property_type"]))
    projects = sorted(set(
        r["project_name"] for r in records
        if r["project_name"] and r["project_name"].lower() != "private"
    ))

    # Normalize layouts into standard buckets
    layout_values = set(r["layout"] for r in records if r["layout"])
    standard_layouts = [
        "studio", "1 bed", "2 beds", "3 beds",
        "4 beds", "5 beds", "6+ beds", "unclassified",
    ]
    # Keep standard order, only include those present in data
    layouts_out = [l for l in standard_layouts if l in layout_values]
    # Add any non-standard layouts at the end
    for lv in sorted(layout_values):
        if lv not in layouts_out:
            layouts_out.append(lv)

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    meta = {
        "lastUpdated": now_utc,
        "rowCount": len(records),
        "dateRange": {
            "min": dates[0] if dates else None,
            "max": dates[-1] if dates else None,
        },
        "districts": districts,
        "communities": communities,
        "propertyTypes": property_types,
        "layouts": layouts_out,
        "projects": projects,
    }

    meta_path = out / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"    meta.json")

    # --- Build summary.json (last 12 months) ---
    print("[5/5] Computing summary statistics (last 12 months)...")

    today = datetime.now()
    twelve_months_ago = today.replace(year=today.year - 1).strftime("%Y-%m-%d")

    recent = [r for r in records if r["sale_date"] >= twelve_months_ago]

    if recent:
        total_volume = len(recent)
        prices = [r["price_aed"] for r in recent if r["price_aed"]]
        rates = [r["rate_per_sqft"] for r in recent if r["rate_per_sqft"] and r["rate_per_sqft"] > 0]

        median_price = round(median(prices)) if prices else 0
        median_rate = round(median(rates)) if rates else 0
        total_value = round(sum(prices))
    else:
        total_volume = 0
        median_price = 0
        median_rate = 0
        total_value = 0

    summary = {
        "totalVolume": total_volume,
        "medianPrice": median_price,
        "medianRatePerSqft": median_rate,
        "totalValue": total_value,
        "periodLabel": "Last 12 months",
    }

    summary_path = out / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"    summary.json")

    print(f"\nDone. {len(records):,} records written to {out}/")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ADInteract Data Pipeline: fetch, transform, and output Abu Dhabi property transactions."
    )
    parser.add_argument(
        "--output-dir",
        default="static/data",
        help="Directory for output files (default: static/data)",
    )
    parser.add_argument(
        "--local-csv",
        default=None,
        help="Path to a local CSV file instead of fetching from Google Sheets",
    )
    args = parser.parse_args()

    try:
        # Fetch data
        if args.local_csv:
            raw_rows = fetch_from_local_csv(args.local_csv)
        else:
            raw_rows = fetch_from_google_sheets()

        # Transform
        records = transform_rows(raw_rows)

        if not records:
            print("ERROR: No valid records after transformation", file=sys.stderr)
            sys.exit(1)

        # Write outputs
        write_outputs(records, args.output_dir)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
