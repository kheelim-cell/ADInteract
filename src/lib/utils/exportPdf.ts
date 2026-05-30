/**
 * exportMarketReportPdf
 *
 * Generates a styled HTML market report and opens it in a new window so the
 * browser's native Save-as-PDF dialog can be used. No server round-trip, no
 * extra npm packages — just a print-optimised HTML template.
 *
 * Logic:
 *   • Project selected  → leaderboard = Price by Layout
 *   • District selected → leaderboard = Top 5 Projects in that District
 *   • No filter         → leaderboard = Top 5 Areas by Volume
 */

import type { StatsResult, DistrictSummary, LayoutSummaryRow, FilterState } from '$lib/db/types';
import {
	exportTransactions,
	queryTopProjects,
	queryTopDistricts,
	queryLayoutSummary
} from '$lib/db/queries';
import { formatCurrency, formatRate, formatCurrencyShort, formatDate, growthPercent } from './format';

// ─── helpers ─────────────────────────────────────────────────────────────────

function fmtDateShort(d: string): string {
	const [y, m, day] = d.split('-');
	return new Date(Number(y), Number(m) - 1, Number(day)).toLocaleDateString('en-GB', {
		day: 'numeric',
		month: 'short',
		year: 'numeric'
	});
}

function periodLabel(f: FilterState, dateStart: string, dateEnd: string): string {
	switch (f.dateRange) {
		case '1m': return 'Last 30 Days';
		case '3m': return 'Last 3 Months';
		case '6m': return 'Last 6 Months';
		case '12m': return 'Last 12 Months';
		case '3y': return 'Last 3 Years';
		case 'ytd': return 'Year to Date';
		default: return `${fmtDateShort(dateStart)} – ${fmtDateShort(dateEnd)}`;
	}
}

function scopeLabel(f: FilterState): string {
	if (f.project) return f.project;
	if (f.district) return f.district;
	if (f.saleType === 'off-plan') return 'Abu Dhabi — Off-Plan Market';
	if (f.saleType === 'ready') return 'Abu Dhabi — Ready Market';
	return 'Abu Dhabi Property Market';
}

/**
 * Build the PDF filename / <title> tag.
 * Format: ADInteract - [District] - [Project] - [Status] - [PropertyType] - [Layout] - [Timeframe]
 * Only active (non-default) filters are included; hyphens separate each field.
 */
function buildFilename(f: FilterState, dateStart: string, dateEnd: string): string {
	const parts: string[] = ['ADInteract'];

	if (f.district) parts.push(f.district);
	if (f.project)  parts.push(f.project);
	if (f.saleType !== 'all') parts.push(f.saleType === 'off-plan' ? 'Off-Plan' : 'Ready');
	if (f.propertyTypes.length) {
		parts.push(f.propertyTypes.map(t => t.charAt(0).toUpperCase() + t.slice(1)).join('+'));
	}
	if (f.layouts.length) {
		// Remove spaces: "1 bed" → "1bed", "2 beds" → "2beds"
		parts.push(f.layouts.map(l => l.replace(/\s+/g, '')).join('+'));
	}

	const timeMap: Record<string, string> = {
		'1m': '1M', '3m': '3M', '6m': '6M', '12m': '12M', '3y': '3Y', 'ytd': 'YTD'
	};
	parts.push(f.dateRange && timeMap[f.dateRange]
		? timeMap[f.dateRange]
		: `${fmtDateShort(dateStart)} to ${fmtDateShort(dateEnd)}`
	);

	return parts.join(' - ');
}

function growthBadge(current: number, previous: number): string {
	const pct = growthPercent(current, previous);
	if (pct == null) return '';
	const up = pct >= 0;
	return `<span class="sg ${up ? 'up' : 'dn'}">${up ? '▲' : '▼'} ${Math.abs(pct).toFixed(1)}% vs prior period</span>`;
}

function rankSpan(i: number): string {
	const cls = i === 0 ? ' r1' : i === 1 ? ' r2' : i === 2 ? ' r3' : '';
	return `<span class="rnk${cls}">${i + 1}</span>`;
}

