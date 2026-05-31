import { query } from './duckdb';

function esc(s: string): string {
	return s.replace(/'/g, "''");
}

export interface InvestorFilterState {
	district?: string | null;
	propertyType?: string | null;  // applies to transactions.property_type
	layout?: string | null;        // applies to both tables
}

/** Extra AND clauses for the transactions table (sales queries) */
function salesExtra(f?: InvestorFilterState): string {
	const parts: string[] = [];
	if (f?.district)     parts.push(`district = '${esc(f.district)}'`);
	if (f?.propertyType) parts.push(`property_type = '${esc(f.propertyType)}'`);
	if (f?.layout)       parts.push(`layout = '${esc(f.layout)}'`);
	return parts.length ? ' AND ' + parts.join(' AND ') : '';
}

/** layout condition for rental queries (override 'all beds' when user picks a layout) */
function rentalLayoutCond(f?: InvestorFilterState): string {
	return f?.layout ? `layout = '${esc(f.layout)}'` : `layout = 'all beds'`;
}

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
	limit = 5,
	filters?: InvestorFilterState
): Promise<GrowthRow[]> {
	const extra = salesExtra({ ...filters, district: null }); // district filter n/a — we're ranking districts
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
			  ${extra}
			GROUP BY district
			HAVING COUNT(*) >= 10
		),
		prv AS (
			SELECT district,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS prev_rate
			FROM transactions
			WHERE YEAR(sale_date) = ${prevYear}
			  AND rate_per_sqft IS NOT NULL AND rate_per_sqft > 0
			  ${extra}
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
	limit = 5,
	filters?: InvestorFilterState
): Promise<GrowthRow[]> {
	const extra = salesExtra(filters);
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
			  AND LOWER(project_name) != 'private'
			  ${extra}
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
			  AND LOWER(project_name) != 'private'
			  ${extra}
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
	limit = 5,
	filters?: InvestorFilterState
): Promise<GrowthRow[]> {
	const prevYear = currentYear - 1;
	const districtClause = filters?.district ? ` AND district = '${esc(filters.district)}'` : '';
	const layoutCond = rentalLayoutCond(filters);
	const rows = await query<{
		project_name: string;
		district: string;
		current_rent: number;
		prev_rent: number;
		yoy_pct: number;
	}>(`
		WITH cur AS (
			-- Use real per-typology rows (not the aggregate sentinel) for accuracy.
			-- Median of medians across typologies gives a figure consistent with
			-- what users see in the Rental tab.
			SELECT project_name,
			       ANY_VALUE(district) AS district,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS current_rent
			FROM rental
			WHERE year = ${currentYear}
			  AND typology != 'All property types'
			  AND ${layoutCond}
			  AND rent_type = 'All types'
			  AND median_rent > 0
			  AND project_name IS NOT NULL AND project_name != ''
			  AND LOWER(project_name) != 'private'
			  ${districtClause}
			GROUP BY project_name
		),
		prv AS (
			SELECT project_name,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS prev_rent
			FROM rental
			WHERE year = ${prevYear}
			  AND typology != 'All property types'
			  AND ${layoutCond}
			  AND rent_type = 'All types'
			  AND median_rent > 0
			  AND project_name IS NOT NULL AND project_name != ''
			  AND LOWER(project_name) != 'private'
			  ${districtClause}
			GROUP BY project_name
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

// ─── Off-Plan Flip Scanner ─────────────────────────────────────────────────

export interface FlipRow {
	projectName: string;
	district: string;
	layout: string;
	entryPsf: number;       // median off-plan rate/sqft — registered in the entry window
	exitPsf: number;        // median secondary-market rate/sqft — last 12 months
	psfGain: number;        // exitPsf − entryPsf
	roiPct: number;         // gain / entryPsf × 100
	offplanCount: number;   // # off-plan tx used to compute entryPsf
	secondaryCount: number; // # secondary tx used to compute exitPsf
	earliestOffplan: string;
	latestOffplan: string;
}

/**
 * Compare median off-plan entry prices (registered N months ago) against
 * current secondary-market prices for the same project + layout.
 *
 * @param entryStartMonths  How far back the off-plan window starts (default 48 months)
 * @param entryEndMonths    How recent the off-plan window ends   (default 12 months)
 *                          i.e. entries between 48 and 12 months ago
 * @param minOffplanCount   Minimum off-plan tx required (default 3)
 * @param minSecondaryCount Minimum secondary tx required (default 2)
 */
export async function queryFlipScanner(
	filters?: InvestorFilterState,
	entryStartMonths = 48,
	entryEndMonths = 12,
	minOffplanCount = 3,
	minSecondaryCount = 2
): Promise<FlipRow[]> {
	const now = new Date();
	function subtractMonths(d: Date, m: number): string {
		const r = new Date(d.getFullYear(), d.getMonth() - m, d.getDate());
		return r.toISOString().slice(0, 10);
	}
	const windowStart  = subtractMonths(now, entryStartMonths); // e.g. 48 months ago
	const windowEnd    = subtractMonths(now, entryEndMonths);   // e.g. 12 months ago
	const exitStart    = subtractMonths(now, 12);               // last 12 months
	const today        = now.toISOString().slice(0, 10);

	const districtClause = filters?.district ? `AND op.district = '${esc(filters.district)}'` : '';
	const layoutClause   = filters?.layout   ? `AND op.layout   = '${esc(filters.layout)}'`   : '';
	const layoutExitClause = filters?.layout ? `AND sx.layout   = '${esc(filters.layout)}'`   : '';

	const rows = await query<{
		project_name: string;
		district: string;
		layout: string;
		entry_psf: number;
		exit_psf: number;
		psf_gain: number;
		roi_pct: number;
		offplan_count: number;
		secondary_count: number;
		earliest_offplan: string;
		latest_offplan: string;
	}>(`
		WITH offplan_entries AS (
			SELECT
				project_name,
				district,
				layout,
				PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS entry_psf,
				COUNT(*)                                                      AS offplan_count,
				MIN(sale_date::VARCHAR)                                       AS earliest_offplan,
				MAX(sale_date::VARCHAR)                                       AS latest_offplan
			FROM transactions op
			WHERE op.sale_type = 'off-plan'
			  AND op.sale_date >= '${windowStart}'
			  AND op.sale_date <  '${windowEnd}'
			  AND op.rate_per_sqft IS NOT NULL AND op.rate_per_sqft > 0
			  AND op.project_name  IS NOT NULL AND op.project_name  != ''
			  AND LOWER(op.project_name) != 'private'
			  AND op.layout        IS NOT NULL AND op.layout        != ''
			  ${districtClause}
			  ${layoutClause}
			GROUP BY project_name, district, layout
			HAVING COUNT(*) >= ${minOffplanCount}
		),
		secondary_exits AS (
			SELECT
				sx.project_name,
				sx.layout,
				PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sx.rate_per_sqft) AS exit_psf,
				COUNT(*)                                                        AS secondary_count
			FROM transactions sx
			WHERE sx.sale_sequence = 'secondary'
			  AND sx.sale_date >= '${exitStart}'
			  AND sx.sale_date <= '${today}'
			  AND sx.rate_per_sqft IS NOT NULL AND sx.rate_per_sqft > 0
			  AND sx.project_name  IS NOT NULL AND sx.project_name  != ''
			  AND LOWER(sx.project_name) != 'private'
			  AND sx.layout        IS NOT NULL AND sx.layout        != ''
			  ${layoutExitClause}
			GROUP BY sx.project_name, sx.layout
			HAVING COUNT(*) >= ${minSecondaryCount}
		)
		SELECT
			o.project_name,
			o.district,
			o.layout,
			ROUND(o.entry_psf, 0)                                   AS entry_psf,
			ROUND(s.exit_psf,  0)                                   AS exit_psf,
			ROUND(s.exit_psf - o.entry_psf, 0)                     AS psf_gain,
			ROUND(((s.exit_psf - o.entry_psf) / o.entry_psf) * 100, 1) AS roi_pct,
			o.offplan_count,
			s.secondary_count,
			o.earliest_offplan,
			o.latest_offplan
		FROM offplan_entries o
		JOIN secondary_exits s
		  ON LOWER(TRIM(o.project_name)) = LOWER(TRIM(s.project_name))
		  AND o.layout = s.layout
		WHERE s.exit_psf > o.entry_psf
		ORDER BY roi_pct DESC
		LIMIT 150
	`);

	return rows.map(r => ({
		projectName:    r.project_name,
		district:       r.district,
		layout:         r.layout,
		entryPsf:       r.entry_psf,
		exitPsf:        r.exit_psf,
		psfGain:        r.psf_gain,
		roiPct:         r.roi_pct,
		offplanCount:   r.offplan_count,
		secondaryCount: r.secondary_count,
		earliestOffplan: r.earliest_offplan,
		latestOffplan:   r.latest_offplan,
	}));
}

// ─── District Side-by-Side Comparison ──────────────────────────────────────

export interface DistrictComparisonData {
	district: string;
	medianPrice: number | null;       // AED, rolling 12 months
	medianPsf: number | null;         // AED/sqft, rolling 12 months
	prevPsf: number | null;           // AED/sqft, prior 12 months (for YoY)
	yoyPct: number | null;            // median AED/sqft YoY growth %
	medianAnnualRent: number | null;  // AED, latest rental year
	grossYieldPct: number | null;     // medianAnnualRent / medianPrice × 100
	txCount: number;                  // sales volume, rolling 12 months
	pipelineCount: number;            // off-plan primary registrations, last 3 years
}

/**
 * Compare 2–3 districts across 7 investment metrics.
 * Uses rolling date windows (not calendar years) for most-current data.
 *
 * @param districts  Array of 2–3 district name strings (must match DB values)
 * @param layout     DB layout value: 'studio' | '1 bed' | '2 beds' | '3 beds'
 * @param rentalYear Latest available year in the rental table
 */
export async function queryDistrictComparison(
	districts: string[],
	layout: string,
	rentalYear: number
): Promise<DistrictComparisonData[]> {
	if (districts.length === 0) return [];

	function subtractDays(d: Date, days: number): string {
		const r = new Date(d);
		r.setDate(r.getDate() - days);
		return r.toISOString().slice(0, 10);
	}

	const now    = new Date();
	const today  = now.toISOString().slice(0, 10);
	const d365   = subtractDays(now, 365);   // current window start
	const d730   = subtractDays(now, 730);   // prior window start
	const d1095  = subtractDays(now, 1095);  // 3-year pipeline start

	const distList         = districts.map(d => `'${esc(d)}'`).join(', ');
	const layoutCond       = `layout = '${esc(layout)}'`;
	const rentalLayoutSQL  = `layout = '${esc(layout)}'`;

	const rows = await query<{
		district: string;
		median_price: number | null;
		median_psf: number | null;
		prev_psf: number | null;
		yoy_pct: number | null;
		median_annual_rent: number | null;
		gross_yield_pct: number | null;
		tx_count: number;
		pipeline_count: number;
	}>(`
		WITH
		cur AS (
			SELECT district,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_aed)    AS median_price,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS median_psf,
			       COUNT(*) AS tx_count
			FROM transactions
			WHERE sale_date >= '${d365}' AND sale_date <= '${today}'
			  AND price_aed > 0 AND rate_per_sqft > 0
			  AND ${layoutCond}
			  AND district IN (${distList})
			GROUP BY district
		),
		prv AS (
			SELECT district,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_per_sqft) AS prev_psf
			FROM transactions
			WHERE sale_date >= '${d730}' AND sale_date < '${d365}'
			  AND rate_per_sqft > 0
			  AND ${layoutCond}
			  AND district IN (${distList})
			GROUP BY district
		),
		rents AS (
			SELECT district,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_rent) AS median_annual_rent
			FROM rental
			WHERE year = ${rentalYear}
			  AND typology = 'All property types'
			  AND ${rentalLayoutSQL}
			  AND rent_type = 'All types'
			  AND median_rent > 0
			  AND district IN (${distList})
			GROUP BY district
		),
		pipeline AS (
			SELECT district, COUNT(*) AS pipeline_count
			FROM transactions
			WHERE sale_type = 'off-plan'
			  AND sale_sequence = 'primary'
			  AND sale_date >= '${d1095}'
			  AND sale_date <= '${today}'
			  AND district IN (${distList})
			GROUP BY district
		)
		SELECT
			c.district,
			ROUND(c.median_price, 0)  AS median_price,
			ROUND(c.median_psf, 0)    AS median_psf,
			ROUND(p.prev_psf, 0)      AS prev_psf,
			CASE
				WHEN p.prev_psf IS NOT NULL AND p.prev_psf > 0
				THEN ROUND(((c.median_psf - p.prev_psf) / p.prev_psf) * 100, 1)
				ELSE NULL
			END AS yoy_pct,
			ROUND(r.median_annual_rent, 0) AS median_annual_rent,
			CASE
				WHEN c.median_price > 0 AND r.median_annual_rent IS NOT NULL
				THEN ROUND((r.median_annual_rent / c.median_price) * 100, 2)
				ELSE NULL
			END AS gross_yield_pct,
			c.tx_count,
			COALESCE(pl.pipeline_count, 0) AS pipeline_count
		FROM cur c
		LEFT JOIN prv p      ON c.district = p.district
		LEFT JOIN rents r    ON c.district = r.district
		LEFT JOIN pipeline pl ON c.district = pl.district
		ORDER BY c.tx_count DESC
	`);

	return rows.map(r => ({
		district:         r.district,
		medianPrice:      r.median_price,
		medianPsf:        r.median_psf,
		prevPsf:          r.prev_psf,
		yoyPct:           r.yoy_pct,
		medianAnnualRent: r.median_annual_rent,
		grossYieldPct:    r.gross_yield_pct,
		txCount:          Number(r.tx_count),
		pipelineCount:    Number(r.pipeline_count),
	}));
}

// ─── Rental yield by community ─────────────────────────────────────────────

/**
 * Gross rental yield by community.
 * yield = median annual rent (rental table, rentalYear) / median sale price (transactions, salesYear) × 100
 *
 * Join strategy: bridge rental → community via project_name in transactions.
 * Only transactions from salesYear are used for the mapping to keep the join small.
 */
export async function queryRentalYieldByCommunity(
	salesYear: number,
	rentalYear: number,
	minSaleCount = 5,
	filters?: InvestorFilterState
): Promise<YieldRow[]> {
	const districtClause  = filters?.district     ? `AND district      = '${esc(filters.district)}'`     : '';
	const layoutSalesCond = filters?.layout        ? `AND layout        = '${esc(filters.layout)}'`        : '';
	const propTypeCond    = filters?.propertyType  ? `AND property_type = '${esc(filters.propertyType)}'`  : '';
	const rentalLayout    = rentalLayoutCond(filters);   // 'all beds' or specific layout
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
			  ${districtClause}
			  ${layoutSalesCond}
			  ${propTypeCond}
			GROUP BY community, district
			HAVING COUNT(*) >= ${minSaleCount}
		),
		proj_map AS (
			SELECT DISTINCT LOWER(TRIM(project_name)) AS proj_key, community
			FROM transactions
			WHERE YEAR(sale_date) = ${salesYear}
			  AND community IS NOT NULL AND community != ''
			  AND project_name IS NOT NULL AND project_name != ''
		),
		rents AS (
			SELECT pm.community,
			       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY r.median_rent) AS median_annual_rent,
			       COUNT(DISTINCT r.project_name) AS project_count
			FROM rental r
			JOIN proj_map pm ON LOWER(TRIM(r.project_name)) = pm.proj_key
			WHERE r.year = ${rentalYear}
			  AND r.typology = 'All property types'
			  AND r.${rentalLayout}
			  AND r.rent_type = 'All types'
			  AND r.median_rent > 0
			GROUP BY pm.community
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

	return rows.map(r => ({
		community: r.community,
		district: r.district,
		medianSalePrice: r.median_sale_price,
		medianAnnualRent: r.median_annual_rent,
		grossYieldPct: r.gross_yield_pct,
		saleCount: r.sale_count,
		projectCount: r.project_count,
	}));
}
