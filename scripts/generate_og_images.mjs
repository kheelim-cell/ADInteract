/**
 * Build-time OG image generator — one 1200×630 PNG per district.
 *
 * Reads src/lib/data/district_summaries.json and renders a branded
 * "report card" image for each district into static/og/area/<slug>.png.
 * These are referenced by og:image on /area/[district] pages so links
 * unfurl with live stats in WhatsApp / iMessage / X.
 *
 * Runs automatically via the npm `prebuild` hook (local + Vercel).
 * Fonts: SVG text rendered by librsvg — uses system sans-serif stack,
 * so no font files are required at build time.
 */
import sharp from 'sharp';
import { readFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const OUT_DIR = path.join(ROOT, 'static', 'og', 'area');
const SUMMARIES = path.join(ROOT, 'src', 'lib', 'data', 'district_summaries.json');

const summaries = JSON.parse(readFileSync(SUMMARIES, 'utf-8'));
mkdirSync(OUT_DIR, { recursive: true });

const fmt = (n) => (n == null ? '—' : Math.round(n).toLocaleString('en-AE'));

function esc(s) {
	return String(s)
		.replaceAll('&', '&amp;')
		.replaceAll('<', '&lt;')
		.replaceAll('>', '&gt;')
		.replaceAll('"', '&quot;')
		.replaceAll("'", '&apos;');
}

/** Shrink district name font size so long names fit the canvas. */
function nameFontSize(name) {
	if (name.length <= 16) return 84;
	if (name.length <= 24) return 64;
	if (name.length <= 34) return 48;
	return 38;
}

function svgFor(districtName, s) {
	const range =
		s.p10_psf && s.p90_psf
			? `AED ${fmt(s.p10_psf)} – ${fmt(s.p90_psf)} /sqft range`
			: s.median_price
				? `Median transaction AED ${fmt(s.median_price)}`
				: '';
	const period = s.is_12m ? 'last 12 months' : 'all recorded sales';

	return `<svg width="1200" height="630" viewBox="0 0 1200 630" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0a2318"/>
      <stop offset="100%" stop-color="#143d2b"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <!-- subtle grid accents -->
  <g stroke="#ffffff" stroke-opacity="0.05" stroke-width="2">
    <line x1="0" y1="500" x2="1200" y2="500"/>
    <line x1="900" y1="0" x2="900" y2="630"/>
  </g>
  <!-- top bar: brand icon (inlined from static/brand/logo-icon.svg, gradient id renamed) + wordmark -->
  <g transform="translate(72,48) scale(0.36)">
    <defs>
      <linearGradient id="iconbg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#1e4d3a"/>
        <stop offset="100%" stop-color="#0d2318"/>
      </linearGradient>
    </defs>
    <rect width="200" height="200" rx="36" fill="url(#iconbg)"/>
    <rect x="12" y="12" width="176" height="176" rx="26" fill="rgba(255,255,255,0.08)" stroke="#C8A951" stroke-width="1.5" stroke-opacity="0.5"/>
    <path transform="translate(20,62) scale(2.0)" fill="#dfb83c"
      d="M0,38 L0,30 L5,30 L5,26 L10,26 L10,30 L11,30 L11,25 Q15.5,18 20,25 L20,30 L21,30
         L21,21 L23,21 L23,13 L25,3 L27,13 L27,21 L29,21 L29,17 L31,17 L31,7 L32,7 L32,2
         L32.5,0 L33,2 L33,7 L34,7 L34,17 L35,17 L35,21 L37,21 L37,13 L39.5,7 L42,13 L42,21
         L44,21 L44,16 L47,13 L50,16 L50,21 L52,21 L52,27 L57,27 L57,23 L64,23 L64,27 L72,27
         L72,31 L80,31 L80,38 Z"/>
  </g>
  <text x="160" y="88" font-family="Arial, Helvetica, sans-serif" font-size="36" letter-spacing="1"><tspan font-weight="800" fill="#dfb83c">AD</tspan><tspan font-style="italic" font-weight="600" fill="#C8A951">INTERACT</tspan></text>
  <text x="160" y="118" font-family="Arial, Helvetica, sans-serif" font-size="20" letter-spacing="2" fill="#9db8aa">ABU DHABI PROPERTY TRANSACTIONS · ADREC DATA</text>

  <!-- district name -->
  <text x="72" y="250" font-family="Arial, Helvetica, sans-serif" font-size="${nameFontSize(districtName)}" font-weight="800" fill="#ffffff">${esc(districtName)}</text>

  <!-- headline stat -->
  <text x="72" y="375" font-family="Arial, Helvetica, sans-serif" font-size="96" font-weight="800" fill="#dfb83c">AED ${fmt(s.median_psf)}<tspan font-size="44" fill="#cde7d8"> /sqft median</tspan></text>
  <text x="72" y="432" font-family="Arial, Helvetica, sans-serif" font-size="30" fill="#cde7d8">${esc(range)}</text>

  <!-- footer stats -->
  <text x="72" y="556" font-family="Arial, Helvetica, sans-serif" font-size="28" font-weight="700" fill="#ffffff">${fmt(s.tx_count_12m)} verified transactions <tspan fill="#9db8aa" font-weight="400">· ${esc(period)}</tspan></text>
  <text x="72" y="596" font-family="Arial, Helvetica, sans-serif" font-size="24" fill="#9db8aa">Free live data → adinteract.co</text>
</svg>`;
}

let ok = 0;
let failed = 0;
for (const [districtName, s] of Object.entries(summaries)) {
	try {
		const png = await sharp(Buffer.from(svgFor(districtName, s))).png().toBuffer();
		const out = path.join(OUT_DIR, `${s.slug}.png`);
		await sharp(png).toFile(out);
		ok++;
	} catch (err) {
		failed++;
		console.error(`og: failed for ${districtName}: ${err.message}`);
	}
}
console.log(`og: generated ${ok} district images${failed ? `, ${failed} failed` : ''} → static/og/area/`);
if (failed > 0 && ok === 0) process.exit(1);
