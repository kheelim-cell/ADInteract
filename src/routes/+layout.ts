export const prerender = true;
// SSR on: prerendered pages must emit real HTML (titles, OG tags, SEO prose).
// Browser-only work (DuckDB-WASM, Supabase auth) is gated behind onMount/browser
// checks, and the root layout only renders the loading gate in-browser.
export const ssr = true;
