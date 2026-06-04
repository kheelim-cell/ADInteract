"""
fetch_adrec.py
--------------
Uses Playwright (headless Chrome) to open the ADREC dashboard,
set the date range (01/01/2019 → today), and click the Export button
in the "Recent Sales" section header (5th export button, index 4).

Key fix: the page has a dismissible popup (× button) that blocks the
dashboard from rendering. We close it, then wait until the dashboard
content is actually visible before searching for Export.
"""

import asyncio
import csv
import os
from datetime import datetime
from playwright.async_api import async_playwright

ADREC_URL   = "https://www.dari.ae/adrec/MarketDetails.html"
OUTPUT_PATH = "scripts/data/adrec_raw.csv"
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
    """Close cookie banners, modals, and any × popup blocking the dashboard."""
    selectors = [
        # Standard accept buttons
        "button:has-text('Accept All')",
        "button:has-text('Accept')",
        "button:has-text('I Accept')",
        "button:has-text('Agree')",
        "button:has-text('OK')",
        # × close buttons (the one blocking the ADREC dashboard)
        "button:has-text('×')",
        "button:has-text('✕')",
        "button[aria-label='Close']",
        "button[aria-label='close']",
        "[class*='modal'] button[class*='close']",
        "[class*='popup'] button[class*='close']",
        "[class*='cookie'] button",
        "[id*='cookie'] button",
        "[id*='accept']",
        "[class*='accept']",
    ]
    dismissed = 0
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1_500):
                await btn.click()
                print(f"  Dismissed overlay via: {sel!r}")
                await page.wait_for_timeout(1_000)
                dismissed += 1
        except Exception:
            pass
    return dismissed


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
        texts = [t.strip() for t in
                 await page.locator("button, a, [role='button']").all_text_contents()
                 if t.strip()]
        print(f"  All buttons/links ({len(texts)}): {texts[:60]}")
    except Exception:
        pass
    frames = page.frames
    print(f"  Frames ({len(frames)}): {[f.url[:80] for f in frames]}")


async def wait_for_dashboard(page, timeout_ms=40_000):
    """
    Wait until the dashboard content is actually on screen.
    Returns True if found, False if timed out.
    """
    indicators = [
        "text=Recent Sales",
        "text=Export",
        "[class*='export' i]",
        "table",
        "[class*='table' i]",
        "[class*='grid' i]",
        "[class*='datatable' i]",
    ]
    for sel in indicators:
        try:
            await page.wait_for_selector(sel, timeout=timeout_ms)
            print(f"  Dashboard ready: found {sel!r}")
            return True
        except Exception:
            continue
    return False


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
        await page.wait_for_timeout(5_000)

        # ── Round 1: dismiss any initial overlays ───────────────────────────
        await dismiss_overlays(page)
        await page.wait_for_timeout(2_000)

        # ── Wait for the dashboard to render ────────────────────────────────
        loaded = await wait_for_dashboard(page, timeout_ms=30_000)

        # ── Round 2: if still not loaded, dismiss again and wait more ───────
        if not loaded:
            print("  Dashboard not ready after round 1 — trying overlay dismissal again…")
            await dismiss_overlays(page)
            await page.wait_for_timeout(3_000)
            loaded = await wait_for_dashboard(page, timeout_ms=20_000)

        if not loaded:
            print("  Dashboard still not rendered. Saving debug info…")
            await save_debug_info(page)
            await browser.close()
            raise RuntimeError(
                "Dashboard did not render. "
                "Check the adrec-debug artifact for debug_screenshot.png."
            )

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
                    await el.fill(value)
                    await page.keyboard.press("Tab")
                    await page.wait_for_timeout(800)
                    print(f"  Set {label} date → {value}")
            except Exception as exc:
                print(f"  Could not set {label} date: {exc}")

        await page.wait_for_timeout(3_000)

        # ── Scroll to load lazy content ─────────────────────────────────────
        for y in [600, 1200, 2000, 3000]:
            await page.evaluate(f"window.scrollTo(0, {y})")
            await page.wait_for_timeout(600)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1_000)

        # ── Find and click the correct Export button ────────────────────────
        all_exports = page.locator("a:has-text('Export'), button:has-text('Export')")
        count = await all_exports.count()
        print(f"  Total Export buttons found: {count}")

        if count == 0:
            await save_debug_info(page)
            await browser.close()
            raise RuntimeError(
                "No Export buttons found after dashboard loaded. "
                "Check the adrec-debug artifact."
            )

        # Primary: try the 5th button (index 4) — the "Recent Sales" Export
        primary_index = 4
        success = False

        if count >= primary_index + 1:
            print(f"  Trying primary: Export button #{primary_index + 1} (index {primary_index})…")
            btn = all_exports.nth(primary_index)
            try:
                await btn.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                tmp = OUTPUT_PATH + ".tmp"
                async with page.expect_download(timeout=60_000) as dl_info:
                    await btn.click()
                dl = await dl_info.value
                await dl.save_as(tmp)
                size = os.path.getsize(tmp)
                valid, cols, msg = validate_csv(tmp)
                if valid:
                    os.replace(tmp, OUTPUT_PATH)
                    print(f"  Primary Export #{primary_index + 1} succeeded. Columns: {cols}")
                    success = True
                else:
                    os.remove(tmp)
                    print(f"  Primary Export #{primary_index + 1} rejected ({size:,} bytes): {msg}")
            except Exception as exc:
                print(f"  Primary Export #{primary_index + 1} error: {exc}")

        # Fallback: try all buttons in order
        if not success:
            print("  Falling back — trying all Export buttons…")
            for i in range(count):
                if i == primary_index:
                    continue  # already tried
                btn = all_exports.nth(i)
                if not await btn.is_visible(timeout=1_000):
                    continue
                print(f"  Trying Export #{i + 1} (index {i})…")
                try:
                    await btn.scroll_into_view_if_needed()
                    await page.wait_for_timeout(300)
                    tmp = OUTPUT_PATH + ".tmp"
                    async with page.expect_download(timeout=60_000) as dl_info:
                        await btn.click()
                    dl = await dl_info.value
                    await dl.save_as(tmp)
                    size = os.path.getsize(tmp)
                    valid, cols, msg = validate_csv(tmp)
                    if valid:
                        os.replace(tmp, OUTPUT_PATH)
                        print(f"  Export #{i + 1} succeeded. Columns: {cols}")
                        success = True
                        break
                    else:
                        os.remove(tmp)
                        print(f"  Export #{i + 1} rejected ({size:,} bytes): {msg}")
                except Exception as exc:
                    print(f"  Export #{i + 1} error: {exc}")

        if not success:
            await save_debug_info(page)
            await browser.close()
            raise RuntimeError(
                "No Export button produced transaction-level data. "
                "Check the adrec-debug artifact (debug_screenshot.png)."
            )

        size = os.path.getsize(OUTPUT_PATH)
        print(f"\n  Final CSV → {OUTPUT_PATH}  ({size:,} bytes)")
        if size < 10_000:
            raise RuntimeError(f"CSV is only {size} bytes — suspiciously small.")

        await browser.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(fetch())
