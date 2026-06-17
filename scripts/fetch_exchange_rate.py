"""
fetch_exchange_rate.py
---------------------
Fetches the current USD/AED rate from a free API and writes it to
static/data/config.json. AED is pegged to USD (~3.6725) so this rarely
changes, but is worth updating daily for accuracy.

Falls back gracefully to the existing file value if the API is unreachable.
"""

import json
import os
import sys
from datetime import date

CONFIG_PATH = "static/data/config.json"
FALLBACK_RATE = 3.6725  # AED peg to USD


def fetch_rate() -> float:
    try:
        import urllib.request
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            rate = data["rates"].get("AED")
            if rate:
                print(f"  Fetched USD/AED rate: {rate}")
                return float(rate)
    except Exception as exc:
        print(f"  Warning: could not fetch exchange rate ({exc}) — using fallback {FALLBACK_RATE}")
    return FALLBACK_RATE


def main():
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

    # Load existing config (preserve other keys)
    config = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                config = json.load(f)
        except Exception:
            pass

    rate = fetch_rate()
    config["usd_aed_rate"] = rate
    config["usd_aed_rate_updated"] = str(date.today())
    config.setdefault("note", "AED is pegged to USD. Rate updated daily by CI via fetch_exchange_rate.py.")

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print(f"  Wrote {CONFIG_PATH}")


if __name__ == "__main__":
    main()
