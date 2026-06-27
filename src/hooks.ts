import type { Reroute } from '@sveltejs/kit';
import { deLocalizeUrl } from '$lib/paraglide/runtime.js';

/**
 * Client-side reroute hook.
 *
 * SvelteKit calls this *before* matching a request against the route tree.
 * Strip any locale prefix here so `/ar/area/al-reem-island` is matched against
 * the existing `src/routes/area/[district]/+page.svelte` file — no need to
 * duplicate route files per locale.
 */
export const reroute: Reroute = ({ url }) => deLocalizeUrl(url).pathname;
