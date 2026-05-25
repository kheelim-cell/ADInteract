import { writable, derived } from 'svelte/store';
import type { FilterState } from '$lib/db/types';
import { DEFAULT_FILTERS } from '$lib/db/types';
import { browser } from '$app/environment';

function parseUrlFilters(): FilterState {
	if (!browser) return { ...DEFAULT_FILTERS };
	const params = new URLSearchParams(window.location.search);
	return {
		district: params.get('district') || null,
		project: params.get('project') || null,
		dateRange: (params.get('range') as FilterState['dateRange']) || '12m',
		customDateStart: params.get('from') || null,
		customDateEnd: params.get('to') || null,
		saleType: (params.get('type') as FilterState['saleType']) || 'all',
		propertyTypes: params.get('propType')?.split(',').filter(Boolean) || [],
		layouts: params.get('layout')?.split(',').filter(Boolean) || [],
		sortColumn: params.get('sort') || 'sale_date',
		sortDirection: (params.get('dir') as 'asc' | 'desc') || 'desc',
		page: parseInt(params.get('page') || '1', 10),
		pageSize: 50
	};
}

export const filters = writable<FilterState>(parseUrlFilters());

export function updateFilter(partial: Partial<FilterState>) {
	filters.update((f) => {
		const updated = { ...f, ...partial };
		if (!('page' in partial)) updated.page = 1;
		return updated;
	});
}

export function resetFilters() {
	filters.set({ ...DEFAULT_FILTERS });
}

export const dateRangeMs = derived(filters, ($f) => {
	const now = new Date();
	let start: Date;
	const end = now;

	switch ($f.dateRange) {
		case '1m':
			start = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
			break;
		case '3m':
			start = new Date(now.getFullYear(), now.getMonth() - 3, now.getDate());
			break;
		case '6m':
			start = new Date(now.getFullYear(), now.getMonth() - 6, now.getDate());
			break;
		case '12m':
			start = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
			break;
		case '3y':
			start = new Date(now.getFullYear() - 3, now.getMonth(), now.getDate());
			break;
		case 'custom':
			start = $f.customDateStart ? new Date($f.customDateStart) : new Date(2019, 0, 1);
			return {
				start: start.toISOString().slice(0, 10),
				end: ($f.customDateEnd || end.toISOString().slice(0, 10))
			};
		default:
			start = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
	}
	return {
		start: start.toISOString().slice(0, 10),
		end: end.toISOString().slice(0, 10)
	};
});

export const prevDateRange = derived(dateRangeMs, ($range) => {
	const start = new Date($range.start);
	const end = new Date($range.end);
	const durationMs = end.getTime() - start.getTime();
	const prevEnd = new Date(start.getTime() - 1);
	const prevStart = new Date(prevEnd.getTime() - durationMs);
	return {
		start: prevStart.toISOString().slice(0, 10),
		end: prevEnd.toISOString().slice(0, 10)
	};
});

if (browser) {
	filters.subscribe(($f) => {
		const params = new URLSearchParams();
		if ($f.district) params.set('district', $f.district);
		if ($f.project) params.set('project', $f.project);
		if ($f.dateRange !== '12m') params.set('range', $f.dateRange);
		if ($f.customDateStart) params.set('from', $f.customDateStart);
		if ($f.customDateEnd) params.set('to', $f.customDateEnd);
		if ($f.saleType !== 'all') params.set('type', $f.saleType);
		if ($f.propertyTypes.length) params.set('propType', $f.propertyTypes.join(','));
		if ($f.layouts.length) params.set('layout', $f.layouts.join(','));
		if ($f.sortColumn !== 'sale_date') params.set('sort', $f.sortColumn);
		if ($f.sortDirection !== 'desc') params.set('dir', $f.sortDirection);
		if ($f.page > 1) params.set('page', String($f.page));

		const qs = params.toString();
		const url = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
		window.history.replaceState({}, '', url);
	});
}
