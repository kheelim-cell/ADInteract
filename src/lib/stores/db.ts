import { writable } from 'svelte/store';
import type { Metadata } from '$lib/db/types';

export const dbReady = writable(false);
export const dbError = writable<string | null>(null);
export const dbLoading = writable(true);
export const metadata = writable<Metadata | null>(null);
