import { query } from './duckdb';
import type {
	FilterState,
	StatsResult,
	ChartDataPoint,
	DistrictSummary,
	PriceDistributionPoint,
	Transaction,
	ProjectInfo,
	LayoutSummaryRow,
	ComparableProject
} from './types';

// Only these 6 property types are shown across the entire platform
const ALLOWED_PROPERTY_TYPES = [
	'apartment',
	'duplex',
	'townhouse / attached villa',
	'villa',
	'office',
	'retail'
];
const PROPERTY_TYPE_FILTER = `property_type IN (${ALLOWED_PROPERTY_TYPES.map((t) => `'${t}'`).join(', ')})`;

function buildWhere(f: FilterState, dateStart: string, dateEnd: string): string {
	const clauses: string[] = [];
	clauses.push(`sale_date >= '${dateStart}'`);
	clauses.push(`sale_date <= '${dateEnd}'`);
	clauses.push(PROPERTY_TYPE_FILTER);
	if (f.district) clauses.push(`district = '${esc(f.district)}'`);
	if (f.project) clauses.push(`project_name = '${esc(f.project)}'`);
	if (f.saleType === 'off-plan') clauses.push(`sale_type = 'off-plan'`);
	if (f.saleType === 'ready') clauses.push(`sale_type = 'ready'`);
	if (f.saleSequence === 'primary') clauses.push(`sale_sequence = 'primary'`);
	if (f.saleSequence === 'secondary') clauses.push(`sale_sequence = 'secondary'`);
	if (f.propertyTypes.length > 0) {
		clauses.push(`property_type IN (${f.propertyTypes.map((t) => `'${esc(t)}'`).join(',')})`);
	}
	if (f.layouts.length > 0) {
		clauses.push(`layout IN (${f.layouts.map((l) => `'${esc(l)}'`).join(',')})`);
	}
	if (f.areaSqftMin != null) clauses.push(`area_sqft >= ${f.areaSqftMin}`);
	if (f.areaSqftMax != null) clauses.push(`area_sqft <= ${f.areaSqftMax}`);
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
	// Tukey IQR method: whiskers capped at Q1 − 1.5×IQR and Q3 + 1.5×IQR
	// so individual outliers don't collapse the visible box
	return query<PriceDistributionPoint>(`
		WITH base AS (
			SELECT layout, rate_per_sqft
			FROM transactions
			WHERE ${where}
				AND rate_per_sqft IS NOT NULL AND rate_per_sqft > 0
				AND layout != 'unclassified'
		),
		pcts AS (
			SELECT
				layout,
				COUNT(*) AS count,
				PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY rate_per_sqft) AS q1,
				PERCENTILE_CONT(0.5)  WITHIN GROUP (ORDER BY rate_per_sqft) AS median,
				PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY rate_per_sqft) AS q3
			FROM base
			GROUP BY layout
			HAVING COUNT(*) >= 5
		)
		SELECT
			p.layout,
			GREATEST(MIN(b.rate_per_sqft), p.q1 - 1.5 * (p.q3 - p.q1)) AS min,
			p.q1,
			p.median,
			p.q3,
			LEAST(MAX(b.rate_per_sqft),   p.q3 + 1.5 * (p.q3 - p.q1)) AS max,
			p.count
		FROM pcts p
		JOIN base b ON b.layout = p.layout
			AND b.rate_per_sqft >= p.q1 - 1.5 * (p.q3 - p.q1)
			AND b.rate_per_sqft <= p.q3 + 1.5 * (p.q3 - p.q1)
		GROUP BY p.layout, p.q1, p.median, p.q3, p.count
		ORDER BY
			CASE p.layout
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

export async function exportTransactions(
	f: FilterState,
	dateStart: string,
	dateEnd: string
): Promise<Transaction[]> {
	const where = buildWhere(f, dateStart, dateEnd);
	const orderCol = f.sortColumn || 'sale_date';
	const orderDir = f.sortDirection || 'desc';
	return query<Transaction>(`
		SELECT
			CAST(sale_date AS VARCHAR) AS sale_date,
			district,
			community,
			project_name,
			property_type,
			layout,
			ROUND(area_sqft, 0) AS area_sqft,
			price_aed,
			ROUND(rate_per_sqft, 0) AS rate_per_sqft,
			sale_type,
			sale_sequence
		FROM transactions
		WHERE ${where}
		ORDER BY ${orderCol} ${orderDir}
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

export async function queryProjectInfo(
	projectName: string,
	dateStart: string,
	dateEnd: string
): Promise<ProjectInfo | null> {
	const escapedProject = esc(projectName);

	// Main stats + district benchmark in one CTE query
	const rows = await query<{
		district: string;
		community: string;
		total_count: number;
		off_plan_count: number;
		ready_count: number;
		first_sale: string;
		last_sale: string;
		project_median_rate: number;
		district_median_rate: number;
	}>(`
		WITH project_data AS (
			SELECT
				district,
				ANY_VALUE(community) AS community,
				COUNT(*) AS total_count,
				COUNT(*) FILTER (WHERE sale_type = 'off-plan') AS off_plan_count,
				COUNT(*) FILTER (WHERE sale_type = 'ready') AS ready_count,
				CAST(MIN(sale_date) AS VARCHAR) AS first_sale,
				CAST(MAX(sale_date) AS VARCHAR) AS last_sale,
				PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft)
					FILTER (WHERE rate_per_sqft IS NOT NULL AND rate_per_sqft > 0) AS project_median_rate
			FROM transactions
			WHERE project_name = '${escapedProject}'
				AND sale_date >= '${dateStart}' AND sale_date <= '${dateEnd}'
				AND ${PROPERTY_TYPE_FILTER}
			GROUP BY district
			ORDER BY COUNT(*) DESC
			LIMIT 1
		),
		district_data AS (
			SELECT
				PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY t.rate_per_sqft)
					FILTER (WHERE t.rate_per_sqft IS NOT NULL AND t.rate_per_sqft > 0) AS district_median_rate
			FROM transactions t
			CROSS JOIN project_data pd
			WHERE t.district = pd.district
				AND t.sale_date >= '${dateStart}' AND t.sale_date <= '${dateEnd}'
		)
		SELECT pd.*, dd.district_median_rate
		FROM project_data pd CROSS JOIN district_data dd
	`);

	if (!rows.length) return null;
	const row = rows[0];

	// Distinct property types (within allowed set)
	const typeRows = await query<{ property_type: string }>(`
		SELECT DISTINCT property_type
		FROM transactions
		WHERE project_name = '${escapedProject}'
			AND sale_date >= '${dateStart}' AND sale_date <= '${dateEnd}'
			AND property_type IS NOT NULL AND property_type != ''
			AND ${PROPERTY_TYPE_FILTER}
		ORDER BY property_type
	`);

	// Distinct layouts in bedroom order
	const layoutRows = await query<{ layout: string }>(`
		SELECT DISTINCT layout
		FROM transactions
		WHERE project_name = '${escapedProject}'
			AND sale_date >= '${dateStart}' AND sale_date <= '${dateEnd}'
			AND layout IS NOT NULL AND layout != '' AND layout != 'unclassified'
		ORDER BY CASE layout
			WHEN 'studio' THEN 1 WHEN '1 bed' THEN 2 WHEN '2 beds' THEN 3
			WHEN '3 beds' THEN 4 WHEN '4 beds' THEN 5 WHEN '5 beds' THEN 6
			WHEN '6+ beds' THEN 7 ELSE 8
		END
	`);

	return {
		district: row.district,
		community: row.community,
		propertyTypes: typeRows.map((r) => r.property_type),
		layouts: layoutRows.map((r) => r.layout),
		firstSale: row.first_sale,
		lastSale: row.last_sale,
		totalCount: row.total_count,
		offPlanCount: row.off_plan_count,
		readyCount: row.ready_count,
		projectMedianRate: row.project_median_rate,
		districtMedianRate: row.district_median_rate
	};
}

export async function queryLayoutSummary(
	f: FilterState,
	dateStart: string,
	dateEnd: string
): Promise<LayoutSummaryRow[]> {
	const where = buildWhere(f, dateStart, dateEnd);
	return query<LayoutSummaryRow>(`
		SELECT
			layout,
			COUNT(*) AS count,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_aed) AS "medianPrice",
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft)
				FILTER (WHERE rate_per_sqft IS NOT NULL AND rate_per_sqft > 0) AS "medianRate"
		FROM transactions
		WHERE ${where}
			AND layout IS NOT NULL AND layout != '' AND layout != 'unclassified'
		GROUP BY layout
		HAVING COUNT(*) >= 2
		ORDER BY CASE layout
			WHEN 'studio' THEN 1 WHEN '1 bed' THEN 2 WHEN '2 beds' THEN 3
			WHEN '3 beds' THEN 4 WHEN '4 beds' THEN 5 WHEN '5 beds' THEN 6
			WHEN '6+ beds' THEN 7 ELSE 8
		END
	`);
}

/** All-time transaction count per district — used to show data richness in dropdowns */
export async function queryAllDistrictCounts(): Promise<Record<string, number>> {
	const rows = await query<{ district: string; cnt: number }>(`
		SELECT district, COUNT(*) AS cnt
		FROM transactions
		WHERE district IS NOT NULL AND district != ''
			AND ${PROPERTY_TYPE_FILTER}
		GROUP BY district
	`);
	const counts: Record<string, number> = {};
	for (const row of rows) {
		counts[row.district] = Number(row.cnt);
	}
	return counts;
}

export async function queryComparableProjects(
	projectName: string,
	dateStart: string,
	dateEnd: string,
	limit = 5
): Promise<ComparableProject[]> {
	const escapedProject = esc(projectName);
	return query<ComparableProject>(`
		WITH target AS (
			SELECT
				district,
				PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft)
					FILTER (WHERE rate_per_sqft IS NOT NULL AND rate_per_sqft > 0) AS target_rate
			FROM transactions
			WHERE project_name = '${escapedProject}'
				AND sale_date >= '${dateStart}' AND sale_date <= '${dateEnd}'
				AND ${PROPERTY_TYPE_FILTER}
			GROUP BY district
			ORDER BY COUNT(*) DESC
			LIMIT 1
		)
		SELECT
			t.project_name,
			t.district,
			COUNT(*) AS volume,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY t.rate_per_sqft)
				FILTER (WHERE t.rate_per_sqft IS NOT NULL AND t.rate_per_sqft > 0) AS "medianRate",
			(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY t.rate_per_sqft)
				FILTER (WHERE t.rate_per_sqft IS NOT NULL AND t.rate_per_sqft > 0) - tgt.target_rate)
				/ tgt.target_rate AS "rateDiff"
		FROM transactions t
		CROSS JOIN target tgt
		WHERE t.district = tgt.district
			AND t.project_name != '${escapedProject}'
			AND t.project_name IS NOT NULL AND t.project_name != ''
			AND t.sale_date >= '${dateStart}' AND t.sale_date <= '${dateEnd}'
			AND ${PROPERTY_TYPE_FILTER}
		GROUP BY t.project_name, t.district, tgt.target_rate
		HAVING COUNT(*) >= 3
		ORDER BY ABS("rateDiff") ASC
		LIMIT ${limit}
	`);
}
