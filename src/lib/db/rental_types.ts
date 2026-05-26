// Rental Index — TypeScript interfaces

export interface RentalRecord {
	project_id: number | null;
	project_name: string;
	municipality: string;
	district: string;
	community: string;
	typology: string;
	layout: string;
	lower_rent: number | null;
	median_rent: number;
	upper_rent: number | null;
	year: number;
	rent_type: string;
}

export interface RentalFilterState {
	district: string | null;
	community: string | null;
	project: string | null;
	year: number | null;          // null = latest available
	typology: string | null;      // null = "All property types"
	layout: string | null;        // null = "all beds"
	rentType: string;             // "All types" | "New" | "Renew"
}

export interface RentalStatsResult {
	projectCount:   number;
	medianRent:     number;
	lowerRent:      number;
	upperRent:      number;
	// Prior-year values for YoY growth badges (null when no prior year data)
	prevMedianRent: number | null;
	prevLowerRent:  number | null;
	prevUpperRent:  number | null;
	resolvedYear:   number;
	prevYear:       number;
}

/** One row in the layout breakdown table/chart */
export interface RentalLayoutRow {
	layout: string;
	projectCount: number;
	lowerRent: number;
	medianRent: number;
	upperRent: number;
}

/** One point on the year-over-year trend line */
export interface RentalTrendPoint {
	year: number;
	medianRent: number;
	projectCount: number;
}

/** One bar in the top-districts chart */
export interface RentalDistrictRow {
	district: string;
	medianRent: number;
	projectCount: number;
}

/** One row in the project table */
export interface RentalProjectRow {
	project_name: string;
	district: string;
	community: string;
	typology: string;
	layout: string;
	lower_rent: number | null;
	median_rent: number;
	upper_rent: number | null;
	prev_median_rent: number | null; // same project previous year
	yoy_change: number | null;        // (current - prev) / prev * 100
}

/** New contract vs renewal rent comparison by bed size */
export interface NewVsRenewRow {
	layout: string;
	newRent: number | null;
	renewRent: number | null;
	gapPct: number | null; // (new - renew) / renew * 100
}

/** Gross rental yield by district (cross-references transactions + rental) */
export interface PriceToRentRow {
	district: string;
	medianSalePrice: number;
	medianAnnualRent: number;
	grossYieldPct: number;    // annual_rent / sale_price × 100
	priceToRentYears: number; // sale_price / annual_rent
}

export interface RentalMetadata {
	lastUpdated: string;
	rowCount: number;
	years: number[];
	latestYear: number | null;
	districts: string[];
	municipalities: string[];
	communities: string[];
	projects: string[];
	typologies: string[];
	layouts: string[];
	rentTypes: string[];
}

export const DEFAULT_RENTAL_FILTERS: RentalFilterState = {
	district: null,
	community: null,
	project: null,
	year: null,      // resolved to latestYear at query time
	typology: null,
	layout: null,
	rentType: 'All types'
};