// Official logo embedded inline for print-window compatibility
// (relative URLs don't resolve in window.open blank windows)
const LOGO_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" style="height:72px;width:288px;flex-shrink:0;display:block">
  <defs>
    <linearGradient id="logobg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1e4d3a"/>
      <stop offset="100%" stop-color="#0d2318"/>
    </linearGradient>
    <linearGradient id="logogl" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="transparent"/>
      <stop offset="50%" stop-color="#C8A951" stop-opacity="0.85"/>
      <stop offset="100%" stop-color="transparent"/>
    </linearGradient>
  </defs>
  <rect width="800" height="200" fill="url(#logobg)"/>
  <rect width="800" height="2.5" fill="url(#logogl)"/>
  <rect x="24" y="24" width="152" height="152" rx="22" fill="rgba(255,255,255,0.06)" stroke="#C8A951" stroke-width="1.5" stroke-opacity="0.32"/>
  <path transform="translate(32,68) scale(1.7)" fill="#dfb83c"
    d="M0,38 L0,30 L5,30 L5,26 L10,26 L10,30 L11,30 L11,25 Q15.5,18 20,25 L20,30 L21,30
       L21,21 L23,21 L23,13 L25,3 L27,13 L27,21 L29,21 L29,17 L31,17 L31,7 L32,7 L32,2
       L32.5,0 L33,2 L33,7 L34,7 L34,17 L35,17 L35,21 L37,21 L37,13 L39.5,7 L42,13 L42,21
       L44,21 L44,16 L47,13 L50,16 L50,21 L52,21 L52,27 L57,27 L57,23 L64,23 L64,27 L72,27
       L72,31 L80,31 L80,38 Z"/>
  <text x="200" y="122" font-family="Montserrat,system-ui,-apple-system,sans-serif" font-size="76" fill="#dfb83c">
    <tspan font-weight="800" letter-spacing="-2">AD</tspan><tspan font-weight="300" font-style="italic" letter-spacing="-1">INTERACT</tspan>
  </text>
  <text x="202" y="154" font-family="Montserrat,system-ui,-apple-system,sans-serif"
        font-size="13.5" fill="rgba(200,169,81,0.75)" font-weight="600" letter-spacing="5">ABU DHABI PROPERTY TRANSACTIONS</text>
