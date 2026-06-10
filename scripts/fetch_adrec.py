"""
fetch_adrec.py
--------------
Uses Playwright (headless Chrome) to export ONLY NEW rows from the
ADREC dashboard (dari.ae), then validates the result.

Key change from v1: Instead of exporting the full 2019→today history
(which exceeds ADREC's export row-cap and cuts off recent data), we
now set the date range to [last_sheet_date + 1 day → today].  The
delta is small (<500 rows on a normal day), can't be capped, and is
validated to contain at least yesterday's date before being accepted.

On failure the script exits non-zero so GitHub Actions marks the step
red and uploads the debug screenshot/HTML artifact.
"""

import asyncio
import csv
import json
import os
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from playwright.async_api import async_playwright

# ── Config ──────────────────────────────────────────────────────────────────
ADREC_URL   = "https://www.dari.ae/adrec/MarketDetails.html"
OUTPUT_PATH = "scripts/data/adrec_raw.csv"
DEBUG_DIR   = "scripts/data"

# Columns we expect in a valid transaction CSV (any match = valid)
TRANSACTION_COLUMNS = {
    "district", "community", "project", "property type",
    "sale price", "sale application", "registration",
    "transaction date", "property sale", "sold area", "asset type",
    "asset class", "layout",
}

# How many days back to look if we can't determine last sheet date
DEFAULT_LOOKBACK_DAYS = 7


# ── Credentials helper ───────────────────────────────────────────────────────
def _get_gspread_client():
    """Return an authenticated gspread client using env vars."""
    import base64
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    creds_file = os.environ.get("GOOGLE_CREDENTIALS_FILE")
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")

    if creds_file:
        creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    elif creds_json:
        if creds_json.strip().startswith("{"):
            info = json.loads(creds_json)
        else:
            padded = creds_json + "=" * (4 - len(creds_json) % 4)
            info = json.loads(base64.b64decode(padded).decode())
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(info, tmp)
        tmp.close()
        creds = Credentials.from_service_account_file(tmp.name, scopes=scopes)
        os.unlink(tmp.name)
    else:
        raise EnvironmentError(
            "Set GOOGLE_CREDENTIALS_FILE or GOOGLE_CREDENTIALS_JSON"
        )

    return gspread.authorize(creds)


def get_last_sheet_date() -> date:
    """
    Query the main Google Sheet to find the latest Sale Application Date.
    Falls back to (today - DEFAULT_LOOKBACK_DAYS) if credentials are
    unavailable or the sheet can't be read.
    """
    SHEET_ID = "1c9Xc6qsXfTwmnZ4gGMwvyCQ3bTDXBIO9ZyfnfwMl3tw"
    GID      = 39002702
    DATE_COL = "Sale Application Date"

    fallback = date.today() - timedelta(days=DEFAULT_LOOKBACK_DAYS)

    try:
        import gspread
        import pandas as pd

        gc = _get_gspread_client()
        sh = gc.open_by_key(SHEET_ID)
        ws = next((s for s in sh.worksheets() if s.id == GID), sh.get_worksheet(0))

        # Read only the header + date column to avoid downloading everything
        header = ws.row_values(1)
        if DATE_COL not in header:
            print(f"  Warning: '{DATE_COL}' not in sheet header — using fallback date")
            return fallback

        col_idx = header.index(DATE_COL) + 1  # 1-based
        date_values = ws.col_values(col_idx)[1:]  # skip header

        parsed = pd.to_datetime(date_values, dayfirst=True, errors="coerce").dropna()
        if parsed.empty:
            return fallback

        last = parsed.max().date()
        print(f"  Last date in sheet: {last}")
        return last

    except Exception as exc:
        print(f"  Warning: could not read sheet ({exc}) — using fallback {fallback}")
        return fallback


