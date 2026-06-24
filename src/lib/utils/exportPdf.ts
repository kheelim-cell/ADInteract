/**
 * exportMarketReportPdf
 *
 * Generates a real, shareable PDF file (via pdf-lib) for the current
 * market-report view. Unlike the old window.print() approach — which opened
 * an about:blank popup that wasn't a real file and couldn't be attached to
 * WhatsApp/email — this builds an actual PDF Blob, then:
 *   • On devices that support the Web Share API with files (most mobile
 *     browsers) → opens the native share sheet with the PDF attached.
 *   • Otherwise → downloads the PDF as a normal file the user can attach
 *     manually.
 *
 * Logic:
 *   • Project selected  → leaderboard = Price by Layout
 *   • District selected → leaderboard = Top 5 Projects in that District
 *   • No filter         → leaderboard = Top 5 Areas by Volume
 */

import { PDFDocument, rgb, type PDFFont, type PDFPage, type PDFImage } from 'pdf-lib';
import fontkit from '@pdf-lib/fontkit';
import { base } from '$app/paths';
import type { StatsResult, DistrictSummary, LayoutSummaryRow, FilterState } from '$lib/db/types';
import {
	exportTransactions,
	queryTopProjects,
	queryTopDistricts,
	queryLayoutSummary
} from '$lib/db/queries';
import { formatCurrency, formatRate, formatCurrencyShort, formatDate, growthPercent } from './format';

async function fetchBytes(path: string): Promise<ArrayBuffer> {
	const res = await fetch(`${base}${path}`);
	return res.arrayBuffer();
}

// ─── brand colours ───────────────────────────────────────────────────────────

const BRAND_GOLD   = rgb(0xc8 / 255, 0xa9 / 255, 0x51 / 255);
const BRAND_DARK    = rgb(0x11 / 255, 0x18 / 255, 0x27 / 255);
const GREY_MED      = rgb(0x6b / 255, 0x72 / 255, 0x80 / 255);
const GREY_LIGHT    = rgb(0x9c / 255, 0xa3 / 255, 0xaf / 255);
const GREY_BG       = rgb(0xf9 / 255, 0xfa / 255, 0xfb / 255);
const GREY_BORDER   = rgb(0xe5 / 255, 0xe7 / 255, 0xeb / 255);
const GREEN_UP      = rgb(0x16 / 255, 0xa3 / 255, 0x4a / 255);
const RED_DOWN      = rgb(0xdc / 255, 0x26 / 255, 0x26 / 255);

const PAGE_W = 595.28; // A4 pt
const PAGE_H = 841.89;
const MARGIN = 36;
const CONTENT_W = PAGE_W - MARGIN * 2;

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
		default: return `${fmtDateShort(dateStart)} - ${fmtDateShort(dateEnd)}`;
	}
}

function scopeLabel(f: FilterState): string {
	if (f.project) return f.project;
	if (f.district) return f.district;
	if (f.saleType === 'off-plan') return 'Abu Dhabi - Off-Plan Market';
	if (f.saleType === 'ready') return 'Abu Dhabi - Ready Market';
	return 'Abu Dhabi Property Market';
}

/**
 * Build the PDF filename / title.
 * Format: ADInteract - [District] - [Project] - [Status] - [PropertyType] - [Layout] - [Timeframe]
 * Only active (non-default) filters are included; hyphens separate each field.
 */
