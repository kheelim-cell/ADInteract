/**
 * Shareable Deal Analysis — encode/decode helpers.
 *
 * Encodes calculator state + pre-computed outputs into a URL-safe base64 string.
 * No backend required — the full analysis lives in the URL param `?s=<encoded>`.
 *
 * Usage:
 *   import { encodeDeal, decodeDeal } from '$lib/utils/dealShare';
 *   const encoded = encodeDeal(snapshot);
 *   const url = `${window.location.origin}/deal?s=${encoded}`;
 */

// ─── Types ─────────────────────────────────────────────────────────────────

export interface OffplanDealSnapshot {
	v: 1;
	type: 'offplan';
	// Optional: from AI property scanner
	projectName?: string;
	developer?: string;
	// Inputs
	district: string;
	layout: string;
	cost: number;
	size: number;
	comparableRent: number;
	yearsTillHandover: number;
	rentalAppPct: number;
	furnishingType: 'none' | 'basic_airbnb' | 'highend_airbnb' | 'branded_hospitality';
	mgmtFeePct: number;
	utilitiesMonthly: number;
	serviceChargePsf: number;
	yearsToResale: number;
	annualAppPct: number;
	otherFactorType: 'none' | 'basic_airbnb' | 'highend_airbnb' | 'branded_hospitality';
	resaleBrokerPct: number;
	// Pre-computed outputs (avoids re-implementing math in deal page)
	pricePerSqft: number;
	registrationFee: number;
	devRegistrationFee: number;
	totalPurchaseCost: number;
	grossRental: number;
	netRental: number;
	grossYield: number;
	netYield: number;
	sellingPrice: number;
	netProfit: number;
	netProfitPct: number;
	netProfitPerYear: number;
	totalRoiPa: number;
}

export interface ReadyDealSnapshot {
	v: 1;
	type: 'ready';
	// Optional: from AI property scanner
	projectName?: string;
	developer?: string;
	// Inputs
	district: string;
	layout: string;
	project: string;
	tenancyStatus: 'tenanted' | 'vacant';
	price: number;
	livingArea: number;
	balconyArea: number;
	serviceChargePsf: number;
	annualRent: number;
	mortgageType: 'none' | '1st' | '2nd';
	residency: 'uae_national' | 'uae_resident' | 'non_resident';
	interestRate: number;
	termYears: number;
	comparablePsf: number;
	yearsToResale: number;
	annualAppPct: number;
	otherFactorType: 'none' | 'basic_airbnb' | 'highend_airbnb' | 'branded_hospitality';
	furnishingType: 'none' | 'basic_airbnb' | 'highend_airbnb' | 'branded_hospitality';
	additionalCapex: number;
	// Pre-computed outputs
	pricePerSqft: number;
	equityInjection: number;
	mortgageAmount: number;
	emi: number;
	totalMonthlyMortgage: number;
	serviceCharge: number;
	netAnnualRental: number;
	netYield: number;
	sellingPrice: number;
	netProfit: number;
	netProfitPct: number;
	netProfitPerYear: number;
	totalRoiPa: number;
}

export type DealSnapshot = OffplanDealSnapshot | ReadyDealSnapshot;

// ─── Encode / Decode ───────────────────────────────────────────────────────

export function encodeDeal(snapshot: DealSnapshot): string {
	try {
		return btoa(encodeURIComponent(JSON.stringify(snapshot)));
	} catch {
		return '';
	}
}

export function decodeDeal(encoded: string): DealSnapshot | null {
	try {
		const json = decodeURIComponent(atob(encoded));
		const obj = JSON.parse(json) as DealSnapshot;
		if (obj.v !== 1) return null;
		if (obj.type !== 'offplan' && obj.type !== 'ready') return null;
		return obj;
	} catch {
		return null;
	}
}

// ─── Helpers ───────────────────────────────────────────────────────────────

export function buildDealUrl(snapshot: DealSnapshot, origin: string, basePath = ''): string {
	const encoded = encodeDeal(snapshot);
	return `${origin}${basePath}/deal?s=${encoded}`;
}
