import { getLocale } from '$lib/paraglide/runtime';

// Western digits (0–9) even on Arabic pages — matches Bayut, Property Finder,
// Aldar, Modon convention in the UAE/GCC. `numberingSystem: 'latn'` forces
// this while still localising separators/words for 'ar-AE'.
function intlLocale(): string {
	return getLocale() === 'ar' ? 'ar-AE' : 'en-AE';
}

function currencyFormatter(): Intl.NumberFormat {
	return new Intl.NumberFormat(intlLocale(), {
		maximumFractionDigits: 0,
		numberingSystem: 'latn'
	});
}

function compactFormatter(): Intl.NumberFormat {
	return new Intl.NumberFormat(intlLocale(), {
		notation: 'compact',
		maximumFractionDigits: 1,
		numberingSystem: 'latn'
	});
}

function dateFormatter(): Intl.DateTimeFormat {
	return new Intl.DateTimeFormat(getLocale() === 'ar' ? 'ar-AE' : 'en-GB', {
		day: 'numeric',
		month: 'short',
		year: 'numeric',
		numberingSystem: 'latn'
	});
}

export function formatCurrency(n: number | null | undefined): string {
	if (n == null || isNaN(n)) return '-';
	return currencyFormatter().format(n) + ' AED';
}

export function formatCurrencyShort(n: number | null | undefined): string {
	if (n == null || isNaN(n)) return '-';
	return compactFormatter().format(n);
}

export function formatNumber(n: number | null | undefined): string {
	if (n == null || isNaN(n)) return '-';
	return currencyFormatter().format(n);
}

export function formatRate(n: number | null | undefined): string {
	if (n == null || isNaN(n)) return '-';
	return currencyFormatter().format(n) + ' AED/sqft';
}

export function formatPercent(n: number | null | undefined): string {
	if (n == null || isNaN(n)) return '-';
	const sign = n > 0 ? '+' : '';
	return sign + n.toFixed(1) + '%';
}

export function formatDate(d: string | null | undefined): string {
	if (!d) return '-';
	return dateFormatter().format(new Date(d));
}

export function formatArea(sqft: number | null | undefined): string {
	if (sqft == null || isNaN(sqft)) return '-';
	return currencyFormatter().format(Math.round(sqft)) + ' sqft';
}

export function growthPercent(current: number, previous: number): number | null {
	if (!previous || previous === 0) return null;
	return ((current - previous) / previous) * 100;
}
