"""
fetch_dari_projects.py
-----------------------
Scrapes DARI's public Projects directory (the construction-completion %
and project-type data ADX's "New Projects" page is built from) — list-view
only, no detail-panel clicks needed since completion % is already in the
card text.

Source: https://www.dari.ae/en/app/directory?category=projects
~289 results, ~25 pages at 12/page — cheap, no login, no CAPTCHA.

This script intentionally does NOT scrape "Sold %" or "available units" —
those fields don't exist anywhere in this public directory (list or detail
view). Any site reporting them from DARI public data is estimating, not
reporting. We pair this with our own honest metric (registered-sales
velocity from ADREC transactions, see compute_project_pipeline.py) instead
of fabricating a sold percentage.

Each card also carries a real project image (Azure blob storage URL under
DARI's own public path, e.g. dmtstrguae1dev.blob.core.windows.net/public/
projects/...) — this is the actual render DARI itself serves to every
visitor of the public directory, not a third-party asset, so we link to it
directly (hotlink) rather than copy/rehost it.

Output: scripts/data/dari_projects_raw.json

Usage:
    python scripts/fetch_dari_projects.py
"""

import json
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

LIST_URL_TEMPLATE = "https://www.dari.ae/en/app/directory?category=projects&page={page}"
OUTPUT_DIR = Path("scripts/data")
OUTPUT_FILE = OUTPUT_DIR / "dari_projects_raw.json"

RESULTS_RE = re.compile(r"([\d,]+)\s*Results", re.I)
PAGE_SIZE = 12

STATUS_WORDS = {"New", "Ready", "Built"}

CARD_RE = re.compile(
    r"^(?P<type>.*?)\n"
    r"(?P<status>New|Ready|Built)\n*\n"
    r"(?P<name>.+?)\n*\n"
    r"Project Number:\s*(?P<project_number>\S+)\n*\n"
    r"(?P<completion>\d+)%\s*Completion\n*\n"
    r"(?P<rest>.+)$",
    re.DOTALL,
)
# "Plot" type cards skip the classification line entirely and go straight
# to the location string — confirmed by inspecting actual failed parses
# (e.g. "Emirates Palace Mansions" / "Bayn – Views 1"). Only treat the
# pre-location line as a classification if it's one of the three known
# values; otherwise it's already the start of the location string.
KNOWN_CLASSIFICATIONS = {"Residential", "Mixed use", "Commercial"}


def parse_card(text: str, image_url: str | None) -> dict | None:
    text = text.strip()
    # A handful of cards have no leading "type" line at all — the card
    # starts straight with the status word. Confirmed via manual inspection
    # (e.g. "Al Deem Townhomes"). Insert an empty type line so the regex
    # still matches consistently.
    first_line = text.split("\n", 1)[0].strip()
    if first_line in STATUS_WORDS:
        text = "\n" + text

    m = CARD_RE.match(text)
    if not m:
        return None

    rest_lines = [l.strip() for l in m.group("rest").split("\n") if l.strip()]
    if not rest_lines:
        return None

    if rest_lines[0] in KNOWN_CLASSIFICATIONS:
        classification = rest_lines[0]
        location = ", ".join(rest_lines[1:])
    else:
        classification = None
        location = ", ".join(rest_lines)

    location_parts = [p.strip() for p in location.split(",")]
    return {
        "name": re.sub(r"\s+", " ", m.group("name")).strip(),
        "type": m.group("type").strip() or None,
        "status": m.group("status").strip(),
        "project_number": m.group("project_number").strip(),
        "completion_pct": int(m.group("completion")),
        "classification": classification,
        "district": location_parts[1] if len(location_parts) > 1 else None,
        "community": location_parts[2] if len(location_parts) > 2 else None,
        "image_url": image_url,
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    launch_kwargs = dict(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
    )
    if os.environ.get("ADREC_USE_SYSTEM_CHROME") == "1":
        launch_kwargs["channel"] = "chrome"

    projects: list[dict] = []
    parse_errors = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        page.goto(LIST_URL_TEMPLATE.format(page=1), wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(2000)
        body = page.inner_text("body")
        m = RESULTS_RE.search(body)
        total = int(m.group(1).replace(",", "")) if m else 0
        total_pages = max(1, -(-total // PAGE_SIZE))
        print(f"Total projects: {total} ({total_pages} pages)")

        for page_num in range(1, total_pages + 1):
            page.goto(LIST_URL_TEMPLATE.format(page=page_num), wait_until="networkidle", timeout=60_000)
            page.wait_for_timeout(1500)

            cards = page.query_selector_all(".MuiCard-root")
            print(f"Page {page_num}/{total_pages}: {len(cards)} cards")
            for c in cards:
                img = c.query_selector("img")
                image_url = img.get_attribute("src") if img else None
                if image_url and "blob.core.windows.net" not in image_url:
                    image_url = None  # only trust DARI's own public asset host, not stray icons
                parsed = parse_card(c.inner_text(), image_url)
                if parsed:
                    projects.append(parsed)
                else:
                    parse_errors += 1

        browser.close()

    output = {
        "total_scraped": len(projects),
        "parse_errors": parse_errors,
        "projects": projects,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {OUTPUT_FILE}")
    print(f"Scraped {len(projects)} projects, {parse_errors} parse errors")
    if not projects:
        raise SystemExit("ERROR: no projects parsed — DARI directory layout may have changed")


if __name__ == "__main__":
    main()
