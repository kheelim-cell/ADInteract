"""
compute_market_structure.py
----------------------------
Transforms the raw DARI directory scrape (scripts/data/dari_directory_raw.json)
into the JSON the /investors/market-structure page reads.

v1 scope: counts by profession type + a Primary/Secondary developer split +
a handful of illustrative directory samples. Does NOT rank agencies by
broker headcount — that needs a per-company detail-panel fetch (the
employee list), which is a heavier scrape deferred to v2.

Run after fetch_dari_directory.py.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

RAW_INPUT = Path("scripts/data/dari_directory_raw.json")
OUTPUT    = Path("src/lib/data/market_structure.json")


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
        "samples": {
            profession: [
                {"name": re.sub(r"\s+", " ", s["name"]).strip(), "classification": s["classification"]}
                for s in entries
            ]
            for profession, entries in raw.get("samples", {}).items()
        },
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Wrote {OUTPUT}")
    print(f"  total licensed: {output['total_licensed']}")
    for row in output["by_profession"]:
        print(f"  {row['label']}: {row['count']}")


if __name__ == "__main__":
    main()
