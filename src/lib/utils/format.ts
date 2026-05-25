const currencyFormatter = new Intl.NumberFormat('en-AE', {
	maximumFractionDigits: 0
});

const compactFormatter = new Intl.NumberFormat('en-AE', {
	notation: 'compact',
	maximumFractionDigits: 1
});

const dateFormatter = new Intl.DateTimeFormat('en-GB', {
	day: 'numeric',
	month: 'short',
	year: 'numeric'
});

export function formatCurrency(n: number | null | undefined): string {
	if (n == null || isNaN(n)) return '-';
	return currencyFormatter.format(n) + ' AED';
}

export function formatCurrencyShort(n: number | null | undefined): string {
	if (n == null || isNaN(n)) return '-';
	return compactFormatter.format(n);
}

export function formatNumber(n: number | null | undefined): string {
	if (n == null || isNaN(n)) return '-';
	return currencyFormatter.format(n);
}

export function formatRate(n: number | null | undefined): string {
	if (n == null || isNaN(n)) return '-';
	return currencyFormatter.format(n) + ' AED/sqft';
}

export function formatPercent(n: number | null | undefined): string {
	if (n == null || isNaN(n)) return '-';
	const sign = n > 0 ? '+' : '';
	return sign + n.toFixed(1) + '%';
}

export function formatDate(d: string | null | undefined): string {
	if (!d) return '-';
	return dateFormatter.format(new Date(d));
}

export function formatArea(sqft: number | null | undefined): string {
	if (sqft == null || isNaN(sqft)) return '-';
	return currencyFormatter.format(Math.round(sqft)) + ' sqft';
}

export function growthPercent(current: number, previous: number): number | null {
	if (!previous || previous === 0) return null;
	return ((current - previous) / previous) * 100;
}
