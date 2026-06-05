"""
backfill_adrec.py
-----------------
One-time historical backfill.

ADREC's export is capped at ~36K rows per request.  A single "01/01/2019 →
today" pull only returns the most-recent 36K transactions, leaving ~61K
historical records missing from the Google Sheet.

This script iterates year-by-year (2019 … current year), downloads each
period's CSV from the ADREC dashboard, deduplicates across all batches,
then appends every row that is not already in the Google Sheet.

Run once manually:
    python scripts/backfill_adrec.py

Or trigger from GitHub Actions → workflow_dispatch (backfill-data.yml).

Env required:
    GOOGLE_CREDENTIALS_JSON  — base64-encoded service-account JSON
"""

import asyncio
import csv
import io
import os
import sys
from datetime import datetime, timezone

import pandas as pd

# ── Reuse existing helpers ──────────────────────────────────────────────────
# Import the Playwright fetch logic from fetch_adrec.py, parameterised with
# start/end dates.  We monkey-patch the module-level constants before calling.
sys.path.insert(0, os.path.dirname(__file__))

from playwright.async_api import async_playwright


# Copy of the relevant helpers from fetch_adrec.py (avoid circular imports)
ADREC_URL   = "https://www.dari.ae/adrec/MarketDetails.html"
DEBUG_DIR   = "scripts/data"

TRANSACTION_COLUMNS = {
    "district", "community", "project", "property type",
    "sale price", "sale application", "registration",
    "transaction date", "property sale", "sold area", "asset type",
}


def validate_csv(path: str) -> tuple[bool, set, str]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            header = [h.strip().lower() for h in next(csv.reader(f), [])]
    except Exception as exc:
        return False, set(), f"Could not read CSV: {exc}"
    found = set(header)
    matches = {col for col in TRANSACTION_COLUMNS if any(col in h for h in found)}
    if not matches:
        return False, found, f"Wrong columns: {found}"
    return True, found, "OK"


async def dismiss_overlays(page):
    selectors = [
        "button:has-text('Accept All')", "button:has-text('Accept')",
        "button:has-text('I Accept')", "button:has-text('Agree')",
        "button:has-text('OK')", "button:has-text('×')",
        "button:has-text('✕')", "button[aria-label='Close']",
        "button[aria-label='close']", "[class*='modal'] button[class*='close']",
        "[class*='popup'] button[class*='close']", "[class*='cookie'] button",
        "[id*='cookie'] button", "[id*='accept']", "[class*='accept']",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1_500):
                await btn.click()
                await page.wait_for_timeout(800)
        except Exception:
            pass


async def wait_for_dashboard(page, timeout_ms=40_000):
    indicators = [
        "text=Recent Sales", "text=Export",
        "[class*='export' i]", "table",
        "[class*='table' i]", "[class*='grid' i]",
    ]
    for sel in indicators:
        try:
            await page.wait_for_selector(sel, timeout=timeout_ms)
            return True
        except Exception:
            continue
    return False


async def fetch_year_range(start_str: str, end_str: str, out_path: str) -> bool:
    """
    Open ADREC, set the date range to [start_str, end_str], click Export,
    save to out_path.  Returns True on success.
    """
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

        print(f"  [{start_str} → {end_str}] Navigating…")
        await page.goto(ADREC_URL, wait_until="networkidle", timeout=120_000)
        await page.wait_for_timeout(5_000)

        await dismiss_overlays(page)
        await page.wait_for_timeout(2_000)

        loaded = await wait_for_dashboard(page, timeout_ms=30_000)
        if not loaded:
            await dismiss_overlays(page)
            await page.wait_for_timeout(3_000)
            loaded = await wait_for_dashboard(page, timeout_ms=20_000)

        if not loaded:
            print(f"  [{start_str} → {end_str}] Dashboard did not load — skipping.")
            await browser.close()
            return False

        # Set date range
        for label, value in [("start", start_str), ("end", end_str)]:
            try:
                inputs = page.locator(
                    "input[type='date'], input[placeholder*='date' i], "
                    "input[placeholder*='from' i], input[placeholder*='to' i], "
                    "[class*='datepicker'] input, [class*='date-picker'] input"
                )
                if await inputs.count() >= 2:
                    idx = 0 if label == "start" else 1
                    el = inputs.nth(idx)
                    await el.fill(value)
                    await page.keyboard.press("Tab")
                    await page.wait_for_timeout(800)
            except Exception as exc:
                print(f"  Could not set {label} date: {exc}")

        await page.wait_for_timeout(3_000)

        # Scroll to trigger lazy load
        for y in [600, 1200, 2000, 3000]:
            await page.evaluate(f"window.scrollTo(0, {y})")
            await page.wait_for_timeout(600)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1_000)

        # Find export buttons
        all_exports = page.locator("a:has-text('Export'), button:has-text('Export')")
        count = await all_exports.count()
        print(f"  [{start_str} → {end_str}] Export buttons: {count}")

        if count == 0:
            await browser.close()
            return False

        success = False
        primary_index = 4

        for i in ([primary_index] + [j for j in range(count) if j != primary_index]):
            if i >= count:
                continue
            btn = all_exports.nth(i)
            try:
                if not await btn.is_visible(timeout=1_000):
                    continue
                await btn.scroll_into_view_if_needed()
                await page.wait_for_timeout(400)
                tmp = out_path + ".tmp"
                async with page.expect_download(timeout=90_000) as dl_info:
                    await btn.click()
                dl = await dl_info.value
                await dl.save_as(tmp)
                size = os.path.getsize(tmp)
                valid, cols, msg = validate_csv(tmp)
                if valid:
                    os.replace(tmp, out_path)
                    print(f"  [{start_str} → {end_str}] Export #{i+1} OK  ({size:,} bytes)")
                    success = True
                    break
                else:
                    os.remove(tmp)
                    print(f"  [{start_str} → {end_str}] Export #{i+1} rejected: {msg}")
            except Exception as exc:
                print(f"  [{start_str} → {end_str}] Export #{i+1} error: {exc}")

        await browser.close()
        return success


