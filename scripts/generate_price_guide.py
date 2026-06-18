"""
generate_price_guide.py
-----------------------
Generates static/data/price-guide-2026.pdf — the ADInteract lead magnet.

Structure (10 pages):
  1  Cover
  2  YTD Abu Dhabi Market Overview
  3-8  Top 6 district highlights (1 per page)
  9  District Investment Rankings — Top 10 table
  10 Investment Score deep-dive — factor breakdown

Run:
    python scripts/generate_price_guide.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parent.parent
PARQUET       = ROOT / "static/data/transactions.parquet"
SCORES_JSON   = ROOT / "src/lib/data/district_scores.json"
LOGO_DARK_BG  = Path(r"C:\Users\KheeXuanLim\Downloads\ADInteract Logos\Horizontal White Logo.png")
LOGO_LIGHT_BG = Path(r"C:\Users\KheeXuanLim\Downloads\ADInteract Logos\Horizontal Dark Logo.png")
ICON_LOGO     = Path(r"C:\Users\KheeXuanLim\Downloads\ADInteract Logos\Logo icon.png")
OUTPUT        = ROOT / "static/data/price-guide-2026.pdf"

# ── Brand colours ────────────────────────────────────────────────────────────
GREEN_DARK  = colors.HexColor("#1B3A2D")
GREEN_MID   = colors.HexColor("#2D5A42")
GOLD        = colors.HexColor("#C9A84C")
GOLD_LIGHT  = colors.HexColor("#E8D08A")
OFF_WHITE   = colors.HexColor("#F7F4EE")
WHITE       = colors.white
GRAY_LIGHT  = colors.HexColor("#E8E4DC")
GRAY_MID    = colors.HexColor("#888880")
GRAY_DARK   = colors.HexColor("#333330")
EMERALD     = colors.HexColor("#16A34A")
BLUE        = colors.HexColor("#2563EB")
AMBER       = colors.HexColor("#D97706")

W, H = A4   # 595.27 x 841.89 pts
M    = 20 * mm  # margin

TOP_6 = [
    "Al Reem Island",
    "Yas Island",
    "Al Saadiyat Island",
    "Al Reef",
    "Khalifa City",
    "Zayed City",
]

# ── Helpers ──────────────────────────────────────────────────────────────────

def fmt_num(n, decimals=0):
    if n is None:
        return "—"
    if decimals:
        return f"{n:,.{decimals}f}"
    return f"{int(round(n)):,}"


def score_type_label(t):
    if t == "yield_stability":    return ("Yield & Stability",    EMERALD)
    if t == "growth_early_cycle": return ("Growth & Early-Cycle", BLUE)
    if t == "both":               return ("Dual market",          colors.HexColor("#7C3AED"))
    return ("—", GRAY_MID)


def draw_logo(c, x, y, width, dark_bg=True):
    logo = LOGO_DARK_BG if dark_bg else LOGO_LIGHT_BG
    if logo.exists():
        aspect = 4.2   # approx width/height ratio of horizontal logo
        c.drawImage(str(logo), x, y, width=width, height=width / aspect,
                    preserveAspectRatio=True, mask="auto")


def header_bar(c, text, y_top, dark=True):
    """Full-width coloured section header."""
    bar_h = 8 * mm
    fill  = GREEN_DARK if dark else OFF_WHITE
    c.setFillColor(fill)
    c.rect(0, y_top - bar_h, W, bar_h, fill=1, stroke=0)
    c.setFillColor(GOLD if dark else GREEN_DARK)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(M, y_top - bar_h + 2.5 * mm, text.upper())
    return y_top - bar_h


def stat_box(c, x, y, w, h, label, value, sub=None, accent=GOLD):
    """Single KPI tile."""
    c.setFillColor(OFF_WHITE)
    c.roundRect(x, y, w, h, 3 * mm, fill=1, stroke=0)
    c.setFillColor(GRAY_MID)
    c.setFont("Helvetica", 7)
    c.drawString(x + 4 * mm, y + h - 5 * mm, label.upper())
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(x + 4 * mm, y + h * 0.38, value)
    if sub:
        c.setFillColor(GRAY_MID)
        c.setFont("Helvetica", 7)
        c.drawString(x + 4 * mm, y + 3 * mm, sub)


def mini_bar_chart(c, x, y, w, h, data, label_color=GRAY_DARK, bar_color=GREEN_MID):
    """Simple bar chart. data = list of (label, value)."""
    if not data:
        return
    max_v = max(v for _, v in data) or 1
    bar_w = (w - 4 * mm) / len(data)
    for i, (lbl, val) in enumerate(data):
        bx = x + i * bar_w + 1 * mm
        bh = (val / max_v) * (h - 10 * mm)
        c.setFillColor(bar_color)
        c.rect(bx, y + 8 * mm, bar_w - 1.5 * mm, bh, fill=1, stroke=0)
        c.setFillColor(label_color)
        c.setFont("Helvetica", 5.5)
        lbl_short = lbl[-7:] if len(lbl) > 7 else lbl
        c.drawCentredString(bx + (bar_w - 1.5 * mm) / 2, y + 3 * mm, lbl_short)
        c.setFont("Helvetica-Bold", 5.5)
        c.drawCentredString(bx + (bar_w - 1.5 * mm) / 2, y + 8 * mm + bh + 1 * mm,
                            fmt_num(val))


def line_chart(c, x, y, w, h, data, line_color=GOLD):
    """Simple sparkline. data = list of values."""
    if len(data) < 2:
        return
    pad = 6 * mm
    min_v, max_v = min(data), max(data)
    rng = max_v - min_v or 1
    pts = []
    for i, v in enumerate(data):
        px = x + pad + i * (w - 2 * pad) / (len(data) - 1)
        py = y + pad + (v - min_v) / rng * (h - 2 * pad)
        pts.append((px, py))
    # shaded area under line
    path = c.beginPath()
    path.moveTo(pts[0][0], y + pad)
    for px, py in pts:
        path.lineTo(px, py)
    path.lineTo(pts[-1][0], y + pad)
    path.close()
    c.setFillColor(line_color.clone() if hasattr(line_color, 'clone') else line_color,
                   alpha=0.12)
    c.drawPath(path, fill=1, stroke=0)
    # line
    c.setStrokeColor(line_color)
    c.setLineWidth(1.5)
    p = c.beginPath()
    p.moveTo(*pts[0])
    for px, py in pts[1:]:
        p.lineTo(px, py)
    c.drawPath(p, fill=0, stroke=1)
    # dots
    c.setFillColor(line_color)
    for px, py in pts:
        c.circle(px, py, 2, fill=1, stroke=0)


def score_bar(c, x, y, w, h, score, fill_color):
    c.setFillColor(GRAY_LIGHT)
    c.roundRect(x, y, w, h, h / 2, fill=1, stroke=0)
    c.setFillColor(fill_color)
    c.roundRect(x, y, max(w * score / 100, h), h, h / 2, fill=1, stroke=0)


def page_footer(c, page_num):
    c.setFillColor(GREEN_DARK)
    c.rect(0, 0, W, 12 * mm, fill=1, stroke=0)
    draw_logo(c, M, 2 * mm, 28 * mm, dark_bg=True)
    c.setFillColor(GRAY_MID)
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(W / 2, 4.5 * mm,
        "Source: Abu Dhabi Real Estate Centre (ADREC) · dari.ae · ADInteract.co is independent of any developer or brokerage")
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 7)
    c.drawRightString(W - M, 4.5 * mm, f"{page_num}")


# ── Page builders ─────────────────────────────────────────────────────────────

def page_cover(c):
    c.setFillColor(GREEN_DARK)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Gold accent bar
    c.setFillColor(GOLD)
    c.rect(0, H * 0.55, W, 2, fill=1, stroke=0)

    # Logo top-left
    draw_logo(c, M, H - 25 * mm, 55 * mm, dark_bg=True)

    # Year badge
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 90)
    c.setFillColor(GOLD)
    c.drawString(M, H * 0.58, "2026")

    # Title
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(M, H * 0.55 - 12 * mm, "ABU DHABI PROPERTY")
    c.setFont("Helvetica-Bold", 22)
    c.drawString(M, H * 0.55 - 22 * mm, "PRICE GUIDE")

    # Subtitle
    c.setFillColor(GOLD_LIGHT)
    c.setFont("Helvetica", 11)
    c.drawString(M, H * 0.55 - 34 * mm, "District prices · Investment scores · Off-plan trends")

    # Credentials
    y_cred = H * 0.25
    for line, bold in [
        ("Official ADREC transaction data", False),
        ("Updated daily  ·  Free  ·  Independent", False),
    ]:
        c.setFillColor(GRAY_LIGHT)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 9)
        c.drawString(M, y_cred, line)
        y_cred -= 6 * mm

    # Bottom accent strip
    c.setFillColor(GOLD)
    c.rect(0, 12 * mm, W, 1.5, fill=1, stroke=0)

    # Footer
    c.setFillColor(GRAY_MID)
    c.setFont("Helvetica", 7)
    c.drawString(M, 5 * mm, "adinteract.co")
    c.drawRightString(W - M, 5 * mm, f"Generated {datetime.now().strftime('%B %Y')}")


def page_market_overview(c, df):
    c.setFillColor(OFF_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Dark header
    c.setFillColor(GREEN_DARK)
    c.rect(0, H - 28 * mm, W, 28 * mm, fill=1, stroke=0)
    draw_logo(c, M, H - 22 * mm, 40 * mm, dark_bg=True)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 16)
    c.drawRightString(W - M, H - 16 * mm, "ABU DHABI MARKET OVERVIEW")
    c.setFillColor(GOLD)
    c.setFont("Helvetica", 9)
    c.drawRightString(W - M, H - 23 * mm, f"Year to Date 2026  ·  January – {datetime.now().strftime('%B %Y')}")

    df["sale_date"] = pd.to_datetime(df["sale_date"])
    ytd26 = df[df["sale_date"].dt.year == 2026]
    ytd25 = df[(df["sale_date"].dt.year == 2025) & (df["sale_date"].dt.month <= datetime.now().month)]

    def pct(a, b): return f"+{round((a-b)/b*100)}%" if b else "—"

    # ── KPI row ──────────────────────────────────────────────────────────────
    y_kpi = H - 28 * mm - 4 * mm - 28 * mm
    kpi_w = (W - 2 * M - 3 * 3 * mm) / 4
    kpis = [
        ("Transactions YTD", fmt_num(len(ytd26)),
         f"vs {fmt_num(len(ytd25))} same period 2025  ({pct(len(ytd26), len(ytd25))})"),
        ("Median AED/sqft", f"AED {fmt_num(ytd26['rate_per_sqft'].median())}",
         f"vs AED {fmt_num(ytd25['rate_per_sqft'].median())} in 2025  ({pct(ytd26['rate_per_sqft'].median(), ytd25['rate_per_sqft'].median())})"),
        ("Median sale price", f"AED {fmt_num(ytd26['price_aed'].median()/1e6, 1)}M",
         f"vs AED {fmt_num(ytd25['price_aed'].median()/1e6, 1)}M in 2025"),
        ("Total sales value", f"AED {fmt_num(ytd26['price_aed'].sum()/1e9, 1)}B",
         f"vs AED {fmt_num(ytd25['price_aed'].sum()/1e9, 1)}B in 2025  ({pct(ytd26['price_aed'].sum(), ytd25['price_aed'].sum())})"),
    ]
    for i, (lbl, val, sub) in enumerate(kpis):
        bx = M + i * (kpi_w + 3 * mm)
        stat_box(c, bx, y_kpi, kpi_w, 28 * mm, lbl, val, sub)

    # ── Off-plan vs Ready / Primary vs Secondary ──────────────────────────────
    y_split = y_kpi - 4 * mm - 22 * mm
    split_w = (W - 2 * M - 3 * mm) / 2

    for col_i, (title, grp_col, color_a, color_b) in enumerate([
        ("Off-Plan vs Ready",    "sale_type",     GREEN_MID,  GOLD),
        ("Primary vs Secondary", "sale_sequence", GREEN_DARK, GOLD_LIGHT),
    ]):
        bx = M + col_i * (split_w + 3 * mm)
        c.setFillColor(WHITE)
        c.roundRect(bx, y_split, split_w, 22 * mm, 3 * mm, fill=1, stroke=0)
        c.setFillColor(GRAY_MID)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(bx + 4 * mm, y_split + 17 * mm, title.upper())

        counts = ytd26[grp_col].value_counts()
        total  = counts.sum()
        pairs  = [(k, v) for k, v in counts.items() if k not in ("unknown", "court-mandated")][:2]
        bar_total_w = split_w - 8 * mm
        x_seg = bx + 4 * mm
        for seg_i, (lbl, cnt) in enumerate(pairs):
            seg_w = (cnt / total) * bar_total_w
            c.setFillColor(color_a if seg_i == 0 else color_b)
            c.roundRect(x_seg, y_split + 9 * mm, seg_w - 0.5, 5 * mm, 1.5 * mm, fill=1, stroke=0)
            x_seg += seg_w
        # labels
        x_lbl = bx + 4 * mm
        for seg_i, (lbl, cnt) in enumerate(pairs):
            pct_v = cnt / total * 100
            c.setFillColor(color_a if seg_i == 0 else color_b)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(x_lbl, y_split + 3.5 * mm, f"{lbl.capitalize()}  {pct_v:.0f}%")
            x_lbl += (split_w - 8 * mm) * (cnt / total)

    # ── Monthly transaction volume (bar chart) ────────────────────────────────
    y_chart = y_split - 4 * mm - 58 * mm
    c.setFillColor(WHITE)
    c.roundRect(M, y_chart, W - 2 * M, 58 * mm, 3 * mm, fill=1, stroke=0)
    header_bar(c, "Monthly Transaction Volume — 2025 / 2026", y_chart + 58 * mm, dark=False)

    monthly = (
        df[df["sale_date"] >= "2025-01-01"]
        .assign(month=df["sale_date"].dt.to_period("M"))
        .groupby("month")
        .size()
        .tail(18)
    )
    chart_data = [(str(p)[-5:], v) for p, v in monthly.items()]
    mini_bar_chart(c, M + 3 * mm, y_chart, W - 2 * M - 6 * mm, 58 * mm,
                   chart_data, bar_color=GREEN_MID)

    # ── Top 8 districts by YTD volume ────────────────────────────────────────
    y_dist = y_chart - 4 * mm - 58 * mm
    c.setFillColor(WHITE)
    c.roundRect(M, y_dist, W - 2 * M, 58 * mm, 3 * mm, fill=1, stroke=0)
    header_bar(c, "Top Districts by Transaction Volume YTD 2026", y_dist + 58 * mm, dark=False)

    top_d = ytd26.groupby("district").size().sort_values(ascending=False).head(8)
    dist_data = [(d[:14], v) for d, v in top_d.items()]
    mini_bar_chart(c, M + 3 * mm, y_dist, W - 2 * M - 6 * mm, 58 * mm,
                   dist_data, bar_color=GOLD)

    page_footer(c, 2)


def page_district(c, df, district_name, page_num, scores):
    c.setFillColor(OFF_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    sub = df[df["district"] == district_name].copy()
    sub["sale_date"] = pd.to_datetime(sub["sale_date"])
    last12 = sub[sub["sale_date"] >= sub["sale_date"].max() - pd.DateOffset(months=12)]

    # Quarterly PSF trend
    sub["q"] = sub["sale_date"].dt.to_period("Q")
    qtly_psf = sub.groupby("q")["rate_per_sqft"].median().tail(8)
    qtly_vol = sub.groupby("q").size().tail(8)

    # Score info
    score_entry = scores.get(district_name)
    score_val   = score_entry["score"] if score_entry else None
    score_type  = score_entry.get("score_type") if score_entry else None
    st_label, st_color = score_type_label(score_type)

    # ── Header ────────────────────────────────────────────────────────────────
    c.setFillColor(GREEN_DARK)
    c.rect(0, H - 28 * mm, W, 28 * mm, fill=1, stroke=0)
    draw_logo(c, M, H - 22 * mm, 38 * mm, dark_bg=True)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 17)
    c.drawRightString(W - M, H - 16 * mm, district_name.upper())
    c.setFillColor(GOLD)
    c.setFont("Helvetica", 8.5)
    c.drawRightString(W - M, H - 23 * mm, "District Highlight  ·  ADREC Transaction Data")

    # ── Score badge ──────────────────────────────────────────────────────────
    if score_val is not None:
        bx, by, bw, bh = W - M - 38 * mm, H - 28 * mm - 20 * mm, 38 * mm, 20 * mm
        c.setFillColor(st_color)
        c.roundRect(bx, by, bw, bh, 3 * mm, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(bx + bw / 2, by + bh * 0.48, str(score_val))
        c.setFont("Helvetica", 6.5)
        c.drawCentredString(bx + bw / 2, by + 3 * mm, st_label)

    # ── KPI tiles ────────────────────────────────────────────────────────────
    y_kpi = H - 28 * mm - 5 * mm - 24 * mm
    if score_val is not None:
        y_kpi = H - 28 * mm - 5 * mm - 24 * mm
    kpi_w = (W - 2 * M - (40 * mm if score_val else 0) - 2 * 3 * mm) / 3
    kpis = [
        ("Transactions (12m)",   fmt_num(len(last12)),                      None),
        ("Median AED/sqft",      f"AED {fmt_num(last12['rate_per_sqft'].median())}",   None),
        ("Median sale price",    f"AED {fmt_num(last12['price_aed'].median()/1e6, 1)}M", None),
    ]
    for i, (lbl, val, sub_txt) in enumerate(kpis):
        bx = M + i * (kpi_w + 3 * mm)
        stat_box(c, bx, y_kpi, kpi_w, 24 * mm, lbl, val, sub_txt)

    # ── PSF trend chart ──────────────────────────────────────────────────────
    chart_h = 60 * mm
    y_psf = y_kpi - 4 * mm - chart_h
    c.setFillColor(WHITE)
    c.roundRect(M, y_psf, W - 2 * M, chart_h, 3 * mm, fill=1, stroke=0)
    header_bar(c, "Median AED/sqft — Quarterly Trend", y_psf + chart_h, dark=False)

    psf_vals = list(qtly_psf.values)
    psf_lbls = [str(p)[-6:] for p in qtly_psf.index]
    line_chart(c, M + 4 * mm, y_psf, W - 2 * M - 8 * mm, chart_h - 10 * mm, psf_vals, GOLD)

    # X-axis labels
    if len(psf_lbls) > 1:
        step = (W - 2 * M - 12 * mm) / (len(psf_lbls) - 1)
        for i, lbl in enumerate(psf_lbls):
            c.setFillColor(GRAY_MID)
            c.setFont("Helvetica", 6)
            c.drawCentredString(M + 6 * mm + i * step, y_psf + 2.5 * mm, lbl)

    # ── Volume bar chart ─────────────────────────────────────────────────────
    y_vol = y_psf - 4 * mm - 50 * mm
    c.setFillColor(WHITE)
    c.roundRect(M, y_vol, (W - 2 * M) / 2 - 1.5 * mm, 50 * mm, 3 * mm, fill=1, stroke=0)
    header_bar(c, "Transaction Volume — Quarterly", y_vol + 50 * mm, dark=False)
    vol_data = [(str(p)[-6:], int(v)) for p, v in qtly_vol.items()]
    mini_bar_chart(c, M + 2 * mm, y_vol, (W - 2 * M) / 2 - 2 * mm, 50 * mm,
                   vol_data, bar_color=GREEN_MID)

    # ── Off-plan vs Ready split ───────────────────────────────────────────────
    split_x = M + (W - 2 * M) / 2 + 1.5 * mm
    split_bw = (W - 2 * M) / 2 - 1.5 * mm
    c.setFillColor(WHITE)
    c.roundRect(split_x, y_vol, split_bw, 50 * mm, 3 * mm, fill=1, stroke=0)
    header_bar(c, "Sale Type Mix (12m)", y_vol + 50 * mm, dark=False)

    type_counts = last12["sale_type"].value_counts()
    total_type  = type_counts.sum()
    type_pairs  = [(k, v) for k, v in type_counts.items() if k != "court-mandated"][:2]
    bar_w_sp    = split_bw - 8 * mm
    x_seg       = split_x + 4 * mm
    clrs        = [GREEN_MID, GOLD]
    for seg_i, (lbl, cnt) in enumerate(type_pairs):
        seg_w = (cnt / total_type) * bar_w_sp
        c.setFillColor(clrs[seg_i])
        c.roundRect(x_seg, y_vol + 25 * mm, seg_w - 0.5, 7 * mm, 1.5 * mm, fill=1, stroke=0)
        x_seg += seg_w
    x_lbl = split_x + 4 * mm
    for seg_i, (lbl, cnt) in enumerate(type_pairs):
        pct_v = cnt / total_type * 100
        c.setFillColor(clrs[seg_i])
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x_lbl, y_vol + 17 * mm, f"{lbl.capitalize()}")
        c.setFont("Helvetica-Bold", 13)
        c.drawString(x_lbl, y_vol + 9 * mm, f"{pct_v:.0f}%")
        x_lbl += bar_w_sp * (cnt / total_type)

    # ── Top projects ─────────────────────────────────────────────────────────
    y_proj = y_vol - 4 * mm - 52 * mm
    c.setFillColor(WHITE)
    c.roundRect(M, y_proj, W - 2 * M, 52 * mm, 3 * mm, fill=1, stroke=0)
    header_bar(c, "Top Projects Transacted (12m)", y_proj + 52 * mm, dark=False)

    top_proj = last12.groupby("project_name").agg(
        txns=("price_aed", "count"),
        med_psf=("rate_per_sqft", "median"),
        med_price=("price_aed", "median"),
    ).sort_values("txns", ascending=False).head(5)

    row_h = 7.5 * mm
    y_row = y_proj + 52 * mm - 10 * mm - row_h
    cols  = [M + 3 * mm, M + 3 * mm + 80 * mm, M + 3 * mm + 120 * mm, M + 3 * mm + 155 * mm]
    hdrs  = ["Project", "Transactions", "Median AED/sqft", "Median Price"]
    c.setFillColor(GRAY_MID)
    c.setFont("Helvetica-Bold", 6.5)
    for col_x, hdr in zip(cols, hdrs):
        c.drawString(col_x, y_row + 2 * mm, hdr.upper())
    c.setStrokeColor(GRAY_LIGHT)
    c.setLineWidth(0.5)
    c.line(M + 3 * mm, y_row, W - M - 3 * mm, y_row)

    for r_i, (proj, row) in enumerate(top_proj.iterrows()):
        y_row -= row_h
        if r_i % 2 == 0:
            c.setFillColor(OFF_WHITE)
            c.rect(M + 2 * mm, y_row, W - 2 * M - 4 * mm, row_h, fill=1, stroke=0)
        c.setFillColor(GRAY_DARK)
        c.setFont("Helvetica", 7)
        proj_name = str(proj)[:38] + "…" if len(str(proj)) > 38 else str(proj)
        c.drawString(cols[0], y_row + 2.5 * mm, proj_name)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(cols[1], y_row + 2.5 * mm, fmt_num(row["txns"]))
        c.drawString(cols[2], y_row + 2.5 * mm, f"AED {fmt_num(row['med_psf'])}")
        c.drawString(cols[3], y_row + 2.5 * mm, f"AED {fmt_num(row['med_price']/1e6, 1)}M")

    page_footer(c, page_num)


def page_rankings_table(c, scores, page_num):
    c.setFillColor(OFF_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(GREEN_DARK)
    c.rect(0, H - 28 * mm, W, 28 * mm, fill=1, stroke=0)
    draw_logo(c, M, H - 22 * mm, 38 * mm, dark_bg=True)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 17)
    c.drawRightString(W - M, H - 16 * mm, "DISTRICT INVESTMENT RANKINGS")
    c.setFillColor(GOLD)
    c.setFont("Helvetica", 8.5)
    c.drawRightString(W - M, H - 23 * mm, "Top 10 districts · dual scoring model · exclusive to ADInteract.co")

    # Legend
    y_leg = H - 28 * mm - 8 * mm
    lx = M
    for lbl, col in [("Yield & Stability", EMERALD), ("Growth & Early-Cycle", BLUE), ("Dual market", colors.HexColor("#7C3AED"))]:
        c.setFillColor(col)
        c.circle(lx + 3 * mm, y_leg + 1.5 * mm, 2.5, fill=1, stroke=0)
        c.setFillColor(GRAY_DARK)
        c.setFont("Helvetica", 7)
        c.drawString(lx + 7 * mm, y_leg, lbl)
        lx += 7 * mm + c.stringWidth(lbl, "Helvetica", 7) + 6 * mm

    left = 20 * mm

    # Column header
    y_hdr = H - 28 * mm - 16 * mm
    cols_x = [left, left + 7 * mm, left + 65 * mm, left + 105 * mm, left + 130 * mm,
              left + 155 * mm, left + 175 * mm]
    hdrs   = ["#", "District", "Score type", "Score", "AED/sqft", "Sales 12m", "Off-plan"]
    c.setFillColor(GREEN_DARK)
    c.rect(0, y_hdr - 2 * mm, W, 8 * mm, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 6.5)
    for cx, hdr in zip(cols_x, hdrs):
        c.drawString(cx, y_hdr, hdr.upper())

    ranked = sorted(scores.values(), key=lambda x: x["score"], reverse=True)[:10]
    row_h  = 17 * mm
    y_row  = y_hdr - 2 * mm - row_h

    for i, entry in enumerate(ranked):
        st_label, st_color = score_type_label(entry.get("score_type"))
        score = entry["score"]

        if i % 2 == 0:
            c.setFillColor(WHITE)
            c.rect(0, y_row, W, row_h, fill=1, stroke=0)

        # Rank
        c.setFillColor(GOLD if i < 3 else GRAY_MID)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(cols_x[0], y_row + row_h * 0.55, str(i + 1))

        # District name
        c.setFillColor(GRAY_DARK)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(cols_x[1], y_row + row_h * 0.65, entry["district_name"])

        # Sub-score bars
        ys  = entry.get("ys")
        gec = entry.get("gec")
        bar_y = y_row + 2 * mm
        bar_w = 50 * mm
        if ys:
            score_bar(c, cols_x[1], bar_y + 4 * mm, bar_w, 2.5 * mm, ys["total"], EMERALD)
        if gec:
            score_bar(c, cols_x[1], bar_y, bar_w, 2.5 * mm, gec["total"], BLUE)

        # Score type badge
        badge_w = 32 * mm
        badge_h = 5.5 * mm
        c.setFillColor(st_color)
        c.roundRect(cols_x[2], y_row + row_h * 0.35, badge_w, badge_h, 1.5 * mm, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(cols_x[2] + badge_w / 2, y_row + row_h * 0.35 + 1.5 * mm, st_label)

        # Score number
        sc_color = EMERALD if score >= 75 else (AMBER if score >= 50 else colors.red)
        c.setFillColor(sc_color)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(cols_x[3], y_row + row_h * 0.4, str(score))

        # Stats
        c.setFillColor(GRAY_DARK)
        c.setFont("Helvetica", 7.5)
        psf = entry.get("median_psf_12m")
        c.drawString(cols_x[4], y_row + row_h * 0.55,
                     f"AED {fmt_num(psf)}" if psf else "—")
        c.drawString(cols_x[5], y_row + row_h * 0.55, fmt_num(entry.get("tx_count_12m")))
        c.drawString(cols_x[6], y_row + row_h * 0.55, f"{entry.get('offplan_pct', '—')}%")

        y_row -= row_h

    page_footer(c, page_num)


def page_score_breakdown(c, scores, page_num):
    c.setFillColor(OFF_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(GREEN_DARK)
    c.rect(0, H - 28 * mm, W, 28 * mm, fill=1, stroke=0)
    draw_logo(c, M, H - 22 * mm, 38 * mm, dark_bg=True)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 17)
    c.drawRightString(W - M, H - 16 * mm, "INVESTMENT SCORE DEEP-DIVE")
    c.setFillColor(GOLD)
    c.setFont("Helvetica", 8.5)
    c.drawRightString(W - M, H - 23 * mm, "Factor breakdown per district · exclusive to ADInteract.co")

    ranked = sorted(scores.values(), key=lambda x: x["score"], reverse=True)[:10]

    # Two-column factor breakdown grid
    col_w = (W - 2 * M - 3 * mm) / 2
    row_h = 32 * mm
    y_start = H - 28 * mm - 5 * mm

    for i, entry in enumerate(ranked):
        col = i % 2
        row = i // 2
        bx  = M + col * (col_w + 3 * mm)
        by  = y_start - (row + 1) * row_h - row * 2 * mm

        st_label, st_color = score_type_label(entry.get("score_type"))
        score = entry["score"]
        ys    = entry.get("ys")
        gec   = entry.get("gec")

        # Card background
        c.setFillColor(WHITE)
        c.roundRect(bx, by, col_w, row_h, 2.5 * mm, fill=1, stroke=0)

        # Left accent bar
        c.setFillColor(st_color)
        c.rect(bx, by, 3, row_h, fill=1, stroke=0)

        # District name + score
        c.setFillColor(GRAY_DARK)
        c.setFont("Helvetica-Bold", 8)
        name = entry["district_name"][:22]
        c.drawString(bx + 5 * mm, by + row_h - 6 * mm, name)
        sc_color = EMERALD if score >= 75 else (AMBER if score >= 50 else colors.red)
        c.setFillColor(sc_color)
        c.setFont("Helvetica-Bold", 13)
        c.drawRightString(bx + col_w - 3 * mm, by + row_h - 6 * mm, str(score))

        # Score type label
        c.setFillColor(st_color)
        c.setFont("Helvetica", 6)
        c.drawString(bx + 5 * mm, by + row_h - 11 * mm, st_label)

        # Factor bars
        factors_ys  = [
            ("Momentum",   ys["momentum"]["score"],     30),
            ("Yield",      ys["yield"]["score"],        25),
            ("Liquidity",  ys["liquidity"]["score"],    20),
            ("Stability",  ys["stability"]["score"],    15),
            ("Apprec.",    ys["appreciation"]["score"], 10),
        ] if ys else []
        factors_gec = [
            ("Velocity",   gec["velocity"]["score"],    30),
            ("Momentum",   gec["momentum"]["score"],    25),
            ("Apprec.",    gec["appreciation"]["score"],20),
            ("Developers", gec["developer"]["score"],   15),
            ("Entry",      gec["entry"]["score"],       10),
        ] if gec else []

        factors_to_show = factors_ys or factors_gec
        f_color = EMERALD if ys and not gec else (BLUE if gec and not ys else GOLD)

        y_f = by + row_h - 15 * mm
        f_row_h = (row_h - 17 * mm) / max(len(factors_to_show), 1)
        bar_area_w = col_w - 28 * mm

        for f_lbl, f_score, f_max in factors_to_show:
            y_f -= f_row_h
            c.setFillColor(GRAY_MID)
            c.setFont("Helvetica", 5.5)
            c.drawString(bx + 5 * mm, y_f + 1 * mm, f_lbl)
            # bar background
            c.setFillColor(GRAY_LIGHT)
            c.roundRect(bx + 18 * mm, y_f + 0.5 * mm, bar_area_w, 3 * mm, 1 * mm, fill=1, stroke=0)
            # bar fill
            c.setFillColor(f_color)
            fill_w = max((f_score / f_max) * bar_area_w, 2)
            c.roundRect(bx + 18 * mm, y_f + 0.5 * mm, fill_w, 3 * mm, 1 * mm, fill=1, stroke=0)
            # score label
            c.setFillColor(GRAY_DARK)
            c.setFont("Helvetica-Bold", 5.5)
            c.drawRightString(bx + col_w - 3 * mm, y_f + 1 * mm,
                              f"{f_score}/{f_max}")

        # If "both", show a mini second row for GEC
        if ys and gec:
            c.setFillColor(BLUE)
            c.setFont("Helvetica", 5.5)
            c.drawString(bx + 5 * mm, by + 2 * mm,
                         f"G&EC {gec['total']}  ·  Y&S {ys['total']}")

    page_footer(c, page_num)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== ADInteract Price Guide Generator ===")
    df = pd.read_parquet(PARQUET)
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    scores = json.load(open(SCORES_JSON))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(OUTPUT), pagesize=A4)
    c.setTitle("Abu Dhabi Property Price Guide 2026 — ADInteract.co")
    c.setAuthor("ADInteract.co")
    c.setSubject("Abu Dhabi District Prices, Investment Scores, Off-Plan Trends")

    print("  Page 1: Cover")
    page_cover(c)
    c.showPage()

    print("  Page 2: Market Overview")
    page_market_overview(c, df.copy())
    c.showPage()

    for pg, district in enumerate(TOP_6, start=3):
        print(f"  Page {pg}: {district}")
        page_district(c, df.copy(), district, pg, scores)
        c.showPage()

    print("  Page 9: Investment Rankings Table")
    page_rankings_table(c, scores, 9)
    c.showPage()

    print("  Page 10: Score Deep-Dive")
    page_score_breakdown(c, scores, 10)
    c.showPage()

    c.save()
    size_kb = OUTPUT.stat().st_size // 1024
    print(f"\nOK Generated {OUTPUT}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