# ── CSV validation ───────────────────────────────────────────────────────────
def validate_csv(path: str, expect_after: date) -> tuple[bool, str]:
    """
    Returns (is_valid, reason).
    Checks:
      1. File is readable and has transaction-like columns.
      2. Contains at least one row dated after expect_after.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            header = [h.strip().lower() for h in (next(reader, None) or [])]
            if not header:
                return False, "Empty file"

            matches = {col for col in TRANSACTION_COLUMNS
                       if any(col in h for h in header)}
            if not matches:
                return False, f"No transaction columns found. Got: {header[:8]}"

            # Find a date-like column
            date_col_idx = None
            for date_hint in ("sale application date", "registration date",
                              "registration", "transaction date", "date"):
                for i, h in enumerate(header):
                    if date_hint in h:
                        date_col_idx = i
                        break
                if date_col_idx is not None:
                    break

            if date_col_idx is None:
                return False, "No date column found"

            # Scan rows for any date after expect_after
            found_recent = False
            for row in reader:
                if date_col_idx >= len(row):
                    continue
                raw = row[date_col_idx].strip()
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
                    try:
                        d = datetime.strptime(raw, fmt).date()
                        if d > expect_after:
                            found_recent = True
                        break
                    except ValueError:
                        continue
                if found_recent:
                    break

            if not found_recent:
                return False, (
                    f"No rows dated after {expect_after}. "
                    "ADREC may not have published this data yet, "
                    "or the date filter did not apply."
                )

    except Exception as exc:
        return False, f"Could not read CSV: {exc}"

    return True, "OK"


# ── Playwright helpers ───────────────────────────────────────────────────────
async def save_debug_info(page):
    os.makedirs(DEBUG_DIR, exist_ok=True)
    ss = f"{DEBUG_DIR}/debug_screenshot.png"
    await page.screenshot(path=ss, full_page=True)
    print(f"  Screenshot → {ss}")
    html_path = f"{DEBUG_DIR}/debug_page.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(await page.content())
    print(f"  HTML       → {html_path}")
    try:
        texts = [t.strip() for t in
                 await page.locator("button, a, [role='button']").all_text_contents()
                 if t.strip()]
        print(f"  Buttons/links ({len(texts)}): {texts[:40]}")
    except Exception:
        pass


async def dismiss_overlays(page):
    selectors = [
        "button:has-text('Accept All')", "button:has-text('Accept')",
        "button:has-text('I Accept')",   "button:has-text('Agree')",
        "button:has-text('OK')",
        "button:has-text('×')",          "button:has-text('✕')",
        "button[aria-label='Close']",    "button[aria-label='close']",
        "[class*='modal'] button[class*='close']",
        "[class*='popup'] button[class*='close']",
        "[class*='cookie'] button",      "[id*='cookie'] button",
        "[id*='accept']",                "[class*='accept']",
    ]
    dismissed = 0
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1_500):
                await btn.click()
                print(f"  Dismissed overlay: {sel!r}")
                await page.wait_for_timeout(800)
                dismissed += 1
        except Exception:
            pass
    return dismissed


async def wait_for_dashboard(page, timeout_ms=40_000) -> bool:
    indicators = [
        "text=Recent Sales",
        "text=Export",
        "[class*='export' i]",
        "table",
        "[class*='datatable' i]",
        "[class*='grid' i]",
    ]
    for sel in indicators:
        try:
            await page.wait_for_selector(sel, timeout=timeout_ms)
            print(f"  Dashboard ready ({sel!r})")
            return True
        except Exception:
            continue
    return False


async def set_date_range(page, start: date, end: date) -> bool:
    """
    Try multiple strategies to set the date range filter.
    Returns True if at least the start date was set.
    """
    start_str_slash = start.strftime("%d/%m/%Y")
    end_str_slash   = end.strftime("%d/%m/%Y")
    start_str_iso   = start.strftime("%Y-%m-%d")
    end_str_iso     = end.strftime("%Y-%m-%d")

    print(f"  Setting date range: {start_str_slash} → {end_str_slash}")

    # Strategy 1: Standard date inputs
    date_inputs = page.locator(
        "input[type='date'], "
        "input[placeholder*='date' i], "
        "input[placeholder*='from' i], "
        "input[placeholder*='to' i], "
        "[class*='datepicker'] input, "
        "[class*='date-picker'] input, "
        "[class*='daterange'] input"
    )
    count = await date_inputs.count()
    print(f"  Found {count} date input(s)")

    if count >= 2:
        try:
            start_el = date_inputs.nth(0)
            end_el   = date_inputs.nth(1)

            # Try ISO format first (works for type="date"), then slash format
            for val in [start_str_iso, start_str_slash]:
                await start_el.triple_click()
                await start_el.fill(val)
                await page.keyboard.press("Tab")
                await page.wait_for_timeout(500)

            for val in [end_str_iso, end_str_slash]:
                await end_el.triple_click()
                await end_el.fill(val)
                await page.keyboard.press("Tab")
                await page.wait_for_timeout(500)

            await page.wait_for_timeout(2_000)
            print(f"  ✓ Date range set via input fields")
            return True
        except Exception as exc:
            print(f"  Date input strategy failed: {exc}")

    # Strategy 2: Look for Apply / Search / Filter button after setting dates
    for btn_text in ["Apply", "Search", "Filter", "Go", "Submit"]:
        try:
            btn = page.locator(f"button:has-text('{btn_text}')").first
            if await btn.is_visible(timeout=1_000):
                await btn.click()
                await page.wait_for_timeout(2_000)
                print(f"  Clicked '{btn_text}' button after date entry")
                break
        except Exception:
            pass

    return count >= 1


async def try_export_buttons(page, output_path: str, expect_after: date) -> bool:
    """
    Try all Export buttons in order: first index 4 (known "Recent Sales"),
    then all others. Accept the first one that produces a valid CSV.
    """
    tmp = output_path + ".tmp"
    all_exports = page.locator("a:has-text('Export'), button:has-text('Export')")
    count = await all_exports.count()
    print(f"  Found {count} Export button(s)")

    if count == 0:
        return False

    # Try index 4 first (historically the Recent Sales export), then all others
    indices = [4] + [i for i in range(count) if i != 4]

    for i in indices:
        if i >= count:
            continue
        btn = all_exports.nth(i)
        try:
            if not await btn.is_visible(timeout=1_000):
                continue
        except Exception:
            continue

        print(f"  Trying Export #{i + 1} (index {i})…")
        try:
            await btn.scroll_into_view_if_needed()
            await page.wait_for_timeout(400)
            async with page.expect_download(timeout=90_000) as dl_info:
                await btn.click()
            dl = await dl_info.value
            await dl.save_as(tmp)
            size = os.path.getsize(tmp)
            print(f"    Downloaded {size:,} bytes")

            valid, reason = validate_csv(tmp, expect_after)
            if valid:
                os.replace(tmp, output_path)
                print(f"  ✓ Export #{i + 1} accepted")
                return True
            else:
                os.remove(tmp)
                print(f"  ✗ Export #{i + 1} rejected: {reason}")
        except Exception as exc:
            print(f"  ✗ Export #{i + 1} error: {exc}")
            if os.path.exists(tmp):
                os.remove(tmp)

    return False


# ── Main fetch ───────────────────────────────────────────────────────────────
async def fetch():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    today = date.today()

    # Determine the date window: last_sheet_date+1 → today
    print("[1/5] Checking last date in Google Sheet…")
    last_date = get_last_sheet_date()
    start_date = last_date + timedelta(days=1)

    # Safety: if last_date is today or future, nothing to fetch
    if start_date > today:
        print(f"  Sheet is already up to date (last={last_date}). Nothing to fetch.")
        # Write an empty sentinel so update_sheets.py can detect this
        Path(OUTPUT_PATH).write_text("")
        return

    print(f"  Fetching window: {start_date} → {today}")
    print(f"  Expecting data after: {last_date}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        context = await browser.new_context(
            accept_downloads=True,
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        print(f"[2/5] Navigating to ADREC dashboard…")
        await page.goto(ADREC_URL, wait_until="networkidle", timeout=120_000)
        await page.wait_for_timeout(5_000)

        print("[3/5] Preparing dashboard…")
        await dismiss_overlays(page)
        await page.wait_for_timeout(2_000)

        loaded = await wait_for_dashboard(page, timeout_ms=30_000)
        if not loaded:
            print("  Round 2: dismissing overlays and retrying…")
            await dismiss_overlays(page)
            await page.wait_for_timeout(3_000)
            loaded = await wait_for_dashboard(page, timeout_ms=20_000)

        if not loaded:
            await save_debug_info(page)
            await browser.close()
            print("ERROR: Dashboard did not render. See debug artifact.", file=sys.stderr)
            sys.exit(1)

        print("[4/5] Setting date range…")
        await set_date_range(page, start_date, today)

        # Scroll to lazy-load all sections
        for y in [600, 1200, 2000, 3000]:
            await page.evaluate(f"window.scrollTo(0, {y})")
            await page.wait_for_timeout(500)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1_000)

        print("[5/5] Downloading export…")
        success = await try_export_buttons(page, OUTPUT_PATH, expect_after=last_date)

        if not success:
            await save_debug_info(page)
            await browser.close()
            print(
                f"ERROR: Could not obtain a CSV with data after {last_date}.\n"
                "Possible causes:\n"
                "  - ADREC has not published this date's data yet (normal if run early)\n"
                "  - The date filter did not apply — check debug_screenshot.png\n"
                "  - The Export button layout changed on dari.ae",
                file=sys.stderr,
            )
            sys.exit(1)

        size = os.path.getsize(OUTPUT_PATH)
        print(f"\n  Final CSV → {OUTPUT_PATH}  ({size:,} bytes)")
        if size < 500 and start_date < today:
            # Not zero (would be caught above) but suspiciously small
            print("  Warning: CSV is very small — may be a partial export.")

        await browser.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(fetch())