def merge_and_append_to_sheet(all_csvs: list[str]):
    """
    Concatenate all downloaded CSVs, deduplicate, then append rows not
    already in the Google Sheet (reusing update_sheets logic).
    """
    if not all_csvs:
        print("No CSVs to merge.")
        return

    print(f"\nMerging {len(all_csvs)} CSV files…")
    frames = []
    for path in all_csvs:
        try:
            df = pd.read_csv(path, low_memory=False)
            frames.append(df)
            print(f"  {path}: {len(df):,} rows")
        except Exception as exc:
            print(f"  Skipping {path}: {exc}")

    if not frames:
        print("No valid data to merge.")
        return

    combined = pd.concat(frames, ignore_index=True)
    print(f"Combined (before dedup): {len(combined):,} rows")

    # Deduplicate on key columns that identify a unique transaction
    key_cols = [c for c in [
        "Sale Application Date", "Registration Date", "Transaction Date",
        "District", "Community", "Project Name",
        "Property Sale Price (AED)", "Property Sold Area (SQM)",
    ] if c in combined.columns]

    if key_cols:
        before = len(combined)
        combined = combined.drop_duplicates(subset=key_cols)
        print(f"Deduped: {before - len(combined):,} duplicates removed → {len(combined):,} rows")

    # Save merged file for update_sheets to consume
    merged_path = "scripts/data/adrec_backfill_merged.csv"
    combined.to_csv(merged_path, index=False)
    print(f"Saved merged CSV → {merged_path}  ({len(combined):,} rows)")

    # Now run update_sheets using the merged CSV instead of the default path
    os.environ["BACKFILL_CSV_OVERRIDE"] = merged_path
    try:
        from update_sheets import update
        update()
    except Exception as exc:
        print(f"\nSheet append failed: {exc}")
        print("Merged CSV is at:", merged_path)
        print("You can manually import it into the Google Sheet as a fallback.")
    finally:
        os.environ.pop("BACKFILL_CSV_OVERRIDE", None)


async def main():
    os.makedirs("scripts/data/backfill_batches", exist_ok=True)

    today = datetime.now(timezone.utc)
    current_year = today.year
    start_year = 2019

    # Build year ranges
    ranges = []
    for year in range(start_year, current_year + 1):
        start = f"01/01/{year}"
        if year == current_year:
            end = today.strftime("%m/%d/%Y")
        else:
            end = f"12/31/{year}"
        ranges.append((start, end, year))

    print(f"Backfill plan: {len(ranges)} batches ({start_year}–{current_year})\n")

    downloaded = []
    for start, end, year in ranges:
        out = f"scripts/data/backfill_batches/adrec_{year}.csv"

        # Skip if already downloaded in a previous run
        if os.path.exists(out) and os.path.getsize(out) > 10_000:
            print(f"  [{start} → {end}] Already have {out} — skipping download.")
            downloaded.append(out)
            continue

        ok = await fetch_year_range(start, end, out)
        if ok:
            downloaded.append(out)
        else:
            print(f"  [{start} → {end}] FAILED — will retry on next run.")

        # Brief pause between requests to avoid rate-limiting
        await asyncio.sleep(5)

    print(f"\nDownloaded {len(downloaded)}/{len(ranges)} year batches.")
    merge_and_append_to_sheet(downloaded)


if __name__ == "__main__":
    asyncio.run(main())
