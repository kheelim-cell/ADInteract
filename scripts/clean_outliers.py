"""
clean_outliers.py
------------------
One-off (re-runnable) pass that applies transform.py's outlier filter to the
EXISTING static/data/transactions.parquet in place, then regenerates meta.json.

Use this to retroactively purge outliers already baked into the parquet from
before the filter existed. The daily pipeline (transform.py) applies the same
filter going forward automatically — this script exists so the fix doesn't
have to wait for tomorrow's cron run.

Usage:  python scripts/clean_outliers.py
"""

import json

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from transform import OUTPUT_PARQUET, OUTPUT_META, apply_outlier_filters, build_meta


def main():
    print(f"Reading {OUTPUT_PARQUET}…")
    df = pd.read_parquet(OUTPUT_PARQUET)
    print(f"  Rows before: {len(df):,}")

    cleaned = apply_outlier_filters(df)

    table = pa.Table.from_pandas(cleaned, preserve_index=False)
    pq.write_table(table, OUTPUT_PARQUET, compression="zstd")
    print(f"  Wrote {OUTPUT_PARQUET} — {len(cleaned):,} rows remain "
          f"({len(df) - len(cleaned):,} removed)")

    with open(OUTPUT_META, "w", encoding="utf-8") as f:
        json.dump(build_meta(cleaned), f, ensure_ascii=False)
    print(f"  Wrote {OUTPUT_META}")


if __name__ == "__main__":
    main()
