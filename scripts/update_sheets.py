"""
update_sheets.py
----------------
Uploads the downloaded ADREC CSV to the Google Sheet so it stays
in sync as a source-of-truth backup.

Requires the GOOGLE_CREDENTIALS_JSON environment variable to be
set to a base64-encoded Google Service Account JSON key.

Sheet  : https://docs.google.com/spreadsheets/d/1c9Xc6qsXfTwmnZ4gGMwvyCQ3bTDXBIO9ZyfnfwMl3tw
Tab GID: 39002702
"""

import base64
import json
import math
import os

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

SHEET_ID      = "1c9Xc6qsXfTwmnZ4gGMwvyCQ3bTDXBIO9ZyfnfwMl3tw"
WORKSHEET_GID = 39002702
# Allow backfill_adrec.py to override the source CSV path via env var
INPUT_CSV     = os.environ.get("BACKFILL_CSV_OVERRIDE", "scripts/data/adrec_raw.csv")
CHUNK_SIZE    = 5_000   # rows per gspread batch call


def load_credentials(env_var: str) -> dict:
    """
    Decode the service account JSON from an env var.
    Handles three formats:
      1. Raw JSON string (secret was pasted as-is)
      2. Base64-encoded JSON (recommended)
      3. Base64 with missing padding
    """
    value = os.environ.get(env_var, "").strip()
    if not value:
        raise EnvironmentError(
            f"{env_var} env var is not set. "
            "Add it as a GitHub Actions secret."
        )

    # Try raw JSON first (starts with '{')
    if value.startswith("{"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

    # Try base64 decode (fix padding if needed)
    try:
        padded = value + "=" * (4 - len(value) % 4)
        decoded = base64.b64decode(padded)
        return json.loads(decoded.decode("utf-8"))
    except Exception as exc:
        raise ValueError(
            f"Could not decode {env_var} as JSON or base64-encoded JSON.\n"
            f"Error: {exc}\n"
            f"To fix: re-encode your service account JSON file and update the secret:\n"
            f"  PowerShell: [Convert]::ToBase64String([IO.File]::ReadAllBytes('credentials.json'))\n"
            f"  Linux/Mac:  base64 -i credentials.json | tr -d '\\n'"
        )


def update():
    creds_json = load_credentials("GOOGLE_CREDENTIALS_JSON")
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
    gc = gspread.authorize(creds)

    sh = gc.open_by_key(SHEET_ID)

    # Find the target worksheet by its numeric GID
    ws = None
    for sheet in sh.worksheets():
        if sheet.id == WORKSHEET_GID:
            ws = sheet
            break
    if ws is None:
        print(f"Warning: tab with gid={WORKSHEET_GID} not found. Using first sheet.")
        ws = sh.get_worksheet(0)

    print(f"Target sheet: '{ws.title}' (gid={ws.id})")

    # Handle sentinel: fetch_adrec.py writes an empty file when sheet is already
    # up to date (start_date > today). Nothing to do in that case.
    if os.path.getsize(INPUT_CSV) == 0:
        print("CSV is empty (sheet already up to date) — nothing to append.")
        return

    # Load new CSV from ADREC scrape
    new_df = pd.read_csv(INPUT_CSV, low_memory=False).fillna("")
    print(f"New CSV: {len(new_df):,} rows × {len(new_df.columns)} columns")

    # Check how many rows already exist in the sheet
    existing_vals = ws.col_values(1)  # first column — header + data
    existing_row_count = max(0, len(existing_vals) - 1)  # subtract header
    print(f"Existing sheet rows: {existing_row_count:,}")

    if existing_row_count == 0:
        # Sheet is empty — do a full upload
        print("Sheet is empty — doing full upload…")
        rows = [new_df.columns.tolist()] + new_df.astype(str).values.tolist()
        total_chunks = math.ceil(len(rows) / CHUNK_SIZE)
        for i in range(0, len(rows), CHUNK_SIZE):
            chunk = rows[i : i + CHUNK_SIZE]
            start_row = i + 1
            ws.update(range_name=f"A{start_row}", values=chunk, value_input_option="RAW")
            chunk_num = i // CHUNK_SIZE + 1
            print(f"  Chunk {chunk_num}/{total_chunks} uploaded")
        print(f"Full upload complete: {len(new_df):,} rows.")
        return

    # Sheet has data — find the max date already in the sheet and append only newer rows.
    # NOTE: the CSV's date column name and the Sheet's date column name can
    # legitimately differ — ADREC has renamed this column over time
    # ("Sale Application Date" -> "Registration" etc.) while keeping the same
    # column *position*. Appends below are positional (raw values, no header
    # realignment), so each side just needs its OWN fuzzy match against the
    # same candidate list — they don't need to match each other textually.
    date_col_candidates = [
        "Sale Application Date", "Registration Date", "Registration",
        "Date", "Transaction Date",
    ]

    def find_col_index(header: list[str], candidates: list[str]) -> int | None:
        """1-based index of the first candidate name found in header (case-insensitive)."""
        lower_header = [h.strip().lower() for h in header]
        for cand in candidates:
            cand_l = cand.strip().lower()
            if cand_l in lower_header:
                return lower_header.index(cand_l) + 1
        return None

    date_col = next((c for c in date_col_candidates if c in new_df.columns), None)
    if date_col is None:
        raise RuntimeError(
            f"Could not identify date column in CSV. "
            f"Tried: {date_col_candidates}. "
            f"Got columns: {list(new_df.columns)[:10]}"
        )

    # Find date column position in the sheet header — independently fuzzy-matched,
    # not required to be the same literal string as `date_col` above.
    header_row = ws.row_values(1)
    date_col_idx = find_col_index(header_row, date_col_candidates)
    if date_col_idx is None:
        raise RuntimeError(
            f"No recognised date column found in sheet header. "
            f"Tried: {date_col_candidates}. "
            f"Sheet header: {header_row[:10]}"
        )

    # Safety check: appends below are positional (raw values written by column
    # index, not by name) so a column-count mismatch would silently misalign
    # data instead of erroring. Fail loudly instead.
    if len(header_row) != len(new_df.columns):
        raise RuntimeError(
            f"Column count mismatch: sheet header has {len(header_row)} columns "
            f"({header_row}), CSV has {len(new_df.columns)} columns "
            f"({list(new_df.columns)}). Appends are positional — refusing to "
            f"write misaligned data. Re-align the sheet header or CSV column "
            f"order before retrying."
        )

    # Parse existing dates to find the max.
    # dayfirst=False, matching transform.py's exact convention (and comment)
    # for the same reason: Google Sheets' API returns date-typed cells back
    # as M/D/YYYY (US locale) regardless of what format they were written
    # in, not the original write format. Using dayfirst=True here silently
    # misread any date with day <= 12, producing bogus max-dates (e.g. a
    # date meant as month=12 day=05 got flipped to day=12 month=05, or
    # vice versa) — that's what caused two months of "no new rows to
    # append" silently, since the wrongly-computed max ended up in the
    # future. See the sanity check below for defense against this class
    # of bug recurring from any other cause.
    existing_dates_raw = ws.col_values(date_col_idx)[1:]  # skip header
    existing_dates = pd.to_datetime(existing_dates_raw, dayfirst=False, errors="coerce").dropna()
    if len(existing_dates) == 0:
        raise RuntimeError(
            "No parseable dates found in sheet date column. "
            "Check that the sheet has data and dates are in a recognised format."
        )

    max_existing_date = existing_dates.max().date()
    print(f"Max date already in sheet: {max_existing_date}")

    # Sanity check: a max date in the future (or implausibly old) means the
    # parse is almost certainly wrong, not that the sheet genuinely has
    # future-dated transactions. Fail loudly instead of silently deciding
    # "nothing new to append" forever — exactly how this bug went
    # unnoticed for two months in the first place.
    today = pd.Timestamp.now().date()
    if max_existing_date > today:
        raise RuntimeError(
            f"Max date already in sheet ({max_existing_date}) is in the future — "
            f"this means date parsing is wrong, not that the sheet has future "
            f"transactions. Refusing to proceed (would silently skip all real "
            f"new rows). Check the sheet's actual date column format."
        )

    # Keep only rows with a date strictly after the sheet's max date.
    # dayfirst=False here too — ADREC's own CSV export is ISO (YYYY-MM-DD),
    # unambiguous regardless of this flag (per transform.py's comment), so
    # this specific call was never the active bug, but kept consistent with
    # the rest of this file rather than leaving a misleading dayfirst=True.
    new_df[date_col] = pd.to_datetime(new_df[date_col], dayfirst=False, errors="coerce")
    truly_new = new_df[new_df[date_col].dt.date > max_existing_date].copy()
    truly_new[date_col] = truly_new[date_col].dt.strftime("%Y-%m-%d")

    if len(truly_new) == 0:
        print("No new rows to append — sheet is already up to date.")
        return

    print(f"Appending {len(truly_new):,} new rows (dates after {max_existing_date})…")
    append_rows = truly_new.astype(str).values.tolist()
    next_row = existing_row_count + 2  # +1 for 1-based index, +1 for header row

    total_chunks = math.ceil(len(append_rows) / CHUNK_SIZE)
    for i in range(0, len(append_rows), CHUNK_SIZE):
        chunk = append_rows[i : i + CHUNK_SIZE]
        row_num = next_row + i
        ws.update(range_name=f"A{row_num}", values=chunk, value_input_option="RAW")
        chunk_num = i // CHUNK_SIZE + 1
        print(f"  Chunk {chunk_num}/{total_chunks} appended (from row {row_num})")

    print(f"Append complete. Sheet now has ~{existing_row_count + len(truly_new):,} rows.")


if __name__ == "__main__":
    update()