</svg>`;

// ─── main export ─────────────────────────────────────────────────────────────

export async function exportMarketReportPdf(opts: {
	filters: FilterState;
	dateStart: string;
	dateEnd: string;
	stats: StatsResult;
	/** Pre-computed top-areas data (used when no district/project filter active) */
	topAreas: DistrictSummary[];
	/** Pre-computed layout summary (used when a project filter is active) */
	layoutSummary: LayoutSummaryRow[];
}): Promise<void> {
	const { filters: f, dateStart, dateEnd, stats, topAreas, layoutSummary } = opts;

	// ── Determine leaderboard ──
	let leaderLabel: string;
	let leaderHead: string;
	let leaderBody: string;

	if (f.project) {
		// Project view: show layout/bedroom breakdown
		const rows: LayoutSummaryRow[] =
			layoutSummary.length > 0 ? layoutSummary : await queryLayoutSummary(f, dateStart, dateEnd);
		leaderLabel = 'Price by Bedroom Type';
		leaderHead = `<th>#</th><th>Layout</th><th class="r">Transactions</th><th class="r">Median Price</th><th class="r">Median AED/sqft</th>`;
		leaderBody = rows
			.map(
				(r, i) =>
					`<tr><td>${rankSpan(i)}</td><td>${r.layout.charAt(0).toUpperCase() + r.layout.slice(1)}</td>
          <td class="r">${r.count.toLocaleString()}</td>
          <td class="r">${formatCurrency(r.medianPrice)}</td>
          <td class="r">${formatRate(r.medianRate)}</td></tr>`
			)
			.join('');
	} else if (f.district) {
		// District view: top 5 projects within that district
		const projects = await queryTopProjects(f, dateStart, dateEnd, 5);
		leaderLabel = `Top Projects — ${f.district}`;
		leaderHead = `<th>#</th><th>Project</th><th class="r">Transactions</th><th class="r">Median Price</th><th class="r">Median AED/sqft</th>`;
		leaderBody = projects
			.map(
				(r, i) =>
					`<tr><td>${rankSpan(i)}</td><td>${r.district}</td>
          <td class="r">${r.volume.toLocaleString()}</td>
          <td class="r">${formatCurrency(r.medianPrice)}</td>
          <td class="r">${formatRate(r.medianRate)}</td></tr>`
			)
			.join('');
	} else {
		// All Abu Dhabi: top 5 areas by volume
		const areas = (topAreas.length > 0 ? topAreas : await queryTopDistricts(f, dateStart, dateEnd, 5)).slice(0, 5);
		leaderLabel = 'Top Areas by Transaction Volume';
		leaderHead = `<th>#</th><th>Area</th><th class="r">Transactions</th><th class="r">Median Price</th><th class="r">Median AED/sqft</th>`;
		leaderBody = areas
			.map(
				(r, i) =>
					`<tr><td>${rankSpan(i)}</td><td>${r.district}</td>
          <td class="r">${r.volume.toLocaleString()}</td>
          <td class="r">${formatCurrency(r.medianPrice)}</td>
          <td class="r">${formatRate(r.medianRate)}</td></tr>`
			)
			.join('');
	}

	// ── Fetch all transactions ──
	const allTx = await exportTransactions(f, dateStart, dateEnd);
	const MAX_TX = 300;
	const displayTx = allTx.slice(0, MAX_TX);

	const txNote =
		allTx.length > MAX_TX
			? `<p class="txnote">Showing first ${MAX_TX} of ${allTx.length.toLocaleString()} transactions. Export the full dataset as CSV from adinteract.co.</p>`
			: '';

	const distCol = f.project ? 'Community' : 'District';

	const txBody = displayTx
		.map((tx) => {
			const typeBadge =
				tx.sale_type === 'off-plan'
					? `<span class="bd bop">Off-plan</span>`
					: tx.sale_type === 'ready'
						? `<span class="bd brd">Ready</span>`
						: `<span class="bd">${tx.sale_type ?? ''}</span>`;
			const seqBadge =
				tx.sale_sequence === 'primary'
					? `<span class="bd bpr">Primary</span>`
					: tx.sale_sequence === 'secondary'
						? `<span class="bd bsc">Secondary</span>`
						: '';
			const layout =
				tx.layout && tx.layout !== 'unclassified'
					? tx.layout.charAt(0).toUpperCase() + tx.layout.slice(1)
					: '-';
			const distVal = f.project ? ((tx as Record<string, unknown>).community as string | undefined ?? tx.district) : tx.district;
			return `<tr>
        <td>${formatDate(tx.sale_date)}</td>
        <td>${tx.project_name || 'Private'}</td>
        <td>${distVal || ''}</td>
        <td class="r">${formatCurrency(tx.price_aed)}</td>
        <td class="r">${tx.rate_per_sqft ? Math.round(tx.rate_per_sqft as unknown as number).toLocaleString() : '-'}</td>
        <td>${layout}</td>
        <td class="r">${tx.area_sqft ? Math.round(tx.area_sqft).toLocaleString() : '-'}</td>
        <td class="c">${typeBadge}${seqBadge}</td>
      </tr>`;
		})
		.join('');

	// ── Build HTML ──
	const scope    = scopeLabel(f);
	const period   = periodLabel(f, dateStart, dateEnd);
	const filename = buildFilename(f, dateStart, dateEnd);
	const generated = new Date().toLocaleDateString('en-GB', {
		day: 'numeric',
		month: 'long',
		year: 'numeric'
	});

	// Filters summary chips (shown in sub-header, only non-default filters)
	const filterChips: string[] = [];
	if (f.saleType !== 'all') filterChips.push(f.saleType === 'off-plan' ? 'Off-Plan' : 'Ready');
	if (f.saleSequence !== 'all') filterChips.push(f.saleSequence === 'primary' ? 'Primary' : 'Secondary');
	if (f.propertyTypes.length) filterChips.push(...f.propertyTypes.map((t) => t.charAt(0).toUpperCase() + t.slice(1)));
	if (f.layouts.length) filterChips.push(...f.layouts);
	const filtersLine = filterChips.length
		? `<span style="margin-left:8px">${filterChips.map((c) => `<span class="fchip">${c}</span>`).join(' ')}</span>`
		: '';

	const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>${filename}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,300&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Montserrat',sans-serif;color:#111827;background:#fff;font-size:10.5px;line-height:1.45}
.pg{max-width:830px;margin:0 auto;padding:22px 26px}

