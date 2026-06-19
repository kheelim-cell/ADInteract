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
from datetime import date, datetime, timedelta
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

# Synthetic header injected when ADREC's "Recent Sales" export ships without
# a header row. Order verified against a live download on 2026-06-19:
#   residential,apartment,2026-06-18,349.12,2346.09,3 beds,Al Reem Island,
#   RS5,SAAS Heights,5458311.58,1.0000,15634.49,off-plan,primary
# i.e. asset_class, property_type, registration(ISO date), sold_area_sqm,
# plot_area_sqm, layout, district, community, project, price_aed, share,
# rate_aed_sqm, sale_type, sale_sequence — 14 columns.
SYNTHETIC_HEADER = [
    "Asset Class", "Property Type", "Registration",
    "Sold Area (sqm)", "Plot Area (sqm)", "Layout",
    "District", "Community", "Project", "Price (AED)",
    "Share", "Rate (AED/sqm)", "Sale Type", "Sale Sequence",
]

# Asset-class tokens that betray a header-less CSV (row 1 is data)
ASSET_CLASS_VALUES = {
    "residential", "commercial", "industrial", "land",
    "office", "retail", "mixed-use", "mixed use", "hospitality",
}


def looks_headerless(first_row: list[str]) -> bool:
    """Return True if row 1 is clearly data, not a header.

    Heuristic: first cell is a known asset-class token AND somewhere in the
    row there's a YYYY-MM-DD or DD/MM/YYYY date — ADREC's headerless export
    pattern.
    """
    if not first_row:
        return False
    first = first_row[0].strip().lower()
    if first not in ASSET_CLASS_VALUES:
        return False
    for cell in first_row:
        raw = cell.strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                datetime.strptime(raw, fmt)
                return True
            except ValueError:
                continue
    return False


