"""
fetch_adrec.py
--------------
Uses Playwright (headless Chrome) to open the ADREC dashboard,
set the full date range (01/01/2019 → today), click Export, and
save the downloaded CSV to scripts/data/adrec_raw.csv.
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

ADREC_URL = "https://adrec.gov.ae/en/property_and_index/adrec-dashboard"
OUTPUT_PATH = "scripts/data/adrec_raw.csv"


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
        # Extra wait for JS-rendered content
        await page.wait_for_timeout(6_000)

        # ── Set date range ──────────────────────────────────────────────────
        today_str = datetime.utcnow().strftime("%m/%d/%Y")  # MM/DD/YYYY
        start_str = "01/01/2019"

        # Try to find date inputs and update end date to today
        for label, value in [("start", start_str), ("end", today_str)]:
            try:
                # Date inputs: look for <input type="date"> or styled date pickers
                inputs = page.locator(
                    "input[type='date'], "
                    "input[placeholder*='date' i], "
                    "input[placeholder*='from' i], "
                    "input[placeholder*='to' i], "
                    "[class*='datepicker'] input, "
                    "[class*='date-picker'] input"
                )
                count = await inputs.count()
                if count >= 2:
                    idx = 0 if label == "start" else 1
                    el = inputs.nth(idx)
                    await el.triple_click()
                    await el.fill(value)
                    await page.keyboard.press("Tab")
                    await page.wait_for_timeout(800)
                    print(f"  Set {label} date → {value}")
            except Exception as exc:
                print(f"  Could not set {label} date: {exc}")

        await page.wait_for_timeout(2_000)

        # ── Find Export button ──────────────────────────────────────────────
        selectors = [
            "button:has-text('Export')",
            "a:has-text('Export')",
            "text=Export",
            "[class*='export' i]",
            "button[title*='export' i]",
            "a[title*='export' i]",
        ]

        export_btn = None
        for sel in selectors:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=3_000):
                    export_btn = btn
                    print(f"  Found Export button: {sel!r}")
                    break
            except Exception:
                continue

        if export_btn is None:
            # Last resort: screenshot for debugging
            await page.screenshot(path="scripts/data/debug_screenshot.png", full_page=True)
            raise RuntimeError(
                "Could not find the Export button. "
                "Check scripts/data/debug_screenshot.png for what Playwright saw."
            )

        # ── Download ────────────────────────────────────────────────────────
        print("  Clicking Export and waiting for download…")
        async with page.expect_download(timeout=90_000) as dl_info:
            await export_btn.click()

        download = await dl_info.value
        await download.save_as(OUTPUT_PATH)

        size = os.path.getsize(OUTPUT_PATH)
        print(f"  Saved → {OUTPUT_PATH}  ({size:,} bytes)")

        if size < 2_000:
            raise RuntimeError(
                f"Downloaded file is only {size} bytes — likely an error page, not data."
            )

        await browser.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(fetch())
