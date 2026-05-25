"""
fetch_adrec.py
--------------
Uses Playwright (headless Chrome) to open the ADREC dashboard,
set the full date range (01/01/2019 → today), click Export, and
save the downloaded CSV to scripts/data/adrec_raw.csv.

When the Export button cannot be found, saves a full-page screenshot,
the page HTML, and a list of all buttons/frames to scripts/data/ so
the debug artifact can be inspected in GitHub Actions.
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

ADREC_URL   = "https://adrec.gov.ae/en/property_and_index/adrec-dashboard"
OUTPUT_PATH = "scripts/data/adrec_raw.csv"
DEBUG_DIR   = "scripts/data"


async def accept_cookies(page):
    """Dismiss cookie / consent banners so they don't block clicks."""
    selectors = [
        "button:has-text('Accept All')",
        "button:has-text('Accept')",
        "button:has-text('I Accept')",
        "button:has-text('Agree')",
        "button:has-text('OK')",
        "button:has-text('Continue')",
        "[id*='accept' i]",
        "[class*='accept' i]",
        "[id*='cookie' i] button",
        "[class*='cookie' i] button",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=2_000):
                await btn.click()
                print(f"  Accepted cookies via: {sel!r}")
                await page.wait_for_timeout(1_500)
                return True
        except Exception:
            continue
    return False


EXPORT_SELECTORS = [
    "button:has-text('Export')",
    "a:has-text('Export')",
    "button:has-text('Download')",
    "a:has-text('Download')",
    "text=Export",
    "text=Download",
    "[class*='export' i]",
    "[class*='download' i]",
    "button[title*='export' i]",
    "button[title*='download' i]",
    "a[title*='export' i]",
    "[aria-label*='export' i]",
    "[aria-label*='download' i]",
    # Arabic equivalents
    "button:has-text('تصدير')",
    "button:has-text('تنزيل')",
    # Power BI / embedded BI tools
    "button[data-testid*='export' i]",
    "[title='Export data']",
    "[title='More options']",   # Power BI "…" menu that leads to export
]


async def find_export_button(page):
    """Search main page and every iframe for the Export button."""
    # ── Main page ──────────────────────────────────────────────────────────
    for sel in EXPORT_SELECTORS:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=2_000):
                print(f"  Export button found in main page: {sel!r}")
                return btn
        except Exception:
            continue

    # ── All iframes ────────────────────────────────────────────────────────
    frames = page.frames
    print(f"  Scanning {len(frames)} frame(s) for Export button…")
    for i, frame in enumerate(frames):
        if frame == page.main_frame:
            continue
        print(f"    Frame {i}: {frame.url[:100]}")
        for sel in EXPORT_SELECTORS:
            try:
                btn = frame.locator(sel).first
                if await btn.is_visible(timeout=1_500):
                    print(f"    Export button found in frame {i}: {sel!r}")
                    return btn
            except Exception:
                continue

    return None


async def save_debug_info(page):
    """Persist everything useful for post-mortem inspection."""
    os.makedirs(DEBUG_DIR, exist_ok=True)

    # Full-page screenshot
    ss_path = f"{DEBUG_DIR}/debug_screenshot.png"
    await page.screenshot(path=ss_path, full_page=True)
    print(f"  Screenshot saved → {ss_path}")

    # Raw HTML
    html_path = f"{DEBUG_DIR}/debug_page.html"
    html = await page.content()
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  HTML saved       → {html_path}")

    # All interactive elements
    try:
        texts = await page.locator("button, a, [role='button']").all_text_contents()
        clean = [t.strip() for t in texts if t.strip()]
        print(f"  Buttons/links ({len(clean)}): {clean[:40]}")
    except Exception:
        pass

    # Frame list
    frames = page.frames
    print(f"  Frames ({len(frames)}):")
    for i, f in enumerate(frames):
        print(f"    [{i}] {f.url[:120]}")


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

        # Accept cookie / consent banner
        await accept_cookies(page)
        await page.wait_for_timeout(2_000)

        # Scroll to trigger lazy-loaded content
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2_000)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(2_000)

        # ── Set date range ──────────────────────────────────────────────────
        today_str = datetime.utcnow().strftime("%m/%d/%Y")
        start_str = "01/01/2019"

        for label, value in [("start", start_str), ("end", today_str)]:
            try:
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

        await page.wait_for_timeout(3_000)

        # ── Find Export button ──────────────────────────────────────────────
        export_btn = await find_export_button(page)

        if export_btn is None:
            await save_debug_info(page)
            await browser.close()
            raise RuntimeError(
                "Could not find the Export button. "
                "Download the 'adrec-debug' artifact from GitHub Actions "
                "to inspect debug_screenshot.png and debug_page.html."
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
