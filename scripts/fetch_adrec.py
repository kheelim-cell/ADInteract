"""
fetch_adrec.py
--------------
Uses Playwright (headless Chrome) to open the ADREC dashboard,
set the date range (01/01/2019 → today), and click the Export button
that lives in the "Recent Sales" section header (top-right corner).

Debug artifacts (screenshot + HTML) are saved to scripts/data/ whenever
the script fails, so they can be inspected via the GitHub Actions artifact.
"""

import asyncio
import csv
import os
from datetime import datetime
from playwright.async_api import async_playwright

ADREC_URL   = "https://adrec.gov.ae/en/property_and_index/adrec-dashboard"
OUTPUT_PATH = "scripts/data/adrec_raw.csv"
DEBUG_DIR   = "scripts/data"

# Header columns that confirm we have transaction-level data, not a summary
TRANSACTION_COLUMNS = {
    "district", "community", "project", "property type",
    "sale price", "sale application", "registration",
    "transaction date", "property sale", "sold area", "asset type",
}


# ── Utilities ──────────────────────────────────────────────────────────────────

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


async def accept_cookies(page):
    for sel in [
        "button:has-text('Accept All')", "button:has-text('Accept')",
        "button:has-text('I Accept')", "button:has-text('Agree')",
        "button:has-text('OK')", "[id*='accept' i]", "[class*='cookie' i] button",
    ]:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=2_000):
                await btn.click()
                print(f"  Accepted cookies via: {sel!r}")
                await page.wait_for_timeout(1_500)
                return
        except Exception:
            pass


async def save_debug_info(page):
    os.makedirs(DEBUG_DIR, exist_ok=True)
    ss = f"{DEBUG_DIR}/debug_screenshot.png"
    await page.screenshot(path=ss, full_page=True)
    print(f"  Screenshot → {ss}")
    html = f"{DEBUG_DIR}/debug_page.html"
    with open(html, "w", encoding="utf-8") as f:
        f.write(await page.content())
    print(f"  HTML       → {html}")
    try:
        texts = [t.strip() for t in await page.locator("button, a, [role='button']").all_text_contents() if t.strip()]
        print(f"  All buttons/links ({len(texts)}): {texts[:60]}")
    except Exception:
        pass


# ── Core fetch ─────────────────────────────────────────────────────────────────

