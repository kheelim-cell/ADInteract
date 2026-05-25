import { query } from './duckdb';
import type {
	FilterState,
	StatsResult,
	ChartDataPoint,
	DistrictSummary,
	PriceDistributionPoint,
	Transaction
} from './types';

function buildWhere(f: FilterState, dateStart: string, dateEnd: string): string {
	const clauses: string[] = [];
	clauses.push(`sale_date >= '${dateStart}'`);
	clauses.push(`sale_date <= '${dateEnd}'`);
	if (f.district) clauses.push(`district = '${esc(f.district)}'`);
	if (f.project) clauses.push(`project_name = '${esc(f.project)}'`);
	if (f.saleType === 'off-plan') clauses.push(`sale_type = 'off-plan'`);
	if (f.saleType === 'ready') clauses.push(`sale_type = 'ready'`);
	if (f.propertyTypes.length > 0) {
		clauses.push(`property_type IN (${f.propertyTypes.map((t) => `'${esc(t)}'`).join(',')})`);
	}
	if (f.layouts.length > 0) {
		clauses.push(`layout IN (${f.layouts.map((l) => `'${esc(l)}'`).join(',')})`);
	}
	return clauses.join(' AND ');
}

function esc(s: string): string {
	return s.replace(/'/g, "''");
}

export async function queryStats(
	f: FilterState,
	dateStart: string,
	dateEnd: string,
	prevStart: string,
	prevEnd: string
): Promise<StatsResult> {
	const where = buildWhere(f, dateStart, dateEnd);
	const prevWhere = buildWhere(f, prevStart, prevEnd);

	const [current] = await query<{
		total_volume: number;
		median_price: number;
		median_rate: number;
		total_value: number;
	}>(`
		SELECT
			COUNT(*) AS total_volume,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_aed) AS median_price,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) FILTER (WHERE rate_per_sqft IS NOT NULL AND rate_per_sqft > 0) AS median_rate,
			SUM(price_aed) AS total_value
		FROM transactions
		WHERE ${where}
	`);

	const [prev] = await query<{
		total_volume: number;
		median_price: number;
		median_rate: number;
		total_value: number;
	}>(`
		SELECT
			COUNT(*) AS total_volume,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_aed) AS median_price,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) FILTER (WHERE rate_per_sqft IS NOT NULL AND rate_per_sqft > 0) AS median_rate,
			SUM(price_aed) AS total_value
		FROM transactions
		WHERE ${prevWhere}
	`);

	return {
		totalVolume: current?.total_volume ?? 0,
		medianPrice: current?.median_price ?? 0,
		medianRatePerSqft: current?.median_rate ?? 0,
		totalValue: current?.total_value ?? 0,
		prevTotalVolume: prev?.total_volume ?? 0,
		prevMedianPrice: prev?.median_price ?? 0,
		prevMedianRatePerSqft: prev?.median_rate ?? 0,
		prevTotalValue: prev?.total_value ?? 0
	};
}

export async function queryChartData(
	f: FilterState,
	dateStart: string,
	dateEnd: string
): Promise<ChartDataPoint[]> {
	const where = buildWhere(f, dateStart, dateEnd);
	return query<ChartDataPoint>(`
		SELECT
			STRFTIME(DATE_TRUNC('month', sale_date), '%Y-%m') AS month,
			COUNT(*) AS volume,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_aed) AS "medianPrice",
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) FILTER (WHERE rate_per_sqft IS NOT NULL AND rate_per_sqft > 0) AS "medianRate",
			COUNT(*) FILTER (WHERE sale_type = 'off-plan') AS "offPlanVolume",
			COUNT(*) FILTER (WHERE sale_type = 'ready') AS "readyVolume"
		FROM transactions
		WHERE ${where}
		GROUP BY DATE_TRUNC('month', sale_date)
		ORDER BY DATE_TRUNC('month', sale_date)
	`);
}

export async function queryTopProjects(
	f: FilterState,
	dateStart: string,
	dateEnd: string,
	limit = 10
): Promise<DistrictSummary[]> {
	const where = buildWhere(f, dateStart, dateEnd);
	return query<DistrictSummary>(`
		SELECT
			project_name AS district,
			COUNT(*) AS volume,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_aed) AS "medianPrice",
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) FILTER (WHERE rate_per_sqft IS NOT NULL AND rate_per_sqft > 0) AS "medianRate"
		FROM transactions
		WHERE ${where} AND project_name IS NOT NULL AND project_name != ''
		GROUP BY project_name
		ORDER BY COUNT(*) DESC
		LIMIT ${limit}
	`);
}

export async function queryTopDistricts(
	f: FilterState,
	dateStart: string,
	dateEnd: string,
	limit = 10
): Promise<DistrictSummary[]> {
	const where = buildWhere(f, dateStart, dateEnd);
	return query<DistrictSummary>(`
		SELECT
			district,
			COUNT(*) AS volume,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_aed) AS "medianPrice",
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) FILTER (WHERE rate_per_sqft IS NOT NULL AND rate_per_sqft > 0) AS "medianRate"
		FROM transactions
		WHERE ${where}
		GROUP BY district
		ORDER BY COUNT(*) DESC
		LIMIT ${limit}
	`);
}

export async function queryPriceDistribution(
	f: FilterState,
	dateStart: string,
	dateEnd: string
): Promise<PriceDistributionPoint[]> {
	const where = buildWhere(f, dateStart, dateEnd);
	return query<PriceDistributionPoint>(`
		SELECT
			layout,
			MIN(rate_per_sqft) AS min,
			PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY rate_per_sqft) AS q1,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS median,
			PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY rate_per_sqft) AS q3,
			MAX(rate_per_sqft) AS max,
			COUNT(*) AS count
		FROM transactions
		WHERE ${where} AND rate_per_sqft IS NOT NULL AND rate_per_sqft > 0
			AND layout != 'unclassified'
		GROUP BY layout
		HAVING COUNT(*) >= 5
		ORDER BY
			CASE layout
				WHEN 'studio' THEN 1
				WHEN '1 bed' THEN 2
				WHEN '2 beds' THEN 3
				WHEN '3 beds' THEN 4
				WHEN '4 beds' THEN 5
				WHEN '5 beds' THEN 6
				WHEN '6+ beds' THEN 7
				ELSE 8
			END
	`);
}

export async function queryTransactions(
	f: FilterState,
	dateStart: string,
	dateEnd: string
): Promise<Transaction[]> {
	const where = buildWhere(f, dateStart, dateEnd);
	const orderCol = f.sortColumn || 'sale_date';
	const orderDir = f.sortDirection || 'desc';
	const offset = (f.page - 1) * f.pageSize;
	return query<Transaction>(`
		SELECT
			CAST(sale_date AS VARCHAR) AS sale_date,
			district,
			community,
			project_name,
			asset_class,
			property_type,
			layout,
			area_sqft,
			land_area_sqft,
			price_aed,
			sold_share,
			rate_per_sqft,
			sale_type,
			sale_sequence
		FROM transactions
		WHERE ${where}
		ORDER BY ${orderCol} ${orderDir}
		LIMIT ${f.pageSize}
		OFFSET ${offset}
	`);
}

export async function queryTransactionCount(
	f: FilterState,
	dateStart: string,
	dateEnd: string
): Promise<number> {
	const where = buildWhere(f, dateStart, dateEnd);
	const [result] = await query<{ cnt: number }>(`
		SELECT COUNT(*) AS cnt FROM transactions WHERE ${where}
	`);
	return result?.cnt ?? 0;
}