/* ── Header ── */
.hdr{display:flex;justify-content:space-between;align-items:center;padding-bottom:14px;border-bottom:2px solid #C8A951;margin-bottom:16px;gap:16px}
.hdright{text-align:right;flex-shrink:0}
.rptitle{font-size:14px;font-weight:800;color:#111827}
.rpscope{font-size:9.5px;color:#6b7280;margin-top:3px}
.gen{font-size:9px;color:#9ca3af;margin-top:4px}
.fchip{display:inline-block;padding:1px 6px;border-radius:8px;font-size:8px;font-weight:600;background:#eff6ff;color:#1d4ed8;margin-left:3px}

/* ── Stats ── */
.sgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:16px}
.sc{background:#f9fafb;border:1px solid #e5e7eb;border-radius:7px;padding:10px 12px}
.slbl{font-size:8px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:.5px;margin-bottom:3px}
.sval{font-size:13px;font-weight:800;color:#111827}
.sg{font-size:8.5px;display:block;margin-top:2px}
.up{color:#16a34a}.dn{color:#dc2626}

/* ── Section ── */
.sec{margin-bottom:16px}
.stitle{font-size:9.5px;font-weight:800;color:#1e4d3a;text-transform:uppercase;letter-spacing:.6px;margin-bottom:7px;padding-bottom:4px;border-bottom:1px solid #e5e7eb}

/* ── Tables ── */
table{width:100%;border-collapse:collapse}
thead tr{background:#f3f4f6}
th{padding:5px 6px;font-size:8px;font-weight:700;text-transform:uppercase;color:#6b7280;letter-spacing:.4px;text-align:left;font-family:'Montserrat',sans-serif}
td{padding:4px 6px;border-bottom:1px solid #f3f4f6;color:#374151;vertical-align:middle;font-family:'Montserrat',sans-serif}
tr:nth-child(even) td{background:#fafafa}
tr:last-child td{border-bottom:none}
.r{text-align:right}.c{text-align:center}

/* ── Rank circles ── */
.rnk{display:inline-flex;align-items:center;justify-content:center;width:17px;height:17px;border-radius:50%;background:#d1d5db;color:#374151;font-size:7.5px;font-weight:700}
.r1{background:#C8A951;color:#fff}
.r2{background:#71717a;color:#fff}
.r3{background:#78350f;color:#fff}

/* ── Badges ── */
.bd{display:inline-block;padding:1.5px 5px;border-radius:8px;font-size:7.5px;font-weight:700;margin:1px}
.bop{background:#eff6ff;color:#1d4ed8}
.brd{background:#f0fdf4;color:#15803d}
.bpr{background:#ecfdf5;color:#065f46}
.bsc{background:#faf5ff;color:#6d28d9}

/* ── Misc ── */
.txnote{font-size:9px;color:#6b7280;margin-bottom:5px}
.ftr{margin-top:18px;padding-top:9px;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between}
.ftxt{font-size:8px;color:#9ca3af}

/* ── Print ── */
@media print{
  body{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  @page{margin:10mm 12mm;size:A4}
  thead{display:table-header-group}
}
</style>
</head>
<body>
<div class="pg">

<!-- Header: official logo + report context -->
<div class="hdr">
  ${LOGO_SVG}
  <div class="hdright">
    <div class="rptitle">${scope}</div>
    <div class="rpscope">${period} &nbsp;·&nbsp; ADREC Transaction Data${filtersLine}</div>
    <div class="gen">Generated ${generated} &nbsp;·&nbsp; adinteract.co</div>
  </div>
</div>

<!-- Stats cards -->
<div class="sgrid">
  <div class="sc">
    <div class="slbl">Transactions</div>
    <div class="sval">${stats.totalVolume.toLocaleString()}</div>
    ${growthBadge(stats.totalVolume, stats.prevTotalVolume)}
  </div>
  <div class="sc">
    <div class="slbl">Median Price</div>
    <div class="sval">${formatCurrency(stats.medianPrice)}</div>
    ${growthBadge(stats.medianPrice, stats.prevMedianPrice)}
  </div>
  <div class="sc">
    <div class="slbl">Median AED / sqft</div>
    <div class="sval">${formatRate(stats.medianRatePerSqft)}</div>
    ${growthBadge(stats.medianRatePerSqft, stats.prevMedianRatePerSqft)}
  </div>
  <div class="sc">
    <div class="slbl">Total Value</div>
    <div class="sval">${formatCurrencyShort(stats.totalValue)} AED</div>
    ${growthBadge(stats.totalValue, stats.prevTotalValue)}
  </div>
</div>

<!-- Leaderboard -->
<div class="sec">
  <div class="stitle">${leaderLabel}</div>
  <table>
    <thead><tr>${leaderHead}</tr></thead>
    <tbody>${leaderBody}</tbody>
  </table>
</div>

<!-- Transactions -->
<div class="sec">
  <div class="stitle">Transactions — ${allTx.length.toLocaleString()} in period</div>
  ${txNote}
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Project</th>
        <th>${distCol}</th>
        <th class="r">Price (AED)</th>
        <th class="r">AED/sqft</th>
        <th>Beds</th>
        <th class="r">Area (sqft)</th>
        <th class="c">Type · Sequence</th>
      </tr>
    </thead>
    <tbody>${txBody}</tbody>
  </table>
</div>

<!-- Footer -->
<div class="ftr">
  <span class="ftxt">Data source: Abu Dhabi Real Estate Centre (ADREC) &nbsp;·&nbsp; adinteract.co</span>
  <span class="ftxt">For informational purposes only. Not financial or investment advice.</span>
</div>

</div>
<script>window.onload = () => { window.print(); }<\/script>
</body>
</html>`;

	const win = window.open('', '_blank', 'width=980,height=760,scrollbars=yes');
	if (!win) {
		alert('Please allow pop-ups for adinteract.co to open the PDF report.');
		return;
	}
	win.document.write(html);
	win.document.close();
}
