import { query } from './duckdb';
import type {
	RentalFilterState,
	RentalStatsResult,
	RentalLayoutRow,
	RentalTrendPoint,
	RentalDistrictRow,
	RentalProjectRow,
	NewVsRenewRow,
	PriceToRentRow
} from './rental_types';

// ─── Helpers ────────────────────────────────────────────────────────────────

function esc(s: string): string {
	return s.replace(/'/g, "''");
}

/**
 * Build a WHERE clause for the rental table.
 * `yearOverride` lets trend queries pin to a specific year while ignoring
 * the filter's year field (they iterate all years themselves).
 * `forProjectTable` — when true, fetches real per-typology rows
 * (Apartment / Villa / Townhouse) instead of the "All property types"
 * aggregate sentinel, so the project table shows actual property types.
 */
function buildRentalWhere(
	f: RentalFilterState,
	latestYear: number,
	yearOverride?: number | null,
	forProjectTable = false
): string {
	const clauses: string[] = [];

	const resolvedYear = yearOverride !== undefined
		? yearOverride
		: (f.year ?? latestYear);

	if (resolvedYear !== null) {
		clauses.push(`year = ${resolvedYear}`);
	}

	// Typology filtering
	if (f.typology && f.typology !== 'All property types') {
		// Specific typology selected — always filter to it
		clauses.push(`typology = '${esc(f.typology)}'`);
	} else if (forProjectTable) {
		// Project table: show real property types, not the aggregate sentinel
		clauses.push(`typology != 'All property types'`);
	} else {
		// Stats / charts: use aggregate rows to avoid double-counting
		clauses.push(`typology = 'All property types'`);
	}

	if (f.layout && f.layout !== 'all beds') {
		clauses.push(`layout = '${esc(f.layout)}'`);
	} else {
		clauses.push(`layout = 'all beds'`);
	}

	if (f.rentType && f.rentType !== 'All types') {
		clauses.push(`rent_type = '${esc(f.rentType)}'`);
	} else {
		clauses.push(`rent_type = 'All types'`);
	}

	if (f.district) clauses.push(`district = '${esc(f.district)}'`);
	if (f.community) clauses.push(`community = '${esc(f.community)}'`);
	if (f.project) clauses.push(`project_name = '${esc(f.project)}'`);

	return clauses.length > 0 ? clauses.join(' AND ') : '1=1';
}

// ─── Stats ───────────────────────────────────────────────────────────────────

export async function queryRentalStats(
	f: RentalFilterState,
	latestYear: number
): Promise<RentalStatsResult> {
	const resolvedYear = f.year ?? latestYear;
	const prevYear     = resolvedYear - 1;
	const where        = buildRentalWhere(f, latestYear);
	const prevWhere    = buildRentalWhere(f, latestYear, prevYear);

	type StatsRow = { project_count: number; median_rent: number; lower_rent: number; upper_rent: number };

	const statsSQL = (w: string) => `
		SELECT
			COUNT(DISTINCT project_name) AS project_count,
			PERCENTILE_CONT(0.5)  WITHIN GROUP (ORDER BY median_rent) AS median_rent,
			PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY median_rent) AS lower_rent,
			PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY median_rent) AS upper_rent
		FROM rental
		WHERE ${w}
	`;

	const [[row], [prevRow]] = await Promise.all([
		query<StatsRow>(statsSQL(where)),
		query<StatsRow>(statsSQL(prevWhere))
	]);

	return {
		projectCount:   row?.project_count ?? 0,
		medianRent:     row?.median_rent   ?? 0,
		lowerRent:      row?.lower_rent    ?? 0,
		upperRent:      row?.upper_rent    ?? 0,
		prevMedianRent: prevRow?.median_rent ?? null,
		prevLowerRent:  prevRow?.lower_rent  ?? null,
		prevUpperRent:  prevRow?.upper_rent  ?? null,
		resolvedYear,
		prevYear
	};
}

// ─── Layout breakdown ────────────────────────────────────────────────────────

/**
 * Per-layout summary: always shows every bed size so the chart is a full
 * comparison. Respects typology, year, district, community, and rent_type.
 * Ignores f.layout (filtering to one bed size would leave a single bar).
 */
export async function queryRentalByLayout(
	f: RentalFilterState,
	latestYear: number
): Promise<RentalLayoutRow[]> {
	const resolvedYear = f.year ?? latestYear;
	const typologyClause = (f.typology && f.typology !== 'All property types')
		? `typology = '${esc(f.typology)}'`
		: `typology = 'All property types'`;

	const clauses: string[] = [
		`year = ${resolvedYear}`,
		typologyClause,
		`layout != 'all beds'`,
		`rent_type = '${esc(f.rentType || 'All types')}'`
	];
	if (f.district)  clauses.push(`district  = '${esc(f.district)}'`);
	if (f.community) clauses.push(`community = '${esc(f.community)}'`);

	const where = clauses.join(' AND ');

	return query<RentalLayoutRow>(`
		SELECT
			layout,
			COUNT(DISTINCT project_name)                                              AS projectCount,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY lower_rent)  FILTER (WHERE lower_rent  IS NOT NULL) AS lowerRent,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent)                                        AS medianRent,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY upper_rent)  FILTER (WHERE upper_rent  IS NOT NULL) AS upperRent
		FROM rental
		WHERE ${where}
		GROUP BY layout
		ORDER BY
			CASE layout
				WHEN 'studio'  THEN 0
				WHEN '1 bed'   THEN 1
				WHEN '2 beds'  THEN 2
				WHEN '3 beds'  THEN 3
				WHEN '4 beds'  THEN 4
				WHEN '5 beds'  THEN 5
				ELSE 99
			END
	`);
}

// ─── Year-on-year trend ──────────────────────────────────────────────────────

export async function queryRentalTrend(
	f: RentalFilterState,
	latestYear: number
): Promise<RentalTrendPoint[]> {
	// Respect selected layout and typology; fall back to aggregate rows
	const layoutClause = (f.layout && f.layout !== 'all beds')
		? `layout = '${esc(f.layout)}'`
		: `layout = 'all beds'`;
	const typologyClause = (f.typology && f.typology !== 'All property types')
		? `typology = '${esc(f.typology)}'`
		: `typology = 'All property types'`;

	const clauses: string[] = [
		typologyClause,
		layoutClause,
		`rent_type = '${esc(f.rentType || 'All types')}'`
	];
	if (f.district)  clauses.push(`district  = '${esc(f.district)}'`);
	if (f.community) clauses.push(`community = '${esc(f.community)}'`);
	if (f.project)   clauses.push(`project_name = '${esc(f.project)}'`);

	const where = clauses.join(' AND ');

	return query<RentalTrendPoint>(`
		SELECT
			year,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS medianRent,
			COUNT(DISTINCT project_name)                              AS projectCount
		FROM rental
		WHERE ${where}
		GROUP BY year
		ORDER BY year
	`);
}

// ─── Top districts ───────────────────────────────────────────────────────────

export async function queryTopRentalDistricts(
	f: RentalFilterState,
	latestYear: number,
	limit = 10
): Promise<RentalDistrictRow[]> {
	const resolvedYear = f.year ?? latestYear;

	const clauses: string[] = [
		`year = ${resolvedYear}`,
		`typology = 'All property types'`,
		`layout   = 'all beds'`,
		`rent_type = '${esc(f.rentType || 'All types')}'`
	];
	if (f.community) clauses.push(`community = '${esc(f.community)}'`);

	const where = clauses.join(' AND ');

	return query<RentalDistrictRow>(`
		SELECT
			district,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS medianRent,
			COUNT(DISTINCT project_name)                              AS projectCount
		FROM rental
		WHERE ${where}
		GROUP BY district
		ORDER BY medianRent DESC
		LIMIT ${limit}
	`);
}

// ─── Project list ─────────────────────────────────────────────────────────────

export async function queryRentalProjects(
	f: RentalFilterState,
	latestYear: number,
	sortCol = 'median_rent',
	sortDir: 'asc' | 'desc' = 'desc',
	page = 1,
	pageSize = 50
): Promise<{ rows: RentalProjectRow[]; total: number }> {
	const resolvedYear = f.year ?? latestYear;
	const prevYear = resolvedYear - 1;

	// Use forProjectTable=true so we get real typologies (Apartment/Villa)
	// instead of the "All property types" aggregate sentinel
	const where = buildRentalWhere(f, latestYear, undefined, true);

	// Previous-year WHERE — same typology logic for like-for-like YoY
	const prevClauses: string[] = [
		`year = ${prevYear}`,
		f.typology && f.typology !== 'All property types'
			? `typology = '${esc(f.typology)}'`
			: `typology != 'All property types'`,
		`layout   = '${esc(f.layout   || 'all beds')}'`,
		`rent_type = '${esc(f.rentType || 'All types')}'`
	];
	if (f.district)  prevClauses.push(`district  = '${esc(f.district)}'`);
	if (f.community) prevClauses.push(`community = '${esc(f.community)}'`);

	const prevWhere = prevClauses.join(' AND ');

	const SAFE_COLS: Record<string, string> = {
		project_name: 'project_name',
		district:     'district',
		median_rent:  'median_rent',
		lower_rent:   'lower_rent',
		upper_rent:   'upper_rent',
		yoy_change:   'yoy_change'
	};
	const orderByCol = SAFE_COLS[sortCol] ?? 'median_rent';
	const direction  = sortDir === 'asc' ? 'ASC' : 'DESC';
	const offset = (page - 1) * pageSize;

	const [countRow] = await query<{ total: number }>(`
		SELECT COUNT(*) AS total
		FROM (
			SELECT project_name, district, community, typology, layout
			FROM rental
			WHERE ${where}
			GROUP BY project_name, district, community, typology, layout
		)
	`);
	const total = countRow?.total ?? 0;

	const rows = await query<RentalProjectRow>(`
		WITH current AS (
			SELECT
				project_name,
				district,
				community,
				typology,
				layout,
				PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY lower_rent)  AS lower_rent,
				PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS median_rent,
				PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY upper_rent)  AS upper_rent
			FROM rental
			WHERE ${where}
			GROUP BY project_name, district, community, typology, layout
		),
		prev AS (
			SELECT
				project_name,
				typology,
				PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS prev_median
			FROM rental
			WHERE ${prevWhere}
			GROUP BY project_name, typology
		)
		SELECT
			c.project_name,
			c.district,
			c.community,
			c.typology,
			c.layout,
			c.lower_rent,
			c.median_rent,
			c.upper_rent,
			p.prev_median AS prev_median_rent,
			CASE
				WHEN p.prev_median IS NOT NULL AND p.prev_median > 0
				THEN ROUND(((c.median_rent - p.prev_median) / p.prev_median) * 100, 1)
				ELSE NULL
			END AS yoy_change
		FROM current c
		LEFT JOIN prev p ON c.project_name = p.project_name AND c.typology = p.typology
		ORDER BY ${orderByCol} ${direction} NULLS LAST
		LIMIT ${pageSize} OFFSET ${offset}
	`);

	return { rows, total };
}

// ─── New vs Renewal rent gap ─────────────────────────────────────────────────

export async function queryRentalNewVsRenew(
	f: RentalFilterState,
	latestYear: number
): Promise<NewVsRenewRow[]> {
	const resolvedYear = f.year ?? latestYear;
	const typologyClause = (f.typology && f.typology !== 'All property types')
		? `typology = '${esc(f.typology)}'`
		: `typology = 'All property types'`;

	const clauses: string[] = [
		`year = ${resolvedYear}`,
		typologyClause,
		`layout IN ('studio', '1 bed', '2 beds', '3 beds')`,
		`rent_type IN ('New', 'Renew')`
	];
	if (f.district)  clauses.push(`district      = '${esc(f.district)}'`);
	if (f.community) clauses.push(`community     = '${esc(f.community)}'`);
	if (f.project)   clauses.push(`project_name  = '${esc(f.project)}'`);

	const where = clauses.join(' AND ');

	const rows = await query<{ layout: string; newRent: number | null; renewRent: number | null }>(`
		SELECT
			layout,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent)
				FILTER (WHERE rent_type = 'New')   AS newRent,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent)
				FILTER (WHERE rent_type = 'Renew') AS renewRent
		FROM rental
		WHERE ${where}
		GROUP BY layout
		ORDER BY
			CASE layout
				WHEN 'studio'  THEN 0
				WHEN '1 bed'   THEN 1
				WHEN '2 beds'  THEN 2
				WHEN '3 beds'  THEN 3
				WHEN '4 beds'  THEN 4
				WHEN '5 beds'  THEN 5
				WHEN '6 beds'  THEN 6
				ELSE 99
			END
	`);

	return rows
		.filter((r) => r.newRent !== null || r.renewRent !== null)
		.map((r) => ({
			layout:    r.layout,
			newRent:   r.newRent,
			renewRent: r.renewRent,
			gapPct:
				r.newRent !== null && r.renewRent !== null && r.renewRent > 0
					? Math.round(((r.newRent - r.renewRent) / r.renewRent) * 1000) / 10
					: null
		}));
}

/** Distinct project count per district (latest year) — used to show data richness in dropdowns */
export async function queryAllRentalDistrictCounts(latestYear: number): Promise<Record<string, number>> {
	const rows = await query<{ district: string; cnt: number }>(`
		SELECT district, COUNT(DISTINCT project_name) AS cnt
		FROM rental
		WHERE year = ${latestYear}
			AND district IS NOT NULL AND district != ''
			AND typology = 'All property types'
		GROUP BY district
	`);
	const counts: Record<string, number> = {};
	for (const row of rows) {
		counts[row.district] = Number(row.cnt);
	}
	return counts;
}

// ─── Price-to-Rent yield (cross-table) ────────────────────────────────────────

export async function queryPriceToRent(
	f: RentalFilterState,
	latestYear: number,
	limit = 15
): Promise<PriceToRentRow[]> {
	const resolvedYear = f.year ?? latestYear;
	const typologyClause = (f.typology && f.typology !== 'All property types')
		? `r.typology = '${esc(f.typology)}'`
		: `r.typology = 'All property types'`;

	const districtClause = f.district ? `r.district = '${esc(f.district)}'` : '1=1';

	return query<PriceToRentRow>(`
		WITH rental_agg AS (
			SELECT
				district,
				PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS median_rent
			FROM rental r
			WHERE r.year = ${resolvedYear}
				AND ${typologyClause}
				AND r.layout    = 'all beds'
				AND r.rent_type = 'All types'
				AND r.median_rent > 0
				AND ${districtClause}
			GROUP BY district
		),
		tx_agg AS (
			SELECT
				district,
				PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_aed) AS median_price
			FROM transactions
			WHERE sale_date >= (CURRENT_DATE - INTERVAL '24 months')
				AND property_type IN (
					'apartment', 'duplex',
					'townhouse / attached villa', 'villa'
				)
				AND price_aed  > 100000
				AND area_sqft  > 0
			GROUP BY district
		)
		SELECT
			r.district,
			ROUND(t.median_price, 0)                              AS medianSalePrice,
			ROUND(r.median_rent,  0)                              AS medianAnnualRent,
			ROUND(r.median_rent / t.median_price * 100, 2)        AS grossYieldPct,
			ROUND(t.median_price / r.median_rent, 1)              AS priceToRentYears
		FROM rental_agg r
		JOIN tx_agg t ON LOWER(TRIM(r.district)) = LOWER(TRIM(t.district))
		WHERE t.median_price > 0 AND r.median_rent > 0
		ORDER BY grossYieldPct DESC
		LIMIT ${limit}
	`);
}

// ─── Rental Market Activity (occupancy proxy) ─────────────────────────────────

export interface RentalActivityRow {
	district: string;
	new_count: number;
	renewal_count: number;
	total_count: number;
	new_pct: number;
	renewal_pct: number;
}

/**
 * Per-district breakdown of new vs renewal contracts.
 * Lower new_pct signals stronger occupancy (more tenants renewing vs vacating).
 */
export async function queryRentalActivity(latestYear: number, district?: string): Promise<RentalActivityRow[]> {
	const districtClause = district ? `AND district = '${esc(district)}'` : '';
	const rows = await query<{
		district: string;
		new_count: number;
		renewal_count: number;
		total_count: number;
	}>(`
		SELECT
			district,
			SUM(CASE WHEN rent_type = 'New' THEN cnt ELSE 0 END)    AS new_count,
			SUM(CASE WHEN rent_type = 'Renew' THEN cnt ELSE 0 END)  AS renewal_count,
			SUM(cnt)                                                  AS total_count
		FROM (
			SELECT district, rent_type, COUNT(*) AS cnt
			FROM rental
			WHERE year = ${latestYear}
			  AND typology = 'All property types'
			  AND layout = 'all beds'
			  AND rent_type IN ('New', 'Renew')
			  AND district IS NOT NULL AND district != ''
			  ${districtClause}
			GROUP BY district, rent_type
		)
		GROUP BY district
		HAVING SUM(cnt) >= 3
		ORDER BY new_count DESC
		LIMIT 20
	`);

	return rows.map(r => {
		const total = Number(r.total_count) || 1;
		return {
			district: r.district,
			new_count: Number(r.new_count),
			renewal_count: Number(r.renewal_count),
			total_count: total,
			new_pct: Math.round((Number(r.new_count) / total) * 100),
			renewal_pct: Math.round((Number(r.renewal_count) / total) * 100),
		};
	});
}
