import type { Handle } from '@sveltejs/kit';
import { paraglideMiddleware } from '$lib/paraglide/server.js';

/**
 * Paraglide locale-resolution + URL-rewrite middleware.
 *
 * For each incoming request:
 *   1. Paraglide determines the locale from the URL (`/ar/...` → `ar`,
 *      anything else → `en` baseLocale fallback).
 *   2. The URL is de-localized before being passed to SvelteKit, so existing
 *      routes under `src/routes/` are reused for every locale (no need to
 *      duplicate the route tree).
 *   3. `transformPageChunk` substitutes the `%paraglide.*%` placeholders in
 *      `src/app.html` with the resolved locale's metadata. Setting `<html lang>`
 *      and `<html dir>` here (rather than in a layout) means they're correct
 *      in the very first byte of HTML — necessary for prerendering, SEO, and
 *      avoiding RTL FOUC.
 */
const handleParaglide: Handle = ({ event, resolve }) =>
	paraglideMiddleware(event.request, ({ request, locale }) => {
		event.request = request;
		const ogLocale = locale === 'ar' ? 'ar_AE' : 'en_AE';
		const dir = locale === 'ar' ? 'rtl' : 'ltr';
		return resolve(event, {
			transformPageChunk: ({ html }) =>
				html
					.replace('%paraglide.lang%', locale)
					.replace('%paraglide.dir%', dir)
					.replace('%paraglide.ogLocale%', ogLocale)
		});
	});

export const handle: Handle = handleParaglide;
