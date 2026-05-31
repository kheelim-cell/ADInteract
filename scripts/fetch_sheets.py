"""
fetch_sheets.py
---------------
Downloads the source-of-truth Google Sheet as a CSV and saves it to
scripts/data/adrec_raw.csv for the downstream transform step.

Uses the Drive export API with service-account credentials — much faster
than cell-by-cell gspread.get_all_values() for 100K+ row sheets.

Requires the GOOGLE_CREDENTIALS_JSON environment variable to be set to a
base64-encoded Google Service Account JSON key.

Sheet  : https://docs.google.com/spreadsheets/d/1c9Xc6qsXfTwmnZ4gGMwvyCQ3bTDXBIO9ZyfnfwMl3tw
Tab GID: 39002702
"""

import base64
import json
import os

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials

SHEET_ID      = "1c9Xc6qsXfTwmnZ4gGMwvyCQ3bTDXBIO9ZyfnfwMl3tw"
WORKSHEET_GID = 39002702
OUTPUT_CSV    = "scripts/data/adrec_raw.csv"

EXPORT_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    f"/export?format=csv&gid={WORKSHEET_GID}"
)


def fetch():
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    creds_b64 = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
    if not creds_b64:
        raise EnvironmentError(
            "GOOGLE_CREDENTIALS_JSON env var is not set. "
            "Add it as a GitHub Actions secret (base64-encoded service account JSON)."
        )

    creds_json = json.loads(base64.b64decode(creds_b64))
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
    session = AuthorizedSession(creds)

    print(f"Downloading Google Sheet → {OUTPUT_CSV} …")
    response = session.get(EXPORT_URL, timeout=120)
    response.raise_for_status()

    with open(OUTPUT_CSV, "wb") as f:
        f.write(response.content)

    size = os.path.getsize(OUTPUT_CSV)
    print(f"  Saved {size:,} bytes")

    if size < 2_000:
        raise RuntimeError(
            f"Downloaded file is only {size} bytes — "
            "check Sheet ID / GID and that the service account has Viewer access."
        )

    line_count = response.text.count("\n")
    print(f"  ~{line_count:,} rows (including header)")
    print("Done.")


if __name__ == "__main__":
    fetch()
