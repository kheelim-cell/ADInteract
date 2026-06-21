"""
fetch_dari_directory.py
------------------------
Scrapes DARI's public Professions directory (brokers, agencies, developers,
evaluators, auctioneers, surveyors, account trustees) — list-view only, v1.

Source: https://www.dari.ae/en/app/directory?category=professions
No login, no CAPTCHA. Confirmed via manual Playwright exploration that the
"Profession" filter is a client-side MUI select driving a `professionType`
query param. Canonical param values (confirmed by driving the UI, not
guessed — the URL value differs from the display label for 3 of 6):

    display label      -> professionType=
    Broker              -> Broker
    Evaluators          -> Evaluator
    Auctioneer          -> Auctioneer
    Surveyors           -> Surveying
    Account trustees    -> Account_Keeper
    Developer           -> Developer

For each profession we just read the "<N> Results" count off the filtered
page — six page loads instead of paginating ~430 pages of cards. We also
grab the first page of cards (up to SAMPLE_LIMIT) for every profession type
as illustrative directory samples (company name + sub-label only; license
numbers and dates live in the per-card detail panel, which is NOT scraped
in v1 — that's a heavier per-record fetch, deferred to v2 alongside the
top-agency broker-headcount ranking).

Output: scripts/data/dari_directory_raw.json

Usage:
    python scripts/fetch_dari_directory.py
"""

import json
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

DIRECTORY_URL = "https://www.dari.ae/en/app/directory?category=professions&page=1"

# (display label, professionType URL param) — param confirmed by driving the
# real dropdown + "Show results" button, not guessed from the label text.
PROFESSIONS = [
    ("Broker", "Broker"),
    ("Evaluators", "Evaluator"),
    ("Auctioneer", "Auctioneer"),
    ("Surveyors", "Surveying"),
    ("Account trustees", "Account_Keeper"),
    ("Developer", "Developer"),
]

SAMPLE_PROFESSIONS = [label for label, _ in PROFESSIONS]  # grab card samples for every profession type
SAMPLE_LIMIT = 15  # per profession — enough for the page's profession filter + "show more" UI

OUTPUT_DIR = Path("scripts/data")
OUTPUT_FILE = OUTPUT_DIR / "dari_directory_raw.json"
DEBUG_SCREENSHOT = OUTPUT_DIR / "dari_directory_debug.png"

RESULTS_RE = re.compile(r"([\d,]+)\s*Results", re.I)


def read_results_count(page) -> int | None:
    text = page.inner_text("body")
    m = RESULTS_RE.search(text)
    if m:
        return int(m.group(1).replace(",", ""))
    if "no professions with your filters" in text.lower():
        return 0
    return None


def scrape_all_cards(page) -> list[str]:
    """Return the raw cleaned leaf-text list for the current directory page
    (name/classification pairs interleaved), for full-pagination scrapes."""
    cards = page.eval_on_selector_all(
        "[class*=jss]",
        """els => els
            .filter(e => e.children.length === 0 && e.textContent.trim())
            .map(e => e.textContent.trim())"""
    )
    skip_words = {"Profession", "Classification", "Filters", "Clear all",
                  "Select Profession", "Show results"}
    return [c for c in cards if c not in skip_words and c not in {p[0] for p in PROFESSIONS}]


def count_developer_classifications(page, total_results: int) -> dict[str, int]:
    """Developer profession is small (~130-150 results, ~12 pages) — cheap
    enough to fully paginate and tally Primary vs Secondary developer counts
    straight from each card's classification label, matching the breakdown
    competitors report (e.g. '38 primary / 94 secondary')."""
    per_page_guess = 12
    last_page = max(1, -(-total_results // per_page_guess))  # ceil div, just an upper bound
    tally: dict[str, int] = {}
    page_num = 1
    seen_names: set[str] = set()

    while True:
        url = f"https://www.dari.ae/en/app/directory?category=professions&page={page_num}&professionType=Developer"
        page.goto(url, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(1800)

        cleaned = scrape_all_cards(page)
        i = 0
        new_on_page = 0
        while i < len(cleaned) - 1:
            name, sub = cleaned[i], cleaned[i + 1]
            if len(sub) < 30 and name not in seen_names:
                seen_names.add(name)
                tally[sub] = tally.get(sub, 0) + 1
                new_on_page += 1
                i += 2
            else:
                i += 1

        if new_on_page == 0 or page_num >= last_page + 2:
            break
        page_num += 1

    return tally


def scrape_card_samples(page, limit: int = 6) -> list[dict]:
    """Grab company name + sub-label (e.g. 'Brokerage') for the first N cards
    on the current (already-filtered) directory page. List-view only."""
    cleaned = scrape_all_cards(page)

    samples = []
    i = 0
    while i < len(cleaned) - 1 and len(samples) < limit:
        name, sub = cleaned[i], cleaned[i + 1]
        # heuristic: sub-labels are short, known classification words
        if len(sub) < 30:
            samples.append({"name": name, "classification": sub})
            i += 2
        else:
            i += 1
    return samples


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    launch_kwargs = dict(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
    )
    if os.environ.get("ADREC_USE_SYSTEM_CHROME") == "1":
        launch_kwargs["channel"] = "chrome"

    counts: dict[str, int] = {}
    samples: dict[str, list[dict]] = {}

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

        for label, param in PROFESSIONS:
            url = f"https://www.dari.ae/en/app/directory?category=professions&page=1&professionType={param}"
            print(f"Fetching {label} ({param})…")
            page.goto(url, wait_until="networkidle", timeout=60_000)
            page.wait_for_timeout(2500)

            n = read_results_count(page)
            if n is None:
                print(f"  WARNING: could not read results count for {label} — saving debug screenshot")
                page.screenshot(path=str(DEBUG_SCREENSHOT))
                continue
            counts[label] = n
            print(f"  {label}: {n} results")

            if label in SAMPLE_PROFESSIONS:
                samples[label] = scrape_card_samples(page, limit=SAMPLE_LIMIT)

        developer_breakdown = {}
        if counts.get("Developer"):
            print("Pagination: tallying Primary vs Secondary developer classifications…")
            developer_breakdown = count_developer_classifications(page, counts["Developer"])
            print(f"  {developer_breakdown}")

        browser.close()

    output = {
        "counts": counts,
        "total": sum(counts.values()),
        "samples": samples,
        "developer_breakdown": developer_breakdown,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {OUTPUT_FILE}")
    print(f"Total professionals: {output['total']}")
    if not counts:
        raise SystemExit("ERROR: no profession counts captured — DARI directory layout may have changed")


if __name__ == "__main__":
    main()
