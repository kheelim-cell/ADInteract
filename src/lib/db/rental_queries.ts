import { query } from './duckdb';
import type {
	RentalFilterState,
	RentalStatsResult,
	RentalLayoutRow,
	RentalTrendPoint,
	RentalDistrictRow,
	RentalProjectRow
} from './rental_types';

// ─── Helpers ────────────────────────────────────────────────────────────────

function esc(s: string): string {
	return s.replace(/'/g, "''");
}

/**
 * Build a WHERE clause for the rental table.
 * `yearOverride` lets trend queries pin to a specific year while ignoring
 * the filter's year field (they iterate all years themselves).
 */
function buildRentalWhere(
	f: RentalFilterState,
	latestYear: number,
	yearOverride?: number | null
): string {
	const clauses: string[] = [];

	const resolvedYear = yearOverride !== undefined
		? yearOverride
		: (f.year ?? latestYear);

	if (resolvedYear !== null) {
		clauses.push(`year = ${resolvedYear}`);
	}

	// Exclude summary rows when a specific layout / typology is requested
	// (summary rows have layout = "all beds" / typology = "All property types")
	if (f.typology && f.typology !== 'All property types') {
		clauses.push(`typology = '${esc(f.typology)}'`);
	} else {
		// Default: show only "All property types" aggregates to avoid double-counting
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
	const where = buildRentalWhere(f, latestYear);

	const [row] = await query<{
		project_count: number;
		median_rent: number;
		lower_rent: number;
		upper_rent: number;
	}>(`
		SELECT
			COUNT(DISTINCT project_name) AS project_count,
			PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS median_rent,
			PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY median_rent) AS lower_rent,
			PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY median_rent) AS upper_rent
		FROM rental
		WHERE ${where}
	`);

	return {
		projectCount: row?.project_count ?? 0,
		medianRent:   row?.median_rent   ?? 0,
		lowerRent:    row?.lower_rent    ?? 0,
		upperRent:    row?.upper_rent    ?? 0
	};
}

// ─── Layout breakdown ────────────────────────────────────────────────────────

/**
 * Per-layout summary: project count + rent percentiles.
 * Ignores f.layout and f.typology so every bed size is shown.
 */
export async function queryRentalByLayout(
	f: RentalFilterState,
	latestYear: number
): Promise<RentalLayoutRow[]> {
	const resolvedYear = f.year ?? latestYear;

	const clauses: string[] = [
		`year = ${resolvedYear}`,
		`typology = 'All property types'`,
		`layout != 'all beds'`,   // exclude the all-beds summary row
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
	// Use "all beds" + "All property types" + chosen rent_type across ALL years
	const clauses: string[] = [
		`typology = 'All property types'`,
		`layout   = 'all beds'`,
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

	const where = buildRentalWhere(f, latestYear);

	// Previous-year median for YoY calc
	const prevClauses: string[] = [
		`year = ${prevYear}`,
		`typology = '${esc(f.typology || 'All property types')}'`,
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
		FROM rental
		WHERE ${where}
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
				lower_rent,
				median_rent,
				upper_rent
			FROM rental
			WHERE ${where}
		),
		prev AS (
			SELECT project_name, median_rent AS prev_median
			FROM rental
			WHERE ${prevWhere}
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
		LEFT JOIN prev p ON c.project_name = p.project_name
		ORDER BY ${orderByCol} ${direction} NULLS LAST
		LIMIT ${pageSize} OFFSET ${offset}
	`);

	return { rows, total };
}