function buildFilename(f: FilterState, dateStart: string, dateEnd: string): string {
	const parts: string[] = ['ADInteract'];

	if (f.district) parts.push(f.district);
	if (f.project)  parts.push(f.project);
	if (f.saleType !== 'all') parts.push(f.saleType === 'off-plan' ? 'Off-Plan' : 'Ready');
	if (f.propertyTypes.length) {
		parts.push(f.propertyTypes.map((t) => t.charAt(0).toUpperCase() + t.slice(1)).join('+'));
	}
	if (f.layouts.length) {
		parts.push(f.layouts.map((l) => l.replace(/\s+/g, '')).join('+'));
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

type Row = { cells: string[]; align?: ('l' | 'r' | 'c')[]; rank?: number; badge?: { text: string; up: boolean }[] };

interface TableSpec {
	colWidths: number[]; // proportions, sum to 1
	headers: string[];
	rows: Row[];
}

// ─── layout engine: a tiny paginated table renderer ─────────────────────────

class PdfBuilder {
	doc: PDFDocument;
	font: PDFFont;
	bold: PDFFont;
	page!: PDFPage;
	y = 0;

	constructor(doc: PDFDocument, font: PDFFont, bold: PDFFont) {
		this.doc = doc;
		this.font = font;
		this.bold = bold;
	}

	newPage() {
		this.page = this.doc.addPage([PAGE_W, PAGE_H]);
		this.y = PAGE_H - MARGIN;
	}

	ensureSpace(h: number) {
		if (this.y - h < MARGIN) this.newPage();
	}

	text(str: string, x: number, size: number, opts: { bold?: boolean; color?: ReturnType<typeof rgb>; align?: 'l' | 'r' | 'c'; width?: number } = {}) {
		const f = opts.bold ? this.bold : this.font;
		const w = f.widthOfTextAtSize(str, size);
		let drawX = x;
		if (opts.align === 'r' && opts.width) drawX = x + opts.width - w;
		if (opts.align === 'c' && opts.width) drawX = x + (opts.width - w) / 2;
		this.page.drawText(str, { x: drawX, y: this.y, size, font: f, color: opts.color ?? BRAND_DARK });
	}

	/** Draws text constrained to maxWidth: shrinks font size first, then
	 * truncates with an ellipsis as a last resort — so a long value (a
	 * project name, "Off-plan / Secondary", etc.) never bleeds into the
	 * next column or off the page edge. */
	fitText(str: string, x: number, y: number, maxWidth: number, size: number, opts: { bold?: boolean; color?: ReturnType<typeof rgb>; align?: 'l' | 'r' } = {}) {
		const f = opts.bold ? this.bold : this.font;
		let s = size;
		let w = f.widthOfTextAtSize(str, s);
		const MIN_SIZE = 6;
		while (w > maxWidth && s > MIN_SIZE) {
			s -= 0.5;
			w = f.widthOfTextAtSize(str, s);
		}
		let out = str;
		if (w > maxWidth) {
			while (out.length > 1 && f.widthOfTextAtSize(out + '…', s) > maxWidth) {
				out = out.slice(0, -1);
			}
			out += '…';
			w = f.widthOfTextAtSize(out, s);
		}
		const drawX = opts.align === 'r' ? x + maxWidth - w : x;
		this.page.drawText(out, { x: drawX, y, size: s, font: f, color: opts.color ?? BRAND_DARK });
	}

	rect(x: number, y: number, w: number, h: number, color: ReturnType<typeof rgb>) {
		this.page.drawRectangle({ x, y, width: w, height: h, color });
	}

	line(x1: number, y1: number, x2: number, y2: number, color = GREY_BORDER, thickness = 0.75) {
		this.page.drawLine({ start: { x: x1, y: y1 }, end: { x: x2, y: y2 }, thickness, color });
	}

	table(spec: TableSpec, opts: { title?: string } = {}) {
		const rowH = 16;
		const headH = 16;
		const colXs: number[] = [];
		let acc = MARGIN;
		for (const w of spec.colWidths) {
			colXs.push(acc);
			acc += w * CONTENT_W;
		}

		if (opts.title) {
			this.ensureSpace(28);
			this.text(opts.title.toUpperCase(), MARGIN, 8.5, { bold: true, color: rgb(0x1e / 255, 0x4d / 255, 0x3a / 255) });
			this.y -= 4;
			this.line(MARGIN, this.y, MARGIN + CONTENT_W, this.y, GREY_BORDER, 1);
			this.y -= 10;
		}

		const drawHeader = () => {
			this.rect(MARGIN, this.y - headH + 4, CONTENT_W, headH, GREY_BG);
			spec.headers.forEach((h, i) => {
				const w = spec.colWidths[i] * CONTENT_W;
				this.fitText(h.toUpperCase(), colXs[i] + 5, this.y, w - 10, 7, {
					bold: true,
					color: GREY_MED,
					align: spec.rows[0]?.align?.[i] === 'r' ? 'r' : 'l'
				});
			});
			this.y -= headH;
		};

		this.ensureSpace(headH + rowH);
		drawHeader();

		spec.rows.forEach((row, ri) => {
			this.ensureSpace(rowH);
			if (this.y > PAGE_H - MARGIN - headH - 1 && ri > 0) {
				// just paginated — redraw header on new page
			}
			if (ri % 2 === 1) this.rect(MARGIN, this.y - rowH + 4, CONTENT_W, rowH, GREY_BG);

			row.cells.forEach((cell, ci) => {
				const w = spec.colWidths[ci] * CONTENT_W;
				const align = row.align?.[ci] ?? 'l';
				let x = colXs[ci] + 5;
				if (ci === 0 && row.rank !== undefined) {
					// rank circle
					const cx = colXs[ci] + 9;
					const cy = this.y - rowH / 2 + 5;
					const rankColor = row.rank === 0 ? BRAND_GOLD : row.rank === 1 ? rgb(0.44, 0.44, 0.44) : row.rank === 2 ? rgb(0.47, 0.21, 0.04) : rgb(0.82, 0.84, 0.86);
					this.page.drawCircle({ x: cx, y: cy, size: 7, color: rankColor });
					this.page.drawText(String(row.rank + 1), {
						x: cx - this.font.widthOfTextAtSize(String(row.rank + 1), 6.5) / 2,
						y: cy - 2.3,
						size: 6.5,
						font: this.bold,
						color: row.rank <= 2 ? rgb(1, 1, 1) : rgb(0.22, 0.25, 0.28)
					});
					return;
				}
				this.fitText(cell, x, this.y, w - 10, 8, { color: rgb(0.22, 0.25, 0.28), align: align === 'r' ? 'r' : 'l' });
			});
			this.y -= rowH;
			this.line(MARGIN, this.y + 4, MARGIN + CONTENT_W, this.y + 4, GREY_BORDER, 0.5);
		});

		this.y -= 8;
	}
}

// ─── main export ─────────────────────────────────────────────────────────────

export async function exportMarketReportPdf(opts: {
	filters: FilterState;
	dateStart: string;
	dateEnd: string;
	stats: StatsResult;
	topAreas: DistrictSummary[];
	layoutSummary: LayoutSummaryRow[];
}): Promise<void> {
	const { filters: f, dateStart, dateEnd, stats, topAreas, layoutSummary } = opts;

	// ── Determine leaderboard ──
	let leaderLabel: string;
	let leaderHeaders: string[];
	let leaderRows: Row[];

	if (f.project) {
		const rows: LayoutSummaryRow[] =
			layoutSummary.length > 0 ? layoutSummary : await queryLayoutSummary(f, dateStart, dateEnd);
		leaderLabel = 'Price by Bedroom Type';
		leaderHeaders = ['#', 'Layout', 'Transactions', 'Median Price', 'Median AED/sqft'];
		leaderRows = rows.map((r, i) => ({
			rank: i,
			align: ['l', 'l', 'r', 'r', 'r'],
			cells: ['', r.layout.charAt(0).toUpperCase() + r.layout.slice(1), r.count.toLocaleString(), formatCurrency(r.medianPrice), formatRate(r.medianRate)]
		}));
	} else if (f.district) {
		const projects = await queryTopProjects(f, dateStart, dateEnd, 5);
		leaderLabel = `Top Projects - ${f.district}`;
		leaderHeaders = ['#', 'Project', 'Transactions', 'Median Price', 'Median AED/sqft'];
		leaderRows = projects.map((r, i) => ({
			rank: i,
			align: ['l', 'l', 'r', 'r', 'r'],
			cells: ['', r.district, r.volume.toLocaleString(), formatCurrency(r.medianPrice), formatRate(r.medianRate)]
		}));
	} else {
		const areas = (topAreas.length > 0 ? topAreas : await queryTopDistricts(f, dateStart, dateEnd, 5)).slice(0, 5);
		leaderLabel = 'Top Areas by Transaction Volume';
		leaderHeaders = ['#', 'Area', 'Transactions', 'Median Price', 'Median AED/sqft'];
		leaderRows = areas.map((r, i) => ({
			rank: i,
			align: ['l', 'l', 'r', 'r', 'r'],
			cells: ['', r.district, r.volume.toLocaleString(), formatCurrency(r.medianPrice), formatRate(r.medianRate)]
		}));
	}

	// ── Fetch all transactions ──
	const allTx = await exportTransactions(f, dateStart, dateEnd);
	const MAX_TX = 300;
	const displayTx = allTx.slice(0, MAX_TX);
	const distCol = f.project ? 'Community' : 'District';

	const txHeaders = ['Date', 'Project', distCol, 'Price (AED)', 'AED/sqft', 'Beds', 'Sqft', 'Type'];
	const txRows: Row[] = displayTx.map((tx) => {
		const layout = tx.layout && tx.layout !== 'unclassified' ? tx.layout.charAt(0).toUpperCase() + tx.layout.slice(1) : '-';
		const distVal = f.project ? ((tx as Record<string, unknown>).community as string | undefined ?? tx.district) : tx.district;
		const typeStr = `${tx.sale_type === 'off-plan' ? 'Off-plan' : tx.sale_type === 'ready' ? 'Ready' : (tx.sale_type ?? '')}${tx.sale_sequence ? ' / ' + (tx.sale_sequence === 'primary' ? 'Primary' : 'Secondary') : ''}`;
		return {
			align: ['l', 'l', 'l', 'r', 'r', 'l', 'r', 'l'],
			cells: [
				formatDate(tx.sale_date),
				tx.project_name || 'Private',
				distVal || '',
				formatCurrency(tx.price_aed),
				tx.rate_per_sqft ? Math.round(tx.rate_per_sqft as unknown as number).toLocaleString() : '-',
				layout,
				tx.area_sqft ? Math.round(tx.area_sqft).toLocaleString() : '-',
				typeStr
			]
		};
	});

	// ── Build PDF ──
	const scope = scopeLabel(f);
	const period = periodLabel(f, dateStart, dateEnd);
	const filename = buildFilename(f, dateStart, dateEnd);
	const generated = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });

	const pdfDoc = await PDFDocument.create();
	pdfDoc.setTitle(filename);
	pdfDoc.setProducer('ADInteract.co');
	pdfDoc.registerFontkit(fontkit);

	const [regularBytes, boldBytes, logoBytes] = await Promise.all([
		fetchBytes('/fonts/Montserrat-Regular.ttf'),
		fetchBytes('/fonts/Montserrat-Bold.ttf'),
		fetchBytes('/branding/logo-horizontal-dark.png')
	]);
	const font = await pdfDoc.embedFont(regularBytes, { subset: true });
	const bold = await pdfDoc.embedFont(boldBytes, { subset: true });
	const logo: PDFImage = await pdfDoc.embedPng(logoBytes);

	const builder = new PdfBuilder(pdfDoc, font, bold);
	builder.newPage();

	// Header — logo banner on the left, scope/period/generated block on the right,
	// vertically sized to whichever side is taller so neither overlaps what follows.
	const logoH = 44;
	const logoW = logoH * (logo.width / logo.height);
	builder.page.drawImage(logo, { x: MARGIN, y: builder.y - logoH, width: logoW, height: logoH });

	const rightX = MARGIN + CONTENT_W;
	let ry = builder.y - 11;
	const drawRight = (str: string, size: number, color = BRAND_DARK, bold_ = false) => {
		const f2 = bold_ ? bold : font;
		builder.fitText(str, MARGIN + logoW + 12, ry, CONTENT_W - logoW - 12, size, { bold: bold_, color, align: 'r' });
		ry -= size + 5;
	};
	drawRight(scope, 12, BRAND_DARK, true);
	drawRight(`${period}  -  ADREC Transaction Data`, 8, GREY_MED);
	drawRight(`Generated ${generated}  -  adinteract.co`, 7, GREY_LIGHT);

	const rightBlockBottom = ry + 5; // undo the last decrement to get the true bottom
	builder.y = Math.min(builder.y - logoH, rightBlockBottom) - 10;
	builder.line(MARGIN, builder.y, MARGIN + CONTENT_W, builder.y, BRAND_GOLD, 1.5);
	builder.y -= 18;

	// Stats grid
	const statBoxW = CONTENT_W / 4 - 6;
	const statDefs: { label: string; value: string; cur: number; prev: number }[] = [
		{ label: 'Transactions', value: stats.totalVolume.toLocaleString(), cur: stats.totalVolume, prev: stats.prevTotalVolume },
		{ label: 'Median Price', value: formatCurrency(stats.medianPrice), cur: stats.medianPrice, prev: stats.prevMedianPrice },
		{ label: 'Median AED/sqft', value: formatRate(stats.medianRatePerSqft), cur: stats.medianRatePerSqft, prev: stats.prevMedianRatePerSqft },
		{ label: 'Total Value', value: `${formatCurrencyShort(stats.totalValue)} AED`, cur: stats.totalValue, prev: stats.prevTotalValue }
	];
	const statBoxH = 46;
	statDefs.forEach((s, i) => {
		const x = MARGIN + i * (statBoxW + 8);
		builder.rect(x, builder.y - statBoxH + 12, statBoxW, statBoxH, GREY_BG);
		builder.page.drawRectangle({ x, y: builder.y - statBoxH + 12, width: statBoxW, height: statBoxH, borderColor: GREY_BORDER, borderWidth: 0.75, color: GREY_BG });
		builder.page.drawText(s.label.toUpperCase(), { x: x + 8, y: builder.y, size: 6.5, font: bold, color: GREY_LIGHT });
		builder.page.drawText(s.value, { x: x + 8, y: builder.y - 16, size: 12, font: bold, color: BRAND_DARK });
		const pct = growthPercent(s.cur, s.prev);
		if (pct != null) {
			const up = pct >= 0;
			builder.page.drawText(`${up ? '+' : '-'} ${Math.abs(pct).toFixed(1)}%`, {
				x: x + 8, y: builder.y - 28, size: 7, font, color: up ? GREEN_UP : RED_DOWN
			});
		}
	});
	builder.y -= statBoxH + 14;

	// Leaderboard
	builder.table(
		{ colWidths: [0.06, 0.34, 0.20, 0.20, 0.20], headers: leaderHeaders, rows: leaderRows },
		{ title: leaderLabel }
	);

	// Transactions
	const txNote = allTx.length > MAX_TX
		? `Showing first ${MAX_TX} of ${allTx.length.toLocaleString()} transactions. Export the full dataset as CSV from adinteract.co.`
		: '';
	builder.ensureSpace(24);
	builder.text(`TRANSACTIONS - ${allTx.length.toLocaleString()} IN PERIOD`, MARGIN, 8.5, { bold: true, color: rgb(0x1e / 255, 0x4d / 255, 0x3a / 255) });
	builder.y -= 4;
	builder.line(MARGIN, builder.y, MARGIN + CONTENT_W, builder.y, GREY_BORDER, 1);
	builder.y -= 10;
	if (txNote) {
		builder.text(txNote, MARGIN, 7.5, { color: GREY_MED });
		builder.y -= 12;
	}
	builder.table({
		colWidths: [0.10, 0.18, 0.13, 0.13, 0.09, 0.08, 0.09, 0.20],
		headers: txHeaders,
		rows: txRows
	});

	// Footer on last page
	builder.ensureSpace(20);
	builder.line(MARGIN, builder.y, MARGIN + CONTENT_W, builder.y, GREY_BORDER, 0.75);
	builder.y -= 12;
	builder.text('Data source: Abu Dhabi Real Estate Centre (ADREC) - adinteract.co', MARGIN, 7, { color: GREY_LIGHT });
	builder.text('For informational purposes only. Not financial or investment advice.', MARGIN + CONTENT_W, 7, { color: GREY_LIGHT, align: 'r', width: 0 });

	const bytes = await pdfDoc.save();
	const blob = new Blob([bytes], { type: 'application/pdf' });
	const fileName = `${filename}.pdf`;
	const file = new File([blob], fileName, { type: 'application/pdf' });

	// Prefer native share sheet (lets the user pick WhatsApp directly with a real
	// attached file) when the browser supports sharing files; otherwise download.
	const nav = navigator as Navigator & { canShare?: (data?: { files?: File[] }) => boolean; share?: (data: ShareData) => Promise<void> };
	if (nav.canShare && nav.canShare({ files: [file] }) && nav.share) {
		try {
			await nav.share({ files: [file], title: filename });
			return;
		} catch (err) {
			// User cancelled the share sheet, or share failed — fall through to download.
			if ((err as Error)?.name === 'AbortError') return;
		}
	}

	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = fileName;
	document.body.appendChild(a);
	a.click();
	a.remove();
	setTimeout(() => URL.revokeObjectURL(url), 10_000);
}
