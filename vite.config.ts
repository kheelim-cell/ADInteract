import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { paraglideVitePlugin } from '@inlang/paraglide-js';

export default defineConfig({
	plugins: [
		// Paraglide must run BEFORE sveltekit so the compiled runtime is on disk
		// before SvelteKit's plugin scans imports.
		paraglideVitePlugin({
			project: './project.inlang',
			outdir: './src/lib/paraglide',
			// URL-based locale: en at root, ar under /ar/*. Matches the SEO-friendly
			// path-prefix strategy approved in the plan. `baseLocale` fallback covers
			// any unmatched URL (404s, etc.).
			strategy: ['url', 'baseLocale'],
			urlPatterns: [
				{
					pattern: '/:path(.*)?',
					// AR listed FIRST so the more-specific `/ar/:path` pattern wins
					// before the catch-all EN `/:path` matches `/ar/foo` as English.
					localized: [
						['ar', '/ar/:path(.*)?'],
						['en', '/:path(.*)?']
					]
				}
			]
		}),
		sveltekit()
	],
	optimizeDeps: {
		exclude: ['@duckdb/duckdb-wasm']
	},
	build: {
		target: 'esnext'
	}
});
