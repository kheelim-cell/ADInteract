import adapterStatic from '@sveltejs/adapter-static';
import adapterVercel from '@sveltejs/adapter-vercel';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/**
 * Use adapter-vercel on Vercel (VERCEL env var is set automatically).
 * Use adapter-static everywhere else (GitHub Actions → GitHub Pages, local build).
 *
 * adapter-vercel: SvelteKit +server.ts API routes are deployed as Vercel
 *   Serverless Functions, so /api/extract-property works on the live site.
 *
 * adapter-static: generates static files only; API routes are excluded.
 *   Used for GitHub Pages deployment via data-refresh.yml.
 */
const isVercel = !!process.env.VERCEL;

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		adapter: isVercel
			? adapterVercel()
			: adapterStatic({ fallback: '404.html' }),
		paths: {
			base: ''
		},
		prerender: {
			// Seed Arabic entry points so the crawler discovers /ar/* before any
			// language switcher links to them. Without this, prerendering only
			// produces English HTML and the AR scaffold can't be verified.
			entries: ['*', '/ar/', '/ar/investors', '/ar/rental']
		}
	}
};

export default config;
