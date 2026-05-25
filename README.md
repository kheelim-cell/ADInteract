# ADInteract -- Abu Dhabi Property Transaction Analytics

Interactive dashboard for exploring Abu Dhabi real estate transaction data. Filter by district, community, property type, layout, and date range. Visualize trends, compare areas, and drill into individual transactions.

![Screenshot placeholder](docs/screenshot.png)

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/your-org/ADInteract.git
cd ADInteract

# 2. Install Node dependencies
npm install

# 3. Generate data from a local CSV export
python scripts/fetch_and_transform.py --local-csv path/to/exported.csv

# 4. Start the dev server
npm run dev

# 5. Open in browser
# http://localhost:5173
```

### Python setup (one-time)

The data pipeline requires Python 3.10+ with a few packages:

```bash
pip install -r scripts/requirements.txt
```

## Production Deployment

1. Push to the `main` branch on GitHub.
2. Enable GitHub Pages (Settings > Pages > Source: GitHub Actions).
3. Add the `GOOGLE_CREDENTIALS_JSON` repository secret containing the service account JSON for Google Sheets access.
4. The `deploy.yml` workflow builds and deploys on every push to `main`.
5. The `data-refresh.yml` workflow runs daily at 02:00 UTC (06:00 GST) to pull fresh data from Google Sheets, rebuild, and redeploy.

## Data Pipeline

The pipeline script (`scripts/fetch_and_transform.py`) handles the full ETL:

1. **Fetch** -- Reads all rows from the Google Sheet (spreadsheet ID `1ZK7oA_qAwTOdaNhy8vE6Oh7omT6TRAdOI0bXmEtysMg`, sheet "AB Sales.csv") via the Google Sheets API using a service account.
2. **Transform** -- Cleans and normalizes the data:
   - Parses dates to `YYYY-MM-DD`
   - Converts areas from SQM to SQFT
   - Calculates rate per SQFT
   - Normalizes text fields (lowercase, trimmed)
   - Skips rows with missing price or date
3. **Output** -- Writes to `static/data/`:
   - `transactions.parquet` (ZSTD compressed, for fast client-side querying)
   - `transactions.csv` (UTF-8 fallback)
   - `meta.json` (unique filter values, date range, row count)
   - `summary.json` (pre-computed last-12-month stats)

### Local development (no Google credentials needed)

Export the Google Sheet as CSV, then:

```bash
python scripts/fetch_and_transform.py --local-csv ~/Downloads/ab_sales.csv
```

### Manual refresh in CI

Go to Actions > Daily Data Refresh > Run workflow.

## Tech Stack

- **Frontend**: SvelteKit, Tailwind CSS, DuckDB-WASM, Apache ECharts
- **Data pipeline**: Python, gspread, PyArrow
- **Hosting**: GitHub Pages (static)
- **CI/CD**: GitHub Actions (daily data refresh + deploy on push)
- **Data format**: Apache Parquet (ZSTD) queried client-side via DuckDB-WASM

## Project Structure

```
ADInteract/
  .github/workflows/
    data-refresh.yml    # Daily ETL + deploy
    deploy.yml          # Code-only deploy on push
  scripts/
    fetch_and_transform.py
    requirements.txt
  src/                  # SvelteKit application
  static/data/
    transactions.parquet
    transactions.csv
    meta.json
    summary.json
```

## License

Private -- all rights reserved.