async def fetch():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

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

        print(f"[{datetime.utcnow().isoformat()}Z] Navigating to ADREC dashboard…")
        await page.goto(ADREC_URL, wait_until="networkidle", timeout=120_000)
        await page.wait_for_timeout(6_000)

        await accept_cookies(page)
        await page.wait_for_timeout(2_000)

        # ── Set date range ──────────────────────────────────────────────────
        today_str = datetime.utcnow().strftime("%m/%d/%Y")
        start_str = "01/01/2019"

        for label, value in [("start", start_str), ("end", today_str)]:
            try:
                inputs = page.locator(
                    "input[type='date'], input[placeholder*='date' i], "
                    "input[placeholder*='from' i], input[placeholder*='to' i], "
                    "[class*='datepicker'] input, [class*='date-picker'] input"
                )
                if await inputs.count() >= 2:
                    idx = 0 if label == "start" else 1
                    el = inputs.nth(idx)
                    await el.triple_click()
                    await el.fill(value)
                    await page.keyboard.press("Tab")
                    await page.wait_for_timeout(800)
                    print(f"  Set {label} date → {value}")
            except Exception as exc:
                print(f"  Could not set {label} date: {exc}")

        await page.wait_for_timeout(3_000)

        # ── Scroll down so "Recent Sales" section fully loads ───────────────
        for y in [600, 1200, 2000, 3000]:
            await page.evaluate(f"window.scrollTo(0, {y})")
            await page.wait_for_timeout(800)

        # Wait for "Recent Sales" heading to appear
        try:
            await page.wait_for_selector(
                "text=Recent Sales", timeout=15_000
            )
            print("  'Recent Sales' section loaded")
        except Exception:
            print("  Warning: 'Recent Sales' text not found, continuing anyway")

        # Scroll back up slightly so the full section is visible
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1_000)

        # ── Find the Export button in the "Recent Sales" section header ─────
        #
        # The page layout (from debug screenshot) is:
        #   [ Recent Sales ]          [ ↗ Export ]
        #   [ date pickers + filters                ]
        #   [ table with Asset Type, Property Type… ]
        #
        # The correct Export is the 5th button (index 4, 0-based).
        # We try that first, validate the CSV, then fall back to other strategies.

        export_btn = None

        # Strategy 0: directly use the 5th Export button (index 4)
        try:
            all_exports = page.locator("a:has-text('Export'), button:has-text('Export')")
            count = await all_exports.count()
            print(f"  Total Export buttons found: {count}")
            if count >= 5:
                btn = all_exports.nth(4)
                if await btn.is_visible(timeout=3_000):
                    export_btn = btn
                    print("  Strategy 0: using Export button #5 (index 4) directly")
        except Exception as exc:
            print(f"  Strategy 0 failed: {exc}")

        # Strategy 1: container that wraps both "Recent Sales" heading + Export
        try:
            container = (
                page.locator("div, section, article, header")
                .filter(has=page.get_by_text("Recent Sales", exact=False))
                .filter(has=page.locator("a:has-text('Export'), button:has-text('Export')"))
                .last  # innermost / most-specific matching ancestor
            )
            btn = container.locator(
                "a:has-text('Export'), button:has-text('Export')"
            ).first
            if await btn.is_visible(timeout=4_000):
                export_btn = btn
                print("  Strategy 1: Export found inside 'Recent Sales' container")
        except Exception as exc:
            print(f"  Strategy 1 failed: {exc}")

        # Strategy 2: heading sibling — element immediately after the heading
        if export_btn is None:
            try:
                btn = page.locator(
                    "h1:has-text('Recent Sales') ~ a:has-text('Export'), "
                    "h2:has-text('Recent Sales') ~ a:has-text('Export'), "
                    "h3:has-text('Recent Sales') ~ a:has-text('Export'), "
                    "h1:has-text('Recent Sales') ~ button:has-text('Export'), "
                    "h2:has-text('Recent Sales') ~ button:has-text('Export'), "
                    "h3:has-text('Recent Sales') ~ button:has-text('Export')"
                ).first
                if await btn.is_visible(timeout=3_000):
                    export_btn = btn
                    print("  Strategy 2: Export found as sibling of 'Recent Sales' heading")
            except Exception as exc:
                print(f"  Strategy 2 failed: {exc}")

        # Strategy 3: scroll Export buttons into view one-by-one; pick the one
        # whose bounding box is closest (vertically) to "Recent Sales" text
        if export_btn is None:
            try:
                heading = page.get_by_text("Recent Sales", exact=False).first
                heading_box = await heading.bounding_box()
                all_exports = page.locator("a:has-text('Export'), button:has-text('Export')")
                count = await all_exports.count()
                print(f"  Strategy 3: scanning {count} Export element(s) by proximity to heading")

                best_btn = None
                best_dist = float("inf")
                for i in range(count):
                    el = all_exports.nth(i)
                    box = await el.bounding_box()
                    if box and heading_box:
                        dist = abs(box["y"] - heading_box["y"])
                        print(f"    Export #{i}: y={box['y']:.0f}, dist={dist:.0f}")
                        if dist < best_dist:
                            best_dist = dist
                            best_btn = el

                if best_btn and await best_btn.is_visible(timeout=2_000):
                    export_btn = best_btn
                    print(f"  Strategy 3: using Export closest to heading (dist={best_dist:.0f}px)")
            except Exception as exc:
                print(f"  Strategy 3 failed: {exc}")

        # Strategy 4: last resort — iterate all Export buttons, take the first
        # that produces a valid transaction CSV
        if export_btn is None:
            print("  Strategy 4: trying every Export button and validating CSV…")
            all_exports = page.locator("a:has-text('Export'), button:has-text('Export')")
            count = await all_exports.count()
            for i in range(count):
                btn = all_exports.nth(i)
                if not await btn.is_visible(timeout=1_000):
                    continue
                try:
                    tmp = OUTPUT_PATH + ".tmp"
                    async with page.expect_download(timeout=30_000) as dl_info:
                        await btn.click()
                    dl = await dl_info.value
                    await dl.save_as(tmp)
                    valid, cols, msg = validate_csv(tmp)
                    if valid:
                        os.replace(tmp, OUTPUT_PATH)
                        print(f"  Strategy 4: Export #{i} produced valid transaction CSV")
                        await browser.close()
                        print("Done.")
                        return
                    else:
                        os.remove(tmp)
                        print(f"  Export #{i} rejected: {msg}")
                except Exception as exc:
                    print(f"  Export #{i} error: {exc}")

            await save_debug_info(page)
            await browser.close()
            raise RuntimeError(
                "No Export button produced transaction-level data. "
                "Check the adrec-debug artifact (debug_screenshot.png)."
            )

        # ── Download (strategies 1-3 path) ─────────────────────────────────
        await export_btn.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)
        print("  Clicking Export, waiting for download…")

        async with page.expect_download(timeout=90_000) as dl_info:
            await export_btn.click()

        download = await dl_info.value
        await download.save_as(OUTPUT_PATH)

        size = os.path.getsize(OUTPUT_PATH)
        print(f"  Downloaded {size:,} bytes")

        valid, cols, msg = validate_csv(OUTPUT_PATH)
        if not valid:
            await save_debug_info(page)
            await browser.close()
            raise RuntimeError(f"Wrong CSV exported: {msg}. Check debug artifact.")

        print(f"  Valid transaction CSV. Columns: {cols}")
        if size < 10_000:
            raise RuntimeError(f"CSV is only {size} bytes — suspiciously small.")

        await browser.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(fetch())
