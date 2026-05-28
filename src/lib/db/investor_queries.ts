import { query } from './duckdb';

export interface GrowthRow {
	name: string;
	district?: string;
	currentValue: number;
	prevValue: number;
	yoyPct: number;
	txCount?: number;
}

export interface YieldRow {
	community: string;
	district: string;
	medianSalePrice: number;
	medianAnnualRent: number;
	grossYieldPct: number;
	saleCount: number;
	projectCount: number;
}

/** Top N districts by YoY median sale rate/sqft growth (min 10 tx each year) */
export async function queryTopDistrictsByGrowth(
	currentYear: number,
	prevYear: number,
	limit = 5
): Promise<GrowthRow[]> {
	const rows = await query<{
		district: string;
		current_rate: number;
		prev_rate: number;
		yoy_pct: number;
		tx_count: number;
	}>(`
		WITH cur AS (
			SELECT district,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS current_rate,
			       COUNT(*) AS tx_count
			FROM transactions
			WHERE YEAR(sale_date) = ${currentYear}
			  AND rate_per_sqft IS NOT NULL AND rate_per_sqft > 0
			GROUP BY district
			HAVING COUNT(*) >= 10
		),
		prv AS (
			SELECT district,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS prev_rate
			FROM transactions
			WHERE YEAR(sale_date) = ${prevYear}
			  AND rate_per_sqft IS NOT NULL AND rate_per_sqft > 0
			GROUP BY district
			HAVING COUNT(*) >= 10
		)
		SELECT c.district,
		       c.current_rate,
		       p.prev_rate,
		       ROUND(((c.current_rate - p.prev_rate) / p.prev_rate) * 100, 1) AS yoy_pct,
		       c.tx_count
		FROM cur c
		JOIN prv p ON c.district = p.district
		WHERE p.prev_rate > 0
		ORDER BY yoy_pct DESC
		LIMIT ${limit}
	`);

	return rows.map(r => ({
		name: r.district,
		currentValue: r.current_rate,
		prevValue: r.prev_rate,
		yoyPct: r.yoy_pct,
		txCount: r.tx_count,
	}));
}

/** Top N projects by YoY median sale rate/sqft growth (min 5 tx each year) */
export async function queryTopProjectsByGrowth(
	currentYear: number,
	prevYear: number,
	limit = 5
): Promise<GrowthRow[]> {
	const rows = await query<{
		project_name: string;
		district: string;
		current_rate: number;
		prev_rate: number;
		yoy_pct: number;
		tx_count: number;
	}>(`
		WITH cur AS (
			SELECT project_name, district,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS current_rate,
			       COUNT(*) AS tx_count
			FROM transactions
			WHERE YEAR(sale_date) = ${currentYear}
			  AND rate_per_sqft IS NOT NULL AND rate_per_sqft > 0
			  AND project_name IS NOT NULL AND project_name != ''
			GROUP BY project_name, district
			HAVING COUNT(*) >= 5
		),
		prv AS (
			SELECT project_name,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS prev_rate
			FROM transactions
			WHERE YEAR(sale_date) = ${prevYear}
			  AND rate_per_sqft IS NOT NULL AND rate_per_sqft > 0
			  AND project_name IS NOT NULL AND project_name != ''
			GROUP BY project_name
			HAVING COUNT(*) >= 5
		)
		SELECT c.project_name,
		       c.district,
		       c.current_rate,
		       p.prev_rate,
		       ROUND(((c.current_rate - p.prev_rate) / p.prev_rate) * 100, 1) AS yoy_pct,
		       c.tx_count
		FROM cur c
		JOIN prv p ON c.project_name = p.project_name
		WHERE p.prev_rate > 0
		ORDER BY yoy_pct DESC
		LIMIT ${limit}
	`);

	return rows.map(r => ({
		name: r.project_name,
		district: r.district,
		currentValue: r.current_rate,
		prevValue: r.prev_rate,
		yoyPct: r.yoy_pct,
		txCount: r.tx_count,
	}));
}

/** Top N projects by YoY median annual rent growth (uses rental pre-aggregated table) */
export async function queryTopRentalProjectsByGrowth(
	currentYear: number,
	limit = 5
): Promise<GrowthRow[]> {
	const prevYear = currentYear - 1;
	const rows = await query<{
		project_name: string;
		district: string;
		current_rent: number;
		prev_rent: number;
		yoy_pct: number;
	}>(`
		WITH cur AS (
			SELECT project_name, district, median_rent AS current_rent
			FROM rental
			WHERE year = ${currentYear}
			  AND typology = 'All property types'
			  AND layout = 'all beds'
			  AND rent_type = 'All types'
			  AND median_rent > 0
		),
		prv AS (
			SELECT project_name, median_rent AS prev_rent
			FROM rental
			WHERE year = ${prevYear}
			  AND typology = 'All property types'
			  AND layout = 'all beds'
			  AND rent_type = 'All types'
			  AND median_rent > 0
		)
		SELECT c.project_name,
		       c.district,
		       c.current_rent,
		       p.prev_rent,
		       ROUND(((c.current_rent - p.prev_rent) / p.prev_rent) * 100, 1) AS yoy_pct
		FROM cur c
		JOIN prv p ON c.project_name = p.project_name
		WHERE p.prev_rent > 0
		ORDER BY yoy_pct DESC
		LIMIT ${limit}
	`);

	return rows.map(r => ({
		name: r.project_name,
		district: r.district,
		currentValue: r.current_rent,
		prevValue: r.prev_rent,
		yoyPct: r.yoy_pct,
	}));
}

/**
 * Gross rental yield by community.
 * yield = median annual rent (rental table) / median sale price (transactions) × 100
 * Requires communities present in both datasets.
 */
export async function queryRentalYieldByCommunity(
	salesYear: number,
	rentalYear: number,
	minSaleCount = 5
): Promise<YieldRow[]> {
	const rows = await query<{
		community: string;
		district: string;
		median_sale_price: number;
		median_annual_rent: number;
		gross_yield_pct: number;
		sale_count: number;
		project_count: number;
	}>(`
		WITH sales AS (
			SELECT community, district,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_aed) AS median_sale_price,
			       COUNT(*) AS sale_count
			FROM transactions
			WHERE YEAR(sale_date) = ${salesYear}
			  AND price_aed IS NOT NULL AND price_aed > 0
			  AND community IS NOT NULL AND community != ''
			GROUP BY community, district
			HAVING COUNT(*) >= ${minSaleCount}
		),
		rents AS (
			SELECT community,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS median_annual_rent,
			       COUNT(DISTINCT project_name) AS project_count
			FROM rental
			WHERE year = ${rentalYear}
			  AND typology = 'All property types'
			  AND layout = 'all beds'
			  AND rent_type = 'All types'
			  AND median_rent > 0
			  AND community IS NOT NULL AND community != ''
			GROUP BY community
		)
		SELECT s.community,
		       s.district,
		       s.median_sale_price,
		       r.median_annual_rent,
		       ROUND((r.median_annual_rent / s.median_sale_price) * 100, 2) AS gross_yield_pct,
		       s.sale_count,
		       r.project_count
		FROM sales s
		JOIN rents r ON s.community = r.community
		WHERE s.median_sale_price > 0
		ORDER BY gross_yield_pct DESC
	`);

	return rows;
}
