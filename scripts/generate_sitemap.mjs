#!/usr/bin/env node
// generate_sitemap.mjs
// ---------------------------------------------------------------------------
// Regenerates static/sitemap.xml from live data on every build.
//
// Why this exists: sitemap.xml was hand-committed once (see git blame) and
// only ever listed 7 of the 96 prerendered /area/[district] pages, using
// space-encoded district names ("Al%20Reem%20Island") that don't match the
// actual slug-based routes the app serves ("al-reem-island"). Those 7 URLs
// 404 against the canonical host. This script fixes both problems by
// deriving every URL from the same data the routes themselves prerender
// from (district_summaries.json), so the sitemap can never drift out of
// sync with the site again.
//
// Canonical host: mirrors SITE_URL in src/routes/+layout.svelte (apex,
// no www) — keep these in sync if that ever changes.
//
// Runs as an npm "prebuild" step, so it fires on every Vercel deploy and
// every local/CI build, same as generate_og_images.mjs.
// ---------------------------------------------------------------------------

import { writeFileSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

const SITE_URL = 'https://adinteract.co';
const today = new Date().toISOString().slice(0, 10);

// Hand-maintained core + Investors pages. These aren't derived from a data
// file, so they stay an explicit list — add a line here when a new
// permanent top-level page ships. (Investors pages are sign-in-gated at the
// UI layer but still prerender full HTML — see src/routes/investors/+layout.svelte
// — so they remain legitimately indexable; not expanding this list to the
// other Investors subpages in this pass, since that needs a per-page check
// this script isn't scoped to do.)
const CORE_PAGES = [
  { loc: '/', changefreq: 'weekly', priority: '1.0' },
  { loc: '/rental', changefreq: 'weekly', priority: '0.9' },
  { loc: '/transactions', changefreq: 'weekly', priority: '0.7' },
  { loc: '/investors/calculator', changefreq: 'monthly', priority: '0.9' },
  { loc: '/investors/price-growth', changefreq: 'weekly', priority: '0.8' },
  { loc: '/investors/rental-yield', changefreq: 'weekly', priority: '0.8' },
  { loc: '/investors/service-charges', changefreq: 'monthly', priority: '0.7' },
  { loc: '/investors/faqs', changefreq: 'monthly', priority: '0.8' }
];

const districtSummaries = JSON.parse(
  readFileSync(path.join(ROOT, 'src/lib/data/district_summaries.json'), 'utf-8')
);

const districtPages = Object.entries(districtSummaries)
  // Highest-volume districts first — cosmetic (order has no SEO effect) but
  // keeps the file diffable/reviewable as volumes shift.
  .sort(([, a], [, b]) => (b.tx_count_all ?? 0) - (a.tx_count_all ?? 0))
  .map(([, d]) => {
    const active = d.is_12m && (d.tx_count_12m ?? 0) > 0;
    return {
      loc: `/area/${d.slug}`,
      lastmod: d.last_sale || today,
      changefreq: active ? 'weekly' : 'monthly',
      // Slightly favour districts with recent trading activity — all still
      // get indexed, this only nudges crawl priority.
      priority: active ? '0.7' : '0.5'
    };
  });

const allPages = [...CORE_PAGES, ...districtPages];

function urlEntry({ loc, lastmod, changefreq, priority }) {
  const enHref = `${SITE_URL}${loc}`;
  const arHref = `${SITE_URL}/ar${loc === '/' ? '/' : loc}`;
  return [
    '  <url>',
    `    <loc>${enHref}</loc>`,
    lastmod ? `    <lastmod>${lastmod}</lastmod>` : null,
    `    <changefreq>${changefreq}</changefreq>`,
    `    <priority>${priority}</priority>`,
    `    <xhtml:link rel="alternate" hreflang="en" href="${enHref}" />`,
    `    <xhtml:link rel="alternate" hreflang="ar" href="${arHref}" />`,
    `    <xhtml:link rel="alternate" hreflang="x-default" href="${enHref}" />`,
    '  </url>'
  ]
    .filter(Boolean)
    .join('\n');
}

const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">

${allPages.map(urlEntry).join('\n')}

</urlset>
`;

writeFileSync(path.join(ROOT, 'static/sitemap.xml'), xml);

console.log(
  `sitemap.xml: ${allPages.length} URLs (${CORE_PAGES.length} core + ${districtPages.length} districts)`
);
