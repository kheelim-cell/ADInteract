export interface Transaction {
	sale_date: string;
	district: string;
	community: string;
	project_name: string;
	asset_class: string;
	property_type: string;
	layout: string;
	area_sqft: number | null;
	land_area_sqft: number | null;
	price_aed: number;
	sold_share: number;
	rate_per_sqft: number | null;
	sale_type: string;
	sale_sequence: string;
}

export interface FilterState {
	district: string | null;
	project: string | null;
	dateRange: '1m' | '3m' | '6m' | '12m' | '3y' | 'custom';
	customDateStart: string | null;
	customDateEnd: string | null;
	saleType: 'all' | 'off-plan' | 'ready';
	propertyTypes: string[];
	layouts: string[];
	sortColumn: string;
	sortDirection: 'asc' | 'desc';
	page: number;
	pageSize: number;
}

export interface StatsResult {
	totalVolume: number;
	medianPrice: number;
	medianRatePerSqft: number;
	totalValue: number;
	prevTotalVolume: number;
	prevMedianPrice: number;
	prevMedianRatePerSqft: number;
	prevTotalValue: number;
}

export interface ChartDataPoint {
	month: string;
	volume: number;
	medianPrice: number;
	medianRate: number;
	offPlanVolume: number;
	readyVolume: number;
}

export interface DistrictSummary {
	district: string;
	volume: number;
	medianPrice: number;
	medianRate: number;
}

export interface PriceDistributionPoint {
	layout: string;
	min: number;
	q1: number;
	median: number;
	q3: number;
	max: number;
	count: number;
}

export interface Metadata {
	lastUpdated: string;
	rowCount: number;
	dateRange: { min: string; max: string };
	districts: string[];
	communities: string[];
	propertyTypes: string[];
	layouts: string[];
	projects: string[];
}

export const DEFAULT_FILTERS: FilterState = {
	district: null,
	project: null,
	dateRange: '12m',
	customDateStart: null,
	customDateEnd: null,
	saleType: 'all',
	propertyTypes: [],
	layouts: [],
	sortColumn: 'sale_date',
	sortDirection: 'desc',
	page: 1,
	pageSize: 50
};
