import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import { page } from '$app/stores';
import type { RentalFilterState } from '$lib/db/rental_types';
import { DEFAULT_RENTAL_FILTERS } from '$lib/db/rental_types';

// ─── Store ───────────────────────────────────────────────────────────────────

function createRentalFilters() {
	const { subscribe, set, update } = writable<RentalFilterState>({ ...DEFAULT_RENTAL_FILTERS });

	return {
		subscribe,
		set,
		update,
		reset: () => set({ ...DEFAULT_RENTAL_FILTERS })
	};
}

export const rentalFilters = createRentalFilters();

export function updateRentalFilter(patch: Partial<RentalFilterState>) {
	rentalFilters.update((f) => ({ ...f, ...patch }));
	if (browser) syncRentalToUrl();
}

export function resetRentalFilters() {
	rentalFilters.set({ ...DEFAULT_RENTAL_FILTERS });
	if (browser) {
		const url = new URL(window.location.href);
		// clear all rental params
		['rd', 'rc', 'rp', 'ry', 'rt', 'rl', 'rrt'].forEach((k) => url.searchParams.delete(k));
		window.history.replaceState({}, '', url.toString());
	}
}

// ─── URL sync ────────────────────────────────────────────────────────────────

/** Short param keys: r prefix to avoid collision with sales filter params */
const PARAM_MAP: Record<keyof RentalFilterState, string> = {
	district:  'rd',
	community: 'rc',
	project:   'rp',
	year:      'ry',
	typology:  'rty',
	layout:    'rl',
	rentType:  'rrt'
};

function syncRentalToUrl() {
	if (typeof window === 'undefined') return;
	const url = new URL(window.location.href);
	let f: RentalFilterState = { ...DEFAULT_RENTAL_FILTERS };
	rentalFilters.subscribe((v) => (f = v))();

	for (const [key, param] of Object.entries(PARAM_MAP) as [keyof RentalFilterState, string][]) {
		const val = f[key];
		if (val !== null && val !== undefined && val !== DEFAULT_RENTAL_FILTERS[key]) {
			url.searchParams.set(param, String(val));
		} else {
			url.searchParams.delete(param);
		}
	}
	window.history.replaceState({}, '', url.toString());
}

export function loadRentalFiltersFromUrl() {
	if (typeof window === 'undefined') return;
	const params = new URLSearchParams(window.location.search);
	const patch: Partial<RentalFilterState> = {};

	if (params.has('rd'))  patch.district  = params.get('rd')  || null;
	if (params.has('rc'))  patch.community = params.get('rc')  || null;
	if (params.has('rp'))  patch.project   = params.get('rp')  || null;
	if (params.has('ry'))  patch.year      = Number(params.get('ry')) || null;
	if (params.has('rty')) patch.typology  = params.get('rty') || null;
	if (params.has('rl'))  patch.layout    = params.get('rl')  || null;
	if (params.has('rrt')) patch.rentType  = params.get('rrt') || 'All types';

	if (Object.keys(patch).length > 0) {
		rentalFilters.update((f) => ({ ...f, ...patch }));
	}
}
