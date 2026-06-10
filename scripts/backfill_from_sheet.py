"""
backfill_from_sheet.py
----------------------
One-time script to pull missing rows from a temporary Google Sheet
and append them to the main ADInteract sheet.

Usage:
    python scripts/backfill_from_sheet.py

Requires GOOGLE_CREDENTIALS_FILE or GOOGLE_CREDENTIALS_JSON env var.
"""

import json
import os
import tempfile

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# ── Sheet config ────────────────────────────────────────────────────────────
MAIN_SHEET_ID   = "1c9Xc6qsXfTwmnZ4gGMwvyCQ3bTDXBIO9ZyfnfwMl3tw"
MAIN_GID        = 39002702

TEMP_SHEET_ID   = "1mdQMw2EttngsqNXx0OrlD1Fpdgr9DDY-dKovkQZH6wk"
TEMP_GID        = 1111258208

CHUNK_SIZE      = 5_000
DATE_COLUMN     = "Sale Application Date"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_credentials() -> Credentials:
    creds_file = os.environ.get("GOOGLE_CREDENTIALS_FILE")
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")

    if creds_file:
        return Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    elif creds_json:
        import base64
        if creds_json.strip().startswith("{"):
            info = json.loads(creds_json)
        else:
            padded = creds_json + "=" * (4 - len(creds_json) % 4)
            info = json.loads(base64.b64decode(padded).decode())
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(info, tmp)
        tmp.close()
        return Credentials.from_service_account_file(tmp.name, scopes=SCOPES)
    else:
        raise EnvironmentError("Set GOOGLE_CREDENTIALS_FILE or GOOGLE_CREDENTIALS_JSON")


def sheet_to_df(gc: gspread.Client, sheet_id: str, gid: int) -> pd.DataFrame:
    sh = gc.open_by_key(sheet_id)
    ws = next((s for s in sh.worksheets() if s.id == gid), sh.get_worksheet(0))
    print(f"  Reading '{ws.title}' (gid={ws.id}) from {sheet_id[:20]}…")
    rows = ws.get_all_values()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    print(f"  -> {len(df):,} rows, {len(df.columns)} columns")
    return df


def main():
    print("[1/4] Authenticating…")
    creds = get_credentials()
    gc = gspread.authorize(creds)

    print("[2/4] Reading main sheet…")
    main_df = sheet_to_df(gc, MAIN_SHEET_ID, MAIN_GID)

    print("[3/4] Reading temporary sheet…")
    temp_df = sheet_to_df(gc, TEMP_SHEET_ID, TEMP_GID)

    if temp_df.empty:
        print("Temp sheet is empty — nothing to backfill.")
        return

    # Normalise date columns to date objects for comparison
    for df in [main_df, temp_df]:
        if DATE_COLUMN in df.columns:
            df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors="coerce")

    if DATE_COLUMN not in main_df.columns or DATE_COLUMN not in temp_df.columns:
        print(f"ERROR: '{DATE_COLUMN}' not found in one of the sheets.")
        print(f"  Main columns:  {list(main_df.columns)}")
        print(f"  Temp columns:  {list(temp_df.columns)}")
        return

    max_main_date = main_df[DATE_COLUMN].max()
    print(f"\n  Max date in main sheet : {max_main_date.date()}")
    print(f"  Max date in temp sheet : {temp_df[DATE_COLUMN].max().date()}")

    # Only keep rows strictly newer than what's already in main
    new_rows = temp_df[temp_df[DATE_COLUMN] > max_main_date].copy()
    print(f"  New rows to append     : {len(new_rows):,}")

    if new_rows.empty:
        print("\nNothing to append — main sheet already has all dates.")
        return

    # Re-format dates as strings before uploading
    new_rows[DATE_COLUMN] = new_rows[DATE_COLUMN].dt.strftime("%Y-%m-%d")

    # Reorder columns to match main sheet
    shared_cols = [c for c in main_df.columns if c in new_rows.columns]
    new_rows = new_rows[shared_cols]

    print(f"\n[4/4] Appending {len(new_rows):,} rows to main sheet…")
    sh = gc.open_by_key(MAIN_SHEET_ID)
    ws = next((s for s in sh.worksheets() if s.id == MAIN_GID), sh.get_worksheet(0))

    existing_count = len(main_df)
    next_row = existing_count + 2  # +1 for header, +1 for 1-based index

    append_rows = new_rows.fillna("").astype(str).values.tolist()
    total_chunks = -(-len(append_rows) // CHUNK_SIZE)  # ceiling division

    for i in range(0, len(append_rows), CHUNK_SIZE):
        chunk = append_rows[i:i + CHUNK_SIZE]
        row_num = next_row + i
        ws.update(range_name=f"A{row_num}", values=chunk, value_input_option="RAW")
        chunk_num = i // CHUNK_SIZE + 1
        print(f"  Chunk {chunk_num}/{total_chunks} → rows {row_num}–{row_num + len(chunk) - 1}")

    print(f"\n✓ Done. Main sheet now has ~{existing_count + len(new_rows):,} rows.")


if __name__ == "__main__":
    main()
