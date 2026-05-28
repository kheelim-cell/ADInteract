import { writable } from 'svelte/store';
import type { Metadata } from '$lib/db/types';
import type { RentalMetadata } from '$lib/db/rental_types';

export const dbReady = writable(false);
export const dbError = writable<string | null>(null);
export const dbLoading = writable(true);
export const metadata = writable<Metadata | null>(null);
export const rentalMetadata = writable<RentalMetadata | null>(null);

// District transaction counts — populated once after DB is ready
// Sales: all-time transaction count per district
// Rental: distinct project count per district (latest year)
export const salesDistrictCounts = writable<Record<string, number>>({});
export const rentalDistrictCounts = writable<Record<string, number>>({});
