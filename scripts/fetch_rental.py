"""
fetch_rental.py
---------------
Captures an ArcGIS session token from the ADREC Interactive Map page (via Playwright),
then paginates the LeaseAnalysis/MapServer/18 layer to download the full rental index
dataset. Output: scripts/data/rental_raw.json

Usage:
    python scripts/fetch_rental.py
"""

import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

# ─── Config ────────────────────────────────────────────────────────────────────
INTERACTIVE_MAP_URL = (
    "https://adrec.gov.ae/en/property_and_index/interactive-map"
)
ARCGIS_BASE = (
    "https://gis.adres.ae/server/rest/services/ADREC"
    "/LeaseAnalysis/MapServer/18/query"
)
FIELDS = [
    "project_id",
    "project_name",
    "project_number",
    "municipality",
    "municipality_id",
    "district",
    "district_id",
    "community",
    "community_id",
    "typology",
    "layout",
    "lable",
    "lower_rent_value",
    "avg_rent_value",
    "upper_rent_value",
    "year",
    "rent_type",
]
PAGE_SIZE = 2000
OUTPUT_DIR = Path("scripts/data")
OUTPUT_FILE = OUTPUT_DIR / "rental_raw.json"
DEBUG_SCREENSHOT = OUTPUT_DIR / "rental_debug_screenshot.png"
DEBUG_HTML = OUTPUT_DIR / "rental_debug_page.html"
TOKEN_TIMEOUT_S = 60  # seconds to wait for a token request to appear
# ───────────────────────────────────────────────────────────────────────────────


def capture_token() -> str | None:
    """
    Launch Chromium headless, navigate to the ADREC Interactive Map, and
    intercept the first network request to gis.adres.ae that carries a token.
    Returns the token string, or None if none was captured within the timeout.
    """
    captured: dict = {}

    def on_request(request):
        url = request.url
        if "gis.adres.ae" in url and "token=" in url:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            token_list = params.get("token", [])
            if token_list and not captured.get("token"):
                captured["token"] = token_list[0]
                print(f"[fetch_rental] Token captured from: {url[:120]}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.on("request", on_request)

        print(f"[fetch_rental] Loading: {INTERACTIVE_MAP_URL}")
        try:
            page.goto(INTERACTIVE_MAP_URL, wait_until="domcontentloaded", timeout=60_000)
        except PwTimeout:
            print("[fetch_rental] Page load timed out — continuing anyway")

        # Wait up to TOKEN_TIMEOUT_S seconds for a token to be intercepted
        deadline = time.time() + TOKEN_TIMEOUT_S
        while not captured.get("token") and time.time() < deadline:
            # Try clicking the "Average Rent Prices" tab if it exists, to
            # force the rental layer to load and emit an authenticated request.
            try:
                tab_locator = page.locator(
                    "text=/average rent/i, [data-label*='rent' i], "
                    "button:has-text('Rent'), a:has-text('Rent')"
                ).first
                if tab_locator.is_visible(timeout=2_000):
                    tab_locator.click()
                    print("[fetch_rental] Clicked rent tab — waiting for token")
            except Exception:
                pass
            time.sleep(1)

        # Save debug artefacts regardless of outcome
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        try:
            page.screenshot(path=str(DEBUG_SCREENSHOT), full_page=False)
            DEBUG_HTML.write_text(page.content(), encoding="utf-8")
        except Exception as exc:
            print(f"[fetch_rental] Warning: could not save debug artefacts: {exc}")

        browser.close()

    return captured.get("token")


def fetch_all(token: str) -> list[dict]:
    """
    Paginate through all records on MapServer layer 18 using the given token.
    Returns a flat list of attribute dicts.
    """
    records: list[dict] = []
    offset = 0

    session = requests.Session()
    session.headers.update(
        {
            "Referer": INTERACTIVE_MAP_URL,
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }
    )

    print(f"[fetch_rental] Starting paginated fetch (page size={PAGE_SIZE})")
    while True:
        params = {
            "where": "1=1",
            "outFields": ",".join(FIELDS),
            "returnGeometry": "false",
            "resultRecordCount": PAGE_SIZE,
            "resultOffset": offset,
            "f": "json",
            "token": token,
        }
        resp = session.get(ARCGIS_BASE, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            raise RuntimeError(
                f"ArcGIS error {data['error'].get('code')}: "
                f"{data['error'].get('message')}"
            )

        features = data.get("features", [])
        batch = [f["attributes"] for f in features]
        records.extend(batch)
        print(f"[fetch_rental]   offset={offset:6d}  fetched={len(batch):4d}  total={len(records):6d}")

        if len(batch) < PAGE_SIZE:
            break  # last page
        offset += PAGE_SIZE

    return records


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[fetch_rental] === Rental Index Fetch ===")

    # ── Step 1: capture token ──────────────────────────────────────────────
    token = capture_token()
    if not token:
        raise RuntimeError(
            "Could not capture ArcGIS session token from the interactive map. "
            "Check rental_debug_screenshot.png and rental_debug_page.html for clues."
        )
    print(f"[fetch_rental] Token: {token[:20]}...")

    # ── Step 2: paginated download ─────────────────────────────────────────
    records = fetch_all(token)

    if not records:
        raise RuntimeError(
            "No records returned from ArcGIS layer 18. "
            "The layer may be empty or the token may have expired mid-fetch."
        )

    # ── Step 3: write raw JSON ─────────────────────────────────────────────
    OUTPUT_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[fetch_rental] Saved {len(records):,} records → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