def inject_header_if_missing(path: str) -> bool:
    """If the CSV has no header row, prepend SYNTHETIC_HEADER.

    Returns True if a header was injected (CSV mutated), False otherwise.
    """
    with open(path, "r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.reader(f)
        first = next(reader, None)
    if not first or not looks_headerless(first):
        return False

    # Match synthetic header length to the actual column count of the file.
    # If ADREC adds/removes a column, we pad with generic "col_N" names so
    # transform.py's name-based lookup still finds what it can.
    width = len(first)
    header = list(SYNTHETIC_HEADER[:width])
    while len(header) < width:
        header.append(f"col_{len(header) + 1}")

    tmp = path + ".hdr"
    with open(path, "r", encoding="utf-8", errors="ignore", newline="") as src, \
         open(tmp,  "w", encoding="utf-8", newline="") as dst:
        writer = csv.writer(dst)
        writer.writerow(header)
        for line in src:
            dst.write(line)
    os.replace(tmp, path)
    print(f"  Injected synthetic header ({width} cols) — ADREC exported without one")
    return True

# How many days back to look if we can't determine last sheet date
DEFAULT_LOOKBACK_DAYS = 7



META_JSON_PATH = "static/data/meta.json"


def get_last_parquet_date() -> date:
    """
    Read the last transaction date from meta.json (written by transform.py).
    This is always in sync with the live parquet — no API call needed.
    Falls back to (today - DEFAULT_LOOKBACK_DAYS) if the file doesn't exist.
    """
    fallback = date.today() - timedelta(days=DEFAULT_LOOKBACK_DAYS)
    try:
        import json
        with open(META_JSON_PATH) as f:
            meta = json.load(f)
        max_date_str = meta.get("dateRange", {}).get("max", "")
        if not max_date_str:
            print(f"  Warning: no dateRange.max in meta.json — using fallback {fallback}")
            return fallback
        last = date.fromisoformat(max_date_str)
        print(f"  Last date in parquet (meta.json): {last}")
        return last
    except Exception as exc:
        print(f"  Warning: could not read {META_JSON_PATH} ({exc}) — using fallback {fallback}")
        return fallback


# ── CSV validation ───────────────────────────────────────────────────────────
# Three possible states returned by validate_csv:
#   "valid"       — a real transactions export WITH rows newer than expect_after
#   "no_new_data" — a structurally-valid transactions export, but nothing newer
#                   than expect_after (ADREC just hasn't published yet — NOT an error)
#   "invalid"     — not a usable transactions export (wrong columns, no dates, etc.)
def validate_csv(path: str, expect_after: date) -> tuple[str, str]:
    """
    Returns (status, reason) where status is one of:
      "valid" | "no_new_data" | "invalid".

    A "no_new_data" result means the scrape itself worked (correct columns and
    parseable dates) but ADREC has no rows after expect_after yet. Callers
    should treat that as "already up to date", not a failure.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            header = [h.strip().lower() for h in (next(reader, None) or [])]
            if not header:
                return "invalid", "Empty file"

            matches = {col for col in TRANSACTION_COLUMNS
                       if any(col in h for h in header)}
            if not matches:
                return "invalid", f"No transaction columns found. Got: {header[:8]}"

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
                return "invalid", "No date column found"

            # Scan rows: count parseable dates and look for any newer than expect_after.
            found_recent = False
            parseable_dates = 0
            for row in reader:
                if date_col_idx >= len(row):
                    continue
                raw = row[date_col_idx].strip()
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
                    try:
                        d = datetime.strptime(raw, fmt).date()
                        parseable_dates += 1
                        if d > expect_after:
                            found_recent = True
                        break
                    except ValueError:
                        continue
                if found_recent:
                    break

            if found_recent:
                return "valid", "OK"

            # No newer rows. If we couldn't parse ANY dates, the export is junk;
            # if we parsed dates fine but none are newer, ADREC is simply behind.
            if parseable_dates == 0:
                return "invalid", "No parseable dates in date column"
            return "no_new_data", (
                f"Structurally valid export but no rows after {expect_after} "
                f"({parseable_dates:,} dated rows scanned). ADREC has not "
                "published newer data yet."
            )

    except Exception as exc:
        return "invalid", f"Could not read CSV: {exc}"


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

    IMPORTANT: This is best-effort. The Recent Sales table is sorted
    newest-first by default with no filter applied, so a failed/skipped
    date-range set does NOT block getting recent rows via Export — it only
    means the export window might be wider than [start, end]. Every step
    below uses short explicit timeouts so a single unclickable/invisible
    element fails in seconds, not the default 30s, which previously caused
    multi-minute stalls (3 date formats × 2 fields × 30s ≈ 3 minutes of
    dead time on a single bad selector match).
    """
    start_str_us    = start.strftime("%m/%d/%Y")   # MM/DD/YYYY (adrec.gov.ae)
    end_str_us      = end.strftime("%m/%d/%Y")
    start_str_slash = start.strftime("%d/%m/%Y")   # DD/MM/YYYY (legacy dari.ae)
    end_str_slash   = end.strftime("%d/%m/%Y")
    start_str_iso   = start.strftime("%Y-%m-%d")
    end_str_iso     = end.strftime("%Y-%m-%d")

    print(f"  Setting date range: {start_str_us} → {end_str_us} (MM/DD/YYYY, best-effort)")

    FIELD_TIMEOUT = 4_000  # per click/fill call — fail fast on non-interactive matches

    # Strategy 1: Standard date inputs — only consider ones that are actually visible
    date_inputs_all = page.locator(
        "input[type='date'], "
        "input[placeholder*='date' i], "
        "input[placeholder*='from' i], "
        "input[placeholder*='to' i], "
        "[class*='datepicker'] input, "
        "[class*='date-picker'] input, "
        "[class*='daterange'] input"
    )
    raw_count = await date_inputs_all.count()
    visible_indices = []
    for i in range(raw_count):
        try:
            if await date_inputs_all.nth(i).is_visible():
                visible_indices.append(i)
        except Exception:
            pass
    print(f"  Found {raw_count} date input(s) in DOM, {len(visible_indices)} visible")

    if len(visible_indices) >= 2:
        try:
            start_el = date_inputs_all.nth(visible_indices[0])
            end_el   = date_inputs_all.nth(visible_indices[1])

            # Try MM/DD/YYYY (current adrec.gov.ae), then ISO, then DD/MM/YYYY (legacy).
            # Stop at the first format that succeeds — no need to try all three.
            set_ok = False
            for val in [start_str_us, start_str_iso, start_str_slash]:
                try:
                    await start_el.click(timeout=FIELD_TIMEOUT)
                    await start_el.fill(val, timeout=FIELD_TIMEOUT)
                    await page.keyboard.press("Tab")
                    await page.wait_for_timeout(400)
                    set_ok = True
                    break
                except Exception:
                    continue

            if set_ok:
                for val in [end_str_us, end_str_iso, end_str_slash]:
                    try:
                        await end_el.click(timeout=FIELD_TIMEOUT)
                        await end_el.fill(val, timeout=FIELD_TIMEOUT)
                        await page.keyboard.press("Tab")
                        await page.wait_for_timeout(400)
                        break
                    except Exception:
                        continue

                await page.wait_for_timeout(1_500)
                print(f"  ✓ Date range set via input fields")
                return True
            else:
                print("  Date input fields found but not fillable in any format — skipping")
        except Exception as exc:
            print(f"  Date input strategy failed: {exc}")
    else:
        print("  No visible date inputs — skipping date-range filter "
              "(Recent Sales is sorted newest-first by default, so this is non-fatal)")

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

    return len(visible_indices) >= 1


async def click_show_results(page) -> bool:
    """
    Click ALL 'Show Results' buttons and wait for 'Downloading…' spinners to
    clear. ADREC sections are lazy-loaded; exports won't fire until the section
    data is fully rendered.
    """
    show_results = page.locator("button:has-text('Show Results'), a:has-text('Show Results')")
    count = await show_results.count()
    if count == 0:
        return False
    print(f"  Found {count} 'Show Results' button(s) — clicking all…")
    clicked = 0
    for idx in range(count):
        try:
            btn = show_results.nth(idx)
            if await btn.is_visible(timeout=2_000):
                await btn.scroll_into_view_if_needed()
                await btn.click()
                await page.wait_for_timeout(1_500)
                clicked += 1
        except Exception as exc:
            print(f"  'Show Results' #{idx + 1} click failed: {exc}")

    if clicked:
        print(f"  ✓ Clicked {clicked} 'Show Results' button(s) — waiting for data load…")
        # Wait up to 90s for all "Downloading…" spinners to clear. Slow ADREC
        # responses are the #1 cause of subsequent Export-button timeouts.
        try:
            await page.wait_for_function(
                "() => !document.body.innerText.includes('Downloading...')",
                timeout=90_000,
            )
            print("  ✓ Data sections loaded")
        except Exception:
            print("  ⚠ 'Downloading…' still visible after 90s — proceeding anyway")
        await page.wait_for_timeout(3_000)

    return clicked > 0


async def find_recent_sales_export_indices(page, all_exports) -> list[int]:
    """
    Locate the Export button(s) belonging to the "Recent Sales" widget by
    vertical proximity, rather than a hardcoded index — ADREC has reordered
    widgets on this page before, which silently broke a fixed-index guess.

    Returns indices into `all_exports`, sorted nearest-first to the "Recent
    Sales" heading. Empty list if the heading isn't found.
    """
    try:
        heading = page.locator("text='Recent Sales'").first
        hbox = await heading.bounding_box()
        if not hbox:
            return []
    except Exception:
        return []

    count = await all_exports.count()
    scored = []
    for i in range(count):
        btn = all_exports.nth(i)
        try:
            if not await btn.is_visible():
                continue
            box = await btn.bounding_box()
            if not box:
                continue
            scored.append((abs(box["y"] - hbox["y"]), i))
        except Exception:
            continue
    scored.sort()
    return [i for _, i in scored]


async def try_export_buttons(page, output_path: str, expect_after: date) -> str:
    """
    Try Export buttons, prioritising the one closest to the "Recent Sales"
    heading (the widget we actually want), then fall back to any other
    visible Export/Download button.

    Returns one of:
      "downloaded"  — a valid export with new rows was saved to output_path
      "no_new_data" — at least one structurally-valid export was found, but
                      none had rows after expect_after (ADREC is behind)
      "failed"      — no usable transactions export could be obtained at all
    """
    tmp = output_path + ".tmp"

    # Best-effort: some ADREC layouts still require a "Show Results" click
    # before a widget's export fires. Harmless no-op if none are visible
    # (current layout's Recent Sales table is rendered by default).
    await click_show_results(page)

    # Also try buttons labelled "Downloading…" — ADREC sometimes uses this
    # label for the same trigger when data is in a loading state
    all_exports = page.locator(
        "a:has-text('Export'), button:has-text('Export'), "
        "a:has-text('Downloading'), button:has-text('Downloading')"
    )
    count = await all_exports.count()
    print(f"  Found {count} Export/Download button(s)")

    if count == 0:
        return "failed"

    # Primary strategy: the single button nearest the "Recent Sales" heading.
    # We trust this targeting once it returns ANY definitive answer (a
    # download, even an empty one, or a structurally-valid-but-stale export)
    # — those answers came from the right widget, so there's no reason to
    # also probe the other widgets' Export buttons. Those tend to hang for
    # the full download timeout waiting for a download that's never coming,
    # since they're a different widget's trigger.
    by_proximity = await find_recent_sales_export_indices(page, all_exports)
    if by_proximity:
        primary_indices = by_proximity[:1]
        fallback_indices = [i for i in range(min(count, 4)) if i not in primary_indices]
        print(f"  Targeting Export button nearest 'Recent Sales' heading: index {primary_indices[0]}")
    else:
        # No heading match at all (page structure changed again) — just try
        # the first few visible Export buttons with no special priority.
        print("  'Recent Sales' heading not found — falling back to first visible Export buttons")
        primary_indices = []
        fallback_indices = list(range(min(count, 4)))

    saw_valid_export = False  # found correct columns/dates, just nothing new

    async def attempt(i: int) -> str | None:
        """Try Export button at index i. Returns 'downloaded', 'no_new_data',
        'empty', or None (couldn't get any usable response — try elsewhere)."""
        nonlocal saw_valid_export
        btn = all_exports.nth(i)
        try:
            if not await btn.is_visible(timeout=1_000):
                return None
        except Exception:
            return None

        btn_text = (await btn.inner_text()).strip()[:20]
        print(f"  Trying Export #{i + 1} (index {i}, text={btn_text!r})…")
        try:
            await btn.scroll_into_view_if_needed()
            await page.wait_for_timeout(600)
            async with page.expect_download(timeout=120_000) as dl_info:
                await btn.click()
            dl = await dl_info.value
            await dl.save_as(tmp)
            size = os.path.getsize(tmp)
            print(f"    Downloaded {size:,} bytes")

            # A 0-byte export from the correctly-targeted button means ADREC
            # simply hasn't published any rows for the requested window yet
            # (common when the window is "today" and it's early in the day).
            # This is a clean no-op, NOT a failure.
            if size == 0:
                os.remove(tmp)
                saw_valid_export = True
                print(f"  ✗ Export #{i + 1} empty (0 bytes) — ADREC has no rows "
                      f"in the requested window yet")
                return "empty"

            # ADREC's "Recent Sales" export no longer ships a header row —
            # inject one before validation so the downstream pipeline works.
            inject_header_if_missing(tmp)

            status, reason = validate_csv(tmp, expect_after)
            if status == "valid":
                os.replace(tmp, output_path)
                print(f"  ✓ Export #{i + 1} accepted")
                return "downloaded"
            else:
                if status == "no_new_data":
                    saw_valid_export = True
                os.remove(tmp)
                print(f"  ✗ Export #{i + 1} rejected ({status}): {reason}")
                return status
        except Exception as exc:
            print(f"  ✗ Export #{i + 1} error: {exc}")
            if os.path.exists(tmp):
                os.remove(tmp)
            return None

    # Try the proximity-targeted button(s) first. Stop immediately on any
    # definitive answer — don't waste time on other widgets once we've heard
    # back from the right one.
    for i in primary_indices:
        if i >= count:
            continue
        result = await attempt(i)
        if result == "downloaded":
            return "downloaded"
        if result in ("empty", "no_new_data"):
            return "no_new_data"
        # result is None (couldn't reach this button) or "invalid" — fall
        # through to try other widgets below.

    for i in fallback_indices:
        if i >= count:
            continue
        result = await attempt(i)
        if result == "downloaded":
            return "downloaded"

    return "no_new_data" if saw_valid_export else "failed"


# ── Main fetch ───────────────────────────────────────────────────────────────
async def fetch():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    today = date.today()

    # Determine the date window: last_parquet_date+1 → today
    print("[1/5] Checking last date in local parquet (meta.json)…")
    last_date = get_last_parquet_date()
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
        # Use system Chrome channel locally on Windows (bundled chromium has
        # spawn issues). CI installs chromium via `playwright install --with-deps`
        # on Ubuntu, where the bundled binary works fine — toggle via env var.
        launch_kwargs = dict(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        if os.environ.get("ADREC_USE_SYSTEM_CHROME") == "1":
            launch_kwargs["channel"] = "chrome"
        browser = await p.chromium.launch(**launch_kwargs)
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
        result = await try_export_buttons(page, OUTPUT_PATH, expect_after=last_date)

        if result == "no_new_data":
            # The scrape worked, ADREC just hasn't published anything newer than
            # last_date yet (government data routinely lags 1–2 days). This is a
            # clean no-op, not a failure: write the empty sentinel and exit 0 so
            # the workflow stays green and downstream steps skip gracefully.
            await browser.close()
            print(
                f"  ADREC has no data after {last_date} yet — already up to date. "
                "Writing empty sentinel and exiting cleanly."
            )
            Path(OUTPUT_PATH).write_text("")
            return

        if result == "failed":
            await save_debug_info(page)
            await browser.close()
            print(
                "ERROR: Could not obtain any usable transactions export.\n"
                "This is a real scrape failure (not just missing recent data).\n"
                "Possible causes:\n"
                "  - The date filter did not apply — check debug_screenshot.png\n"
                "  - The Export button layout changed on dari.ae\n"
                "  - The dashboard structure changed",
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
