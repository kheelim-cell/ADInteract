"""
compute_market_structure.py
----------------------------
Transforms the raw DARI directory scrapes into the JSON the
/investors/market-structure page reads.

v1 scope (scripts/data/dari_directory_raw.json, from fetch_dari_directory.py):
  - counts by profession type
  - Primary/Secondary developer split
  - Company/Individual broker split (agencies vs independent brokers)
  - illustrative directory samples

v2 scope (scripts/data/dari_agency_rankings_raw.json, from
fetch_dari_agency_rankings.py — optional, ~45-60min full scrape):
  - top agencies ranked by broker employee headcount

If the v2 file isn't present yet (first run, or local dev without the long
scrape), agency_rankings is written as an empty list and the page shows
its "coming soon" state — this script never fails just because v2 data is
missing.

Run after fetch_dari_directory.py (and optionally fetch_dari_agency_rankings.py).
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

RAW_INPUT          = Path("scripts/data/dari_directory_raw.json")
AGENCY_RAW_INPUT   = Path("scripts/data/dari_agency_rankings_raw.json")
OUTPUT             = Path("src/lib/data/market_structure.json")
TOP_AGENCIES_LIMIT = 15


def main():
    if not RAW_INPUT.exists():
        raise SystemExit(f"ERROR: {RAW_INPUT} not found — run fetch_dari_directory.py first")

    with open(RAW_INPUT, encoding="utf-8") as f:
        raw = json.load(f)

    counts = raw.get("counts", {})
    if not counts:
        raise SystemExit("ERROR: raw scrape has no profession counts — refusing to overwrite market_structure.json")

    os.makedirs(OUTPUT.parent, exist_ok=True)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_licensed": raw.get("total", sum(counts.values())),
        "by_profession": [
            {"label": "Brokers",          "count": counts.get("Broker", 0)},
            {"label": "Surveyors",        "count": counts.get("Surveyors", 0)},
            {"label": "Evaluators",       "count": counts.get("Evaluators", 0)},
            {"label": "Account trustees", "count": counts.get("Account trustees", 0)},
            {"label": "Developers",       "count": counts.get("Developer", 0)},
            {"label": "Auctioneers",      "count": counts.get("Auctioneer", 0)},
        ],
        "developer_breakdown": raw.get("developer_breakdown", {}),
        "broker_breakdown": raw.get("broker_breakdown", {}),
        "samples": {
            profession: [
                {"name": re.sub(r"\s+", " ", s["name"]).strip(), "classification": s["classification"]}
                for s in entries
            ]
            for profession, entries in raw.get("samples", {}).items()
        },
        "agency_rankings": [],
        "agency_rankings_total_scraped": 0,
    }

    if AGENCY_RAW_INPUT.exists():
        with open(AGENCY_RAW_INPUT, encoding="utf-8") as f:
            agency_raw = json.load(f)
        agencies = agency_raw.get("agencies", [])
        output["agency_rankings"] = [
            {"name": re.sub(r"\s+", " ", a["name"]).strip(), "employee_count": a["employee_count"]}
            for a in agencies[:TOP_AGENCIES_LIMIT]
        ]
        output["agency_rankings_total_scraped"] = agency_raw.get("total_companies_seen", len(agencies))

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Wrote {OUTPUT}")
    print(f"  total licensed: {output['total_licensed']}")
    for row in output["by_profession"]:
        print(f"  {row['label']}: {row['count']}")
    if output["broker_breakdown"]:
        print(f"  broker breakdown: {output['broker_breakdown']}")
    if output["agency_rankings"]:
        print(f"  agency rankings: top {len(output['agency_rankings'])} of {output['agency_rankings_total_scraped']} scraped")
    else:
        print("  agency rankings: none (run fetch_dari_agency_rankings.py to populate)")


if __name__ == "__main__":
    main()
