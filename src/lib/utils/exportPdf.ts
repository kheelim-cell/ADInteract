/**
 * exportMarketReportPdf
 *
 * Generates a styled HTML market report and opens it in a new window so the
 * browser's native Save-as-PDF dialog can be used. No server round-trip, no
 * extra npm packages — just a print-optimised HTML template.
 *
 * Logic:
 *   • Project selected  → leaderboard = Price by Layout
 *   • District selected → leaderboard = Top Projects in that District
 *   • No filter         → leaderboard = Top Areas by Volume
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
		// District view: top projects within that district
		const projects = await queryTopProjects(f, dateStart, dateEnd, 10);
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
		// All Abu Dhabi: top areas by volume
		const areas = topAreas.length > 0 ? topAreas : await queryTopDistricts(f, dateStart, dateEnd, 10);
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
	const scope = scopeLabel(f);
	const period = periodLabel(f, dateStart, dateEnd);
	const generated = new Date().toLocaleDateString('en-GB', {
		day: 'numeric',
		month: 'long',
		year: 'numeric'
	});

	// Filters summary line (only show non-default filters)
	const filterChips: string[] = [];
	if (f.saleType !== 'all') filterChips.push(f.saleType === 'off-plan' ? 'Off-Plan' : 'Ready');
	if (f.saleSequence !== 'all') filterChips.push(f.saleSequence === 'primary' ? 'Primary' : 'Secondary');
	if (f.propertyTypes.length) filterChips.push(...f.propertyTypes.map((t) => t.charAt(0).toUpperCase() + t.slice(1)));
	if (f.layouts.length) filterChips.push(...f.layouts);
	const filtersLine = filterChips.length ? `<span style="margin-left:8px">${filterChips.map((c) => `<span class="fchip">${c}</span>`).join(' ')}</span>` : '';

	const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ADInteract — ${scope}</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;color:#111827;background:#fff;font-size:10.5px;line-height:1.45}
.pg{max-width:830px;margin:0 auto;padding:22px 26px}

/* ── Header ── */
.hdr{display:flex;justify-content:space-between;align-items:flex-start;padding-bottom:14px;border-bottom:2.5px solid #1e3a5f;margin-bottom:16px}
.brand{font-size:18px;font-weight:900;color:#1e3a5f;letter-spacing:-0.4px}
.brand em{font-style:normal;color:#e85d04}
.rptitle{font-size:13px;font-weight:700;color:#111827;margin-top:3px}
.rpscope{font-size:9.5px;color:#6b7280;margin-top:2px}
.hdright{text-align:right}
.gen{font-size:9px;color:#9ca3af}
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
.stitle{font-size:9.5px;font-weight:800;color:#1e3a5f;text-transform:uppercase;letter-spacing:.6px;margin-bottom:7px;padding-bottom:4px;border-bottom:1px solid #e5e7eb}

/* ── Tables ── */
table{width:100%;border-collapse:collapse}
thead tr{background:#f3f4f6}
th{padding:5px 6px;font-size:8px;font-weight:700;text-transform:uppercase;color:#6b7280;letter-spacing:.4px;text-align:left}
td{padding:4px 6px;border-bottom:1px solid #f3f4f6;color:#374151;vertical-align:middle}
tr:nth-child(even) td{background:#fafafa}
tr:last-child td{border-bottom:none}
.r{text-align:right}.c{text-align:center}

/* ── Rank circles ── */
.rnk{display:inline-flex;align-items:center;justify-content:center;width:17px;height:17px;border-radius:50%;background:#d1d5db;color:#374151;font-size:7.5px;font-weight:700}
.r1{background:#e85d04;color:#fff}
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

<!-- Header -->
<div class="hdr">
  <div>
    <div class="brand">AD<em>Interact</em></div>
    <div class="rptitle">${scope}</div>
    <div class="rpscope">${period} &nbsp;·&nbsp; ADREC Transaction Data${filtersLine}</div>
  </div>
  <div class="hdright">
    <div class="gen">Generated ${generated}</div>
    <div class="gen" style="margin-top:2px">adinteract.co</div>
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
		// Fallback: create a blob and force-download as HTML (printable)
		alert('Please allow pop-ups for adinteract.co to open the PDF report.');
		return;
	}
	win.document.write(html);
	win.document.close();
}
