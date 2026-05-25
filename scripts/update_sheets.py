"""
update_sheets.py
----------------
Uploads the downloaded ADREC CSV to the Google Sheet so it stays
in sync as a source-of-truth backup.

Requires the GOOGLE_CREDENTIALS_JSON environment variable to be
set to a base64-encoded Google Service Account JSON key.

Sheet  : https://docs.google.com/spreadsheets/d/1ZK7oA_qAwTOdaNhy8vE6Oh7omT6TRAdOI0bXmEtysMg
Tab GID: 39002702
"""

import base64
import json
import math
import os

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

SHEET_ID      = "1ZK7oA_qAwTOdaNhy8vE6Oh7omT6TRAdOI0bXmEtysMg"
WORKSHEET_GID = 39002702
INPUT_CSV     = "scripts/data/adrec_raw.csv"
CHUNK_SIZE    = 5_000   # rows per gspread batch call


def update():
    creds_b64 = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
    if not creds_b64:
        raise EnvironmentError(
            "GOOGLE_CREDENTIALS_JSON env var is not set. "
            "Add it as a GitHub Actions secret (base64-encoded service account JSON)."
        )

    # Strip whitespace and fix any missing base64 padding
    creds_b64 = creds_b64.strip()
    creds_b64 += "=" * (4 - len(creds_b64) % 4)
    creds_json = json.loads(base64.b64decode(creds_b64))
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

    # Load CSV
    df = pd.read_csv(INPUT_CSV, low_memory=False).fillna("")
    print(f"Uploading {len(df):,} rows × {len(df.columns)} columns…")

    # Build as list-of-lists: header + data rows
    rows = [df.columns.tolist()] + df.astype(str).values.tolist()

    # Clear existing content first
    ws.clear()

    # Upload in chunks (gspread has a 10 MB per-request limit)
    total_chunks = math.ceil(len(rows) / CHUNK_SIZE)
    for i in range(0, len(rows), CHUNK_SIZE):
        chunk = rows[i : i + CHUNK_SIZE]
        start_row = i + 1
        ws.update(f"A{start_row}", chunk, value_input_option="RAW")
        chunk_num = i // CHUNK_SIZE + 1
        print(f"  Chunk {chunk_num}/{total_chunks} uploaded (rows {start_row}–{start_row + len(chunk) - 1})")

    print("Google Sheet updated successfully.")


if __name__ == "__main__":
    update()
