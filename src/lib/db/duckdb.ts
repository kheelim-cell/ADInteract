import * as duckdb from '@duckdb/duckdb-wasm';
import type { AsyncDuckDB, AsyncDuckDBConnection } from '@duckdb/duckdb-wasm';

let db: AsyncDuckDB | null = null;
let conn: AsyncDuckDBConnection | null = null;

export async function initDuckDB(): Promise<AsyncDuckDB> {
	if (db) return db;

	const JSDELIVR_BUNDLES = duckdb.getJsDelivrBundles();
	const bundle = await duckdb.selectBundle(JSDELIVR_BUNDLES);

	const worker_url = URL.createObjectURL(
		new Blob([`importScripts("${bundle.mainWorker!}");`], { type: 'text/javascript' })
	);
	const worker = new Worker(worker_url);
	const logger = new duckdb.ConsoleLogger();
	db = new duckdb.AsyncDuckDB(logger, worker);
	await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
	URL.revokeObjectURL(worker_url);

	return db;
}

export async function getConnection(): Promise<AsyncDuckDBConnection> {
	if (conn) return conn;
	if (!db) throw new Error('DuckDB not initialized');
	conn = await db.connect();
	return conn;
}

export async function loadData(baseUrl: string): Promise<void> {
	if (!db) throw new Error('DuckDB not initialized');

	const parquetUrl = `${baseUrl}/data/transactions.parquet`;
	const csvUrl = `${baseUrl}/data/transactions.csv`;

	const c = await getConnection();

	try {
		const res = await fetch(parquetUrl, { method: 'HEAD' });
		if (res.ok) {
			await db.registerFileURL('transactions.parquet', parquetUrl, duckdb.DuckDBDataProtocol.HTTP, false);
			await c.query(`CREATE OR REPLACE TABLE transactions AS SELECT * FROM read_parquet('transactions.parquet')`);
			return;
		}
	} catch {
		// parquet not available, try CSV
	}

	try {
		const res = await fetch(csvUrl);
		if (res.ok) {
			const csvText = await res.text();
			await db.registerFileText('transactions.csv', csvText);
			await c.query(`
				CREATE OR REPLACE TABLE transactions AS
				SELECT
					CAST(sale_date AS DATE) AS sale_date,
					district,
					community,
					project_name,
					asset_class,
					property_type,
					layout,
					CAST(area_sqft AS DOUBLE) AS area_sqft,
					CAST(land_area_sqft AS DOUBLE) AS land_area_sqft,
					CAST(price_aed AS DOUBLE) AS price_aed,
					CAST(sold_share AS DOUBLE) AS sold_share,
					CAST(rate_per_sqft AS DOUBLE) AS rate_per_sqft,
					sale_type,
					sale_sequence
				FROM read_csv_auto('transactions.csv')
			`);
			return;
		}
	} catch {
		// CSV also not available
	}

	throw new Error('No data file found. Run the data pipeline first.');
}

export async function query<T = Record<string, unknown>>(sql: string): Promise<T[]> {
	const c = await getConnection();
	const result = await c.query(sql);
	return result.toArray().map((row: Record<string, unknown>) => {
		const obj: Record<string, unknown> = {};
		for (const key of Object.keys(row)) {
			const val = row[key];
			obj[key] = typeof val === 'bigint' ? Number(val) : val;
		}
		return obj as T;
	});
}
