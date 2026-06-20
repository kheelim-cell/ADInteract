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
FONT_DIR      = Path(__file__).parent / "data"
SQUARE_LOGO   = FONT_DIR / "square-logo.png"
OG_IMAGE      = FONT_DIR / "og-image.png"
OUTPUT        = ROOT / "static/data/price-guide-2026.pdf"
SS_SALES      = Path(__file__).parent / "data" / "ss_sales.png"
SS_INVESTORS  = Path(__file__).parent / "data" / "ss_investors.png"

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
M    = 10 * mm  # margin (pages 2-11)
M1   = 18 * mm  # margin for cover page only

# ── Fonts ────────────────────────────────────────────────────────────────────
def register_fonts():
    variants = {
        "Montserrat":         "Montserrat-Regular.ttf",
        "Montserrat-Bold":    "Montserrat-Bold.ttf",
        "Montserrat-Semi":    "Montserrat-SemiBold.ttf",
        "Montserrat-Italic":  "Montserrat-Italic.ttf",
    }
    for alias, fname in variants.items():
        fpath = FONT_DIR / fname
        if fpath.exists():
            pdfmetrics.registerFont(TTFont(alias, str(fpath)))
    pdfmetrics.registerFontFamily(
        "Montserrat",
        normal="Montserrat",
        bold="Montserrat-Bold",
        italic="Montserrat-Italic",
    )

_FONTS_REGISTERED = False

def ensure_fonts():
    global _FONTS_REGISTERED
    if not _FONTS_REGISTERED:
        register_fonts()
        _FONTS_REGISTERED = True

def F(bold=False, size=9):
    """Return (font_name, size) tuple."""
    ensure_fonts()
    return ("Montserrat-Bold" if bold else "Montserrat", size)

def set_font(c, bold=False, size=9):
    ensure_fonts()
    c.setFont("Montserrat-Bold" if bold else "Montserrat", size)

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
    if t == "both":               return ("Dual market",          GOLD)
    return ("—", GRAY_MID)


def draw_square_logo(c, x, y, size):
    if SQUARE_LOGO.exists():
        c.drawImage(str(SQUARE_LOGO), x, y, width=size, height=size,
                    preserveAspectRatio=True, mask="auto")

def draw_og_logo(c, x, y_bottom, w):
    """Draw the og-image (1789x937) at given width, bottom-aligned to y_bottom."""
    if OG_IMAGE.exists():
        aspect = 1789 / 937
        h = w / aspect
        c.drawImage(str(OG_IMAGE), x, y_bottom, width=w, height=h,
                    preserveAspectRatio=True, mask="auto")


def header_bar(c, text, y_top, dark=True):
    """Full-width coloured section header."""
    bar_h = 9 * mm
    fill  = GREEN_DARK if dark else OFF_WHITE
    c.setFillColor(fill)
    c.rect(0, y_top - bar_h, W, bar_h, fill=1, stroke=0)
    c.setFillColor(GOLD if dark else GREEN_DARK)
    set_font(c, bold=True, size=10)
    c.drawString(M, y_top - bar_h + 2.5 * mm, text.upper())
    return y_top - bar_h


def stat_box(c, x, y, w, h, label, value, sub=None, accent=GOLD, value_size=26, align="left"):
    """Single KPI tile. align='left'|'right'."""
    c.setFillColor(OFF_WHITE)
    c.roundRect(x, y, w, h, 3 * mm, fill=1, stroke=0)
    c.setFillColor(GRAY_MID)
    set_font(c, bold=True, size=8.5)
    if align == "right":
        c.drawRightString(x + w - 4 * mm, y + h - 8 * mm, label.upper())
    else:
        c.drawString(x + 4 * mm, y + h - 8 * mm, label.upper())
    c.setFillColor(accent)
    set_font(c, bold=True, size=value_size)
    if align == "right":
        c.drawRightString(x + w - 4 * mm, y + h * 0.35, value)
    else:
        c.drawString(x + 4 * mm, y + h * 0.35, value)
    if sub:
        c.setFillColor(GRAY_MID)
        c.setFont("Montserrat-Italic", 6.5)
        if align == "right":
            c.drawRightString(x + w - 4 * mm, y + 3 * mm, sub)
        else:
            c.drawString(x + 4 * mm, y + 3 * mm, sub)


def mini_bar_chart(c, x, y, w, h, data, label_color=GRAY_DARK, bar_color=GREEN_MID):
    """Simple bar chart. data = list of (label, value)."""
    if not data:
        return
    HEADER_H  = 8 * mm   # header_bar height at the top of the box
    LABEL_B   = 10 * mm  # space at bottom for x-axis labels (2 rows)
    VAL_TOP   = 12 * mm  # white space above tallest bar
    max_bar_h = h - HEADER_H - LABEL_B - VAL_TOP
    max_v     = max(v for _, v in data) or 1
    n         = len(data)
    bar_w     = (w - 4 * mm) / n
    # Centre bars: total drawn span = n*bar_w - 1.5mm (no trailing gap)
    x_start   = x + (w - (n * bar_w - 1.5 * mm)) / 2
    bar_base  = y + LABEL_B
    for i, (lbl, val) in enumerate(data):
        bx = x_start + i * bar_w
        bh = (val / max_v) * max_bar_h
        c.setFillColor(bar_color)
        c.rect(bx, bar_base, bar_w - 1.5 * mm, bh, fill=1, stroke=0)
        c.setFillColor(label_color)
        set_font(c, bold=False, size=7.5)
        cx_ = bx + (bar_w - 1.5 * mm) / 2
        # Split into two lines at a space if label is long
        words = lbl.split()
        mid   = len(words) // 2
        if len(words) > 1 and len(lbl) > 8:
            line1 = " ".join(words[:mid])
            line2 = " ".join(words[mid:])
            c.drawCentredString(cx_, y + 6.5 * mm, line1)
            c.drawCentredString(cx_, y + 2.5 * mm, line2)
        else:
            c.drawCentredString(cx_, y + 4 * mm, lbl)
        set_font(c, bold=True, size=7.5)
        c.drawCentredString(bx + (bar_w - 1.5 * mm) / 2, bar_base + bh + 1.5 * mm,
                            fmt_num(val))


def line_chart(c, x, y, w, h, data, line_color=GOLD, show_values=False, value_fmt=None):
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
    path = c.beginPath()
    path.moveTo(pts[0][0], y + pad)
    for px, py in pts:
        path.lineTo(px, py)
    path.lineTo(pts[-1][0], y + pad)
    path.close()
    c.setFillColor(line_color.clone() if hasattr(line_color, 'clone') else line_color,
                   alpha=0.12)
    c.drawPath(path, fill=1, stroke=0)
    c.setStrokeColor(line_color)
    c.setLineWidth(1.5)
    p = c.beginPath()
    p.moveTo(*pts[0])
    for px, py in pts[1:]:
        p.lineTo(px, py)
    c.drawPath(p, fill=0, stroke=1)
    c.setFillColor(line_color)
    for px, py in pts:
        c.circle(px, py, 2, fill=1, stroke=0)
    if show_values:
        fmt = value_fmt or (lambda v: f"{int(v):,}")
        c.setFillColor(GRAY_DARK)
        set_font(c, bold=True, size=8)
        for i, ((px, py), v) in enumerate(zip(pts, data)):
            label = fmt(v)
            # Always above; clamp so labels don't overflow top
            label_y = py + 4.5 * mm
            max_y   = y + h - 3 * mm
            c.drawCentredString(px, min(label_y, max_y), label)


def score_bar(c, x, y, w, h, score, fill_color):
    c.setFillColor(GRAY_LIGHT)
    c.roundRect(x, y, w, h, h / 2, fill=1, stroke=0)
    c.setFillColor(fill_color)
    c.roundRect(x, y, max(w * score / 100, h), h, h / 2, fill=1, stroke=0)


def page_footer(c, page_num):
    c.setFillColor(GREEN_DARK)
    c.rect(0, 0, W, 10 * mm, fill=1, stroke=0)
    c.setFillColor(GRAY_MID)
    set_font(c, bold=False, size=7.5)
    c.drawCentredString(W / 2, 3.5 * mm,
        "Source: Abu Dhabi Real Estate Centre (ADREC)  ·  dari.ae  ·  ADInteract.co is independent of any developer or brokerage")
    c.setFillColor(GOLD)
    set_font(c, bold=True, size=7.5)
    c.drawRightString(W - M, 3.5 * mm, f"{page_num}")


# ── Page builders ─────────────────────────────────────────────────────────────

def page_cover(c):
    c.setFillColor(GREEN_DARK)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Gold accent bar mid-page
    c.setFillColor(GOLD)
    c.rect(0, H * 0.55, W, 2, fill=1, stroke=0)

    # Year
    set_font(c, bold=True, size=90)
    c.setFillColor(GOLD)
    c.drawString(M1, H * 0.58, "2026")

    # Title
    c.setFillColor(WHITE)
    set_font(c, bold=True, size=22)
    c.drawString(M1, H * 0.55 - 12 * mm, "ABU DHABI PROPERTY")
    set_font(c, bold=True, size=22)
    c.drawString(M1, H * 0.55 - 22 * mm, "INVESTOR GUIDE")
    c.setFont("Montserrat-Italic", 18)
    c.setFillColor(GOLD_LIGHT)
    c.drawString(M1, H * 0.55 - 34 * mm, "brought to you by ADInteract.co")

    # Bottom accent strip
    c.setFillColor(GOLD)
    c.rect(0, 12 * mm, W, 1.5, fill=1, stroke=0)

    # Credential lines — just above the gold strip
    cred_bottom = 20 * mm   # bottom of lower text line
    c.setFillColor(GRAY_LIGHT)
    set_font(c, bold=False, size=13.5)
    c.drawString(M1, cred_bottom, "Official ADREC transaction data")
    c.setFillColor(GOLD)
    set_font(c, bold=True, size=13.5)
    c.drawString(M1, cred_bottom + 8 * mm, "ADInteract.co")

    # Logo bottom-right, bottom-aligned with lower text line
    logo_size = 30 * mm
    draw_square_logo(c, W - M1 - logo_size, cred_bottom, logo_size)

    # Generated date bottom-left
    c.setFillColor(GRAY_MID)
    set_font(c, bold=False, size=7.5)
    c.drawString(M1, 5 * mm, f"Generated {datetime.now().strftime('%B %Y')}")


def page_market_overview(c, df):
    c.setFillColor(OFF_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Dark header
    hdr_h = 28 * mm
    c.setFillColor(GREEN_DARK)
    c.rect(0, H - hdr_h, W, hdr_h, fill=1, stroke=0)
    draw_og_logo(c, M, H - 23 * mm, 32 * mm)
    c.setFillColor(WHITE)
    set_font(c, bold=True, size=16)
    c.drawRightString(W - M, H - 16 * mm, "ABU DHABI MARKET OVERVIEW")
    c.setFillColor(GOLD)
    set_font(c, bold=False, size=9)
    c.drawRightString(W - M, H - 23 * mm, f"Year to Date 2026  ·  January – {datetime.now().strftime('%B %Y')}")

    df["sale_date"] = pd.to_datetime(df["sale_date"])
    ytd26 = df[df["sale_date"].dt.year == 2026]
    ytd25 = df[(df["sale_date"].dt.year == 2025) & (df["sale_date"].dt.month <= datetime.now().month)]

    def pct(a, b): return f"+{round((a-b)/b*100)}%" if b else "—"

    # ── KPI row ──────────────────────────────────────────────────────────────
    y_kpi = H - 28 * mm - 5 * mm - 30 * mm
    kpi_w = (W - 2 * M - 3 * 3 * mm) / 4
    kpis = [
        ("Transactions YTD", fmt_num(len(ytd26)),
         f"vs {fmt_num(len(ytd25))} same period 2025  ({pct(len(ytd26), len(ytd25))})"),
        ("Median AED/sqft", f"AED {fmt_num(ytd26['rate_per_sqft'].median())}",
         f"vs AED {fmt_num(ytd25['rate_per_sqft'].median())} in 2025  ({pct(ytd26['rate_per_sqft'].median(), ytd25['rate_per_sqft'].median())})"),
        ("Median sale price", f"AED {fmt_num(ytd26['price_aed'].median()/1e6, 1)}M",
         f"vs AED {fmt_num(ytd25['price_aed'].median()/1e6, 1)}M in 2025"),
        ("Total value", f"AED {fmt_num(ytd26['price_aed'].sum()/1e9, 1)}B",
         f"vs AED {fmt_num(ytd25['price_aed'].sum()/1e9, 1)}B in 2025  ({pct(ytd26['price_aed'].sum(), ytd25['price_aed'].sum())})"),
    ]
    for i, (lbl, val, sub) in enumerate(kpis):
        bx = M + i * (kpi_w + 3 * mm)
        stat_box(c, bx, y_kpi, kpi_w, 30 * mm, lbl, val, sub, value_size=17)

    # ── Off-plan vs Ready / Primary vs Secondary ──────────────────────────────
    y_split = y_kpi - 5 * mm - 24 * mm
    split_w = (W - 2 * M - 3 * mm) / 2

    for col_i, (title, grp_col, color_a, color_b) in enumerate([
        ("Off-Plan vs Ready",    "sale_type",     GREEN_MID,  GOLD),
        ("Primary vs Secondary", "sale_sequence", GREEN_MID,  GOLD),
    ]):
        bx = M + col_i * (split_w + 3 * mm)
        c.setFillColor(WHITE)
        c.roundRect(bx, y_split, split_w, 24 * mm, 3 * mm, fill=1, stroke=0)
        c.setFillColor(GRAY_MID)
        set_font(c, bold=True, size=7.5)
        c.drawString(bx + 4 * mm, y_split + 19 * mm, title.upper())

        counts = ytd26[grp_col].value_counts()
        total  = counts.sum()
        pairs  = [(k, v) for k, v in counts.items() if k not in ("unknown", "court-mandated")][:2]
        bar_total_w = split_w - 8 * mm
        bar_h = 6 * mm
        bar_y = y_split + 11 * mm
        # Continuous bar — no gaps/rounding between segments
        x_seg = bx + 4 * mm
        for seg_i, (lbl, cnt) in enumerate(pairs):
            seg_w = (cnt / total) * bar_total_w
            c.setFillColor(color_a if seg_i == 0 else color_b)
            c.rect(x_seg, bar_y, seg_w, bar_h, fill=1, stroke=0)
            x_seg += seg_w
        # labels
        x_lbl = bx + 4 * mm
        for seg_i, (lbl, cnt) in enumerate(pairs):
            pct_v = cnt / total * 100
            c.setFillColor(color_a if seg_i == 0 else color_b)
            set_font(c, bold=True, size=7.5)
            c.drawString(x_lbl, y_split + 4 * mm, f"{lbl.capitalize()}  {pct_v:.0f}%")
            x_lbl += (split_w - 8 * mm) * (cnt / total)

    # ── Monthly transaction volume (bar chart) ────────────────────────────────
    y_chart = y_split - 5 * mm - 65 * mm
    c.setFillColor(WHITE)
    c.roundRect(M, y_chart, W - 2 * M, 65 * mm, 3 * mm, fill=1, stroke=0)
    header_bar(c, "Monthly Transaction Volume — 2025 / 2026", y_chart + 65 * mm, dark=False)

    monthly = (
        df[df["sale_date"] >= "2025-01-01"]
        .assign(month=df["sale_date"].dt.to_period("M"))
        .groupby("month")
        .size()
        .tail(18)
    )
    MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    def fmt_period(p):
        s = str(p)  # "2025-01"
        yr, mo = s.split("-")
        return f"{MONTH_ABBR[int(mo)-1]}'{yr[2:]}"
    chart_data = [(fmt_period(p), v) for p, v in monthly.items()]
    mini_bar_chart(c, M + 3 * mm, y_chart, W - 2 * M - 6 * mm, 65 * mm,
                   chart_data, bar_color=GREEN_MID)

    # ── Top 8 districts by YTD volume ────────────────────────────────────────
    y_dist_bottom = 16 * mm   # gap above the 10mm footer
    dist_h = y_chart - 5 * mm - y_dist_bottom
    y_dist = y_dist_bottom
    c.setFillColor(WHITE)
    c.roundRect(M, y_dist, W - 2 * M, dist_h, 3 * mm, fill=1, stroke=0)
    header_bar(c, "Top Districts by Transaction Volume YTD 2026", y_dist + dist_h, dark=False)

    top_d = ytd26.groupby("district").size().sort_values(ascending=False).head(8)
    dist_data = [(d, v) for d, v in top_d.items()]
    mini_bar_chart(c, M + 3 * mm, y_dist, W - 2 * M - 6 * mm, dist_h,
                   dist_data, bar_color=GOLD)

    page_footer(c, 2)


def page_district(c, df, district_name, page_num, scores):
    c.setFillColor(OFF_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    sub = df[df["district"] == district_name].copy()
    sub["sale_date"] = pd.to_datetime(sub["sale_date"])
    last12 = sub[sub["sale_date"] >= sub["sale_date"].max() - pd.DateOffset(months=12)]

    sub["q"] = sub["sale_date"].dt.to_period("Q")
    qtly_psf = sub.groupby("q")["rate_per_sqft"].median().tail(8)
    qtly_vol = sub.groupby("q").size().tail(8)

    # ── Header ────────────────────────────────────────────────────────────────
    hdr_h = 28 * mm
    c.setFillColor(GREEN_DARK)
    c.rect(0, H - hdr_h, W, hdr_h, fill=1, stroke=0)
    draw_og_logo(c, M, H - 23 * mm, 32 * mm)
    c.setFillColor(WHITE)
    set_font(c, bold=True, size=17)
    c.drawRightString(W - M, H - 16 * mm, district_name.upper())
    c.setFillColor(GOLD)
    set_font(c, bold=False, size=8.5)
    c.drawRightString(W - M, H - 23 * mm, "District Highlight  ·  ADREC Transaction Data")

    # ── KPI tiles — evenly distributed full width ─────────────────────────────
    y_kpi = H - hdr_h - 6 * mm - 30 * mm
    gap   = 4 * mm
    kpi_w = (W - 2 * M - 2 * gap) / 3
    kpis  = [
        ("Transactions (12m)", fmt_num(len(last12)), None, "left"),
        ("Median AED/sqft",    f"AED {fmt_num(last12['rate_per_sqft'].median())}", None, "left"),
        ("Median sale price",  f"AED {fmt_num(last12['price_aed'].median()/1e6, 1)}M", None, "right"),
    ]
    for i, (lbl, val, sub_txt, align) in enumerate(kpis):
        bx = M + i * (kpi_w + gap)
        stat_box(c, bx, y_kpi, kpi_w, 30 * mm, lbl, val, sub_txt, align=align)

    # ── PSF trend chart ──────────────────────────────────────────────────────
    chart_h = 65 * mm
    y_psf = y_kpi + 2 * mm - chart_h
    c.setFillColor(WHITE)
    c.roundRect(M, y_psf, W - 2 * M, chart_h, 3 * mm, fill=1, stroke=0)
    header_bar(c, "Median AED/sqft — Quarterly Trend", y_psf + chart_h, dark=False)

    psf_vals = list(qtly_psf.values)
    def fmt_quarter(p):
        s = str(p)   # e.g. "2024Q3"
        yr, q = s[:4], s[4:]   # s[4:] = "Q3" not s[5:] = "3"
        return f"{q} '{yr[2:]}"
    psf_lbls = [fmt_quarter(p) for p in qtly_psf.index]
    line_chart(c, M + 4 * mm, y_psf, W - 2 * M - 8 * mm, chart_h - 10 * mm, psf_vals, GOLD,
               show_values=True, value_fmt=lambda v: f"{int(v):,}")

    if len(psf_lbls) > 1:
        step = (W - 2 * M - 12 * mm) / (len(psf_lbls) - 1)
        for i, lbl in enumerate(psf_lbls):
            c.setFillColor(GRAY_MID)
            set_font(c, bold=False, size=7.5)
            c.drawCentredString(M + 6 * mm + i * step, y_psf + 2.5 * mm, lbl)

    # ── Volume bar chart + Off-plan split ─────────────────────────────────────
    lower_h = 55 * mm
    y_vol = y_psf - 5 * mm - lower_h
    half_w = (W - 2 * M - 3 * mm) / 2

    # Volume bars (left)
    c.setFillColor(WHITE)
    c.roundRect(M, y_vol, half_w, lower_h, 3 * mm, fill=1, stroke=0)
    header_bar(c, "Transaction Volume — Quarterly", y_vol + lower_h, dark=False)
    vol_data = [(fmt_quarter(p), int(v)) for p, v in qtly_vol.items()]
    mini_bar_chart(c, M, y_vol, half_w, lower_h, vol_data, bar_color=GREEN_MID)

    # Off-plan / ready (right) — continuous bar
    split_x  = M + half_w + 3 * mm
    c.setFillColor(WHITE)
    c.roundRect(split_x, y_vol, half_w, lower_h, 3 * mm, fill=1, stroke=0)
    header_bar(c, "Off-Plan vs Ready (12m)", y_vol + lower_h, dark=False)

    type_counts = last12["sale_type"].value_counts()
    total_type  = type_counts.sum()
    type_pairs  = [(k, v) for k, v in type_counts.items() if k != "court-mandated"][:2]
    bar_total_w = half_w - 8 * mm   # 4mm margin on each side of the panel
    bar_y_pos   = y_vol + lower_h * 0.48
    x_seg       = split_x + 4 * mm
    clrs        = [GREEN_MID, GOLD]
    for seg_i, (lbl, cnt) in enumerate(type_pairs):
        seg_w = (cnt / total_type) * bar_total_w
        c.setFillColor(clrs[seg_i])
        c.rect(x_seg, bar_y_pos, seg_w, 7 * mm, fill=1, stroke=0)
        x_seg += seg_w
    x_lbl = split_x + 4 * mm
    right_edge = split_x + half_w - 4 * mm   # right margin of the panel
    for seg_i, (lbl, cnt) in enumerate(type_pairs):
        pct_v = cnt / total_type * 100
        c.setFillColor(clrs[seg_i])
        set_font(c, bold=True, size=9)
        if seg_i == 1:
            c.drawRightString(right_edge, bar_y_pos - 9 * mm, f"{lbl.capitalize()}")
        else:
            c.drawString(x_lbl, bar_y_pos - 9 * mm, f"{lbl.capitalize()}")
        set_font(c, bold=True, size=20)
        if seg_i == 1:
            c.drawRightString(right_edge, y_vol + 6 * mm, f"{pct_v:.0f}%")
        else:
            c.drawString(x_lbl, y_vol + 6 * mm, f"{pct_v:.0f}%")
        x_lbl += bar_total_w * (cnt / total_type)

    # ── Top projects ─────────────────────────────────────────────────────────
    row_h_p  = 10 * mm
    n_rows   = 5
    PAD_V    = 6 * mm   # equal top & bottom padding inside box
    hdr_row  = 10 * mm
    proj_h   = 9 * mm + hdr_row + n_rows * row_h_p + PAD_V  # header_bar + col header + rows + bottom pad
    y_proj   = y_vol - 5 * mm - proj_h
    c.setFillColor(WHITE)
    c.roundRect(M, y_proj, W - 2 * M, proj_h, 3 * mm, fill=1, stroke=0)
    header_bar(c, "Top Projects Transacted (12m)", y_proj + proj_h, dark=False)

    top_proj = last12.groupby("project_name").agg(
        txns=("price_aed", "count"),
        med_psf=("rate_per_sqft", "median"),
        med_price=("price_aed", "median"),
    ).sort_values("txns", ascending=False).head(5)

    y_row   = y_proj + proj_h - 9 * mm - hdr_row   # just below header_bar
    # col[0] = project name (left), cols[1-3] = numeric cols (centred)
    cols    = [M + 4*mm, M + 82*mm, M + 120*mm, M + 158*mm]
    hdrs    = ["Project", "Transactions", "Median AED/sqft", "Median Price"]
    c.setFillColor(GRAY_MID)
    set_font(c, bold=True, size=9)
    for i, (col_x, hdr) in enumerate(zip(cols, hdrs)):
        if i == 0:
            c.drawString(col_x, y_row + 3 * mm, hdr.upper())
        else:
            c.drawCentredString(col_x, y_row + 3 * mm, hdr.upper())
    c.setStrokeColor(GRAY_LIGHT)
    c.setLineWidth(0.5)
    c.line(M + 4 * mm, y_row, W - M - 4 * mm, y_row)

    for r_i, (proj, row) in enumerate(top_proj.iterrows()):
        y_row -= row_h_p
        if r_i % 2 == 0:
            c.setFillColor(OFF_WHITE)
            c.rect(M + 2 * mm, y_row, W - 2 * M - 4 * mm, row_h_p, fill=1, stroke=0)
        c.setFillColor(GRAY_DARK)
        set_font(c, bold=True, size=9)
        proj_name = str(proj)[:42] + "…" if len(str(proj)) > 42 else str(proj)
        c.drawString(cols[0], y_row + 3.5 * mm, proj_name)
        set_font(c, bold=True, size=9)
        c.drawCentredString(cols[1], y_row + 3.5 * mm, fmt_num(row["txns"]))
        c.drawCentredString(cols[2], y_row + 3.5 * mm, f"AED {fmt_num(row['med_psf'])}")
        c.drawCentredString(cols[3], y_row + 3.5 * mm, f"AED {fmt_num(row['med_price']/1e6, 1)}M")

    page_footer(c, page_num)


def page_rankings_table(c, scores, page_num):
    c.setFillColor(OFF_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    hdr_h = 28 * mm
    c.setFillColor(GREEN_DARK)
    c.rect(0, H - hdr_h, W, hdr_h, fill=1, stroke=0)
    draw_og_logo(c, M, H - 23 * mm, 32 * mm)
    c.setFillColor(WHITE)
    set_font(c, bold=True, size=17)
    c.drawRightString(W - M, H - 16 * mm, "DISTRICT INVESTMENT RANKINGS")
    c.setFillColor(GOLD)
    set_font(c, bold=False, size=8.5)
    c.drawRightString(W - M, H - 23 * mm, "Top 10 districts · dual scoring model · exclusive to ADInteract.co")

    # Left-anchored cols (0-2) and centre-anchored cols (3-5)
    cols_x  = [M, M + 7*mm, M + 67*mm]                         # #, District, Score type
    col_ctr = [M + 121*mm, M + 152*mm, M + 177*mm]             # Score, AED/sqft, L12M TXN
    hdrs_l  = ["#", "District", "Score type"]
    hdrs_c  = ["Score", "AED/sqft", "L12M TXN"]

    y_hdr   = H - hdr_h - 5 * mm
    hdr_bar = 10 * mm
    c.setFillColor(GREEN_DARK)
    c.rect(0, y_hdr - hdr_bar, W, hdr_bar, fill=1, stroke=0)
    c.setFillColor(GOLD)
    set_font(c, bold=True, size=11)
    for cx, hdr in zip(cols_x, hdrs_l):
        c.drawString(cx, y_hdr - hdr_bar + 3 * mm, hdr.upper())
    for cx, hdr in zip(col_ctr, hdrs_c):
        c.drawCentredString(cx, y_hdr - hdr_bar + 3 * mm, hdr.upper())

    ranked = sorted(scores.values(), key=lambda x: x["score"], reverse=True)[:10]

    # Evenly distribute 10 rows between col-header bottom and footer
    available = y_hdr - hdr_bar - 10 * mm
    row_h     = available / 10
    y_row     = y_hdr - hdr_bar - row_h

    for i, entry in enumerate(ranked):
        st_label, _ = score_type_label(entry.get("score_type"))
        score       = entry["score"]
        stype       = entry.get("score_type", "")

        # Explicit badge colours: green / gold / grey
        if stype == "yield_stability":
            badge_color = GREEN_MID
        elif stype == "growth_early_cycle":
            badge_color = GOLD
        else:
            badge_color = GRAY_MID

        if i % 2 == 0:
            c.setFillColor(WHITE)
            c.rect(0, y_row, W, row_h, fill=1, stroke=0)

        # Shared vertical baselines for optical middle-alignment
        row_mid   = y_row + row_h / 2
        base_12   = row_mid - 2 * mm   # size-12 cap ≈ 4mm → baseline 2mm below mid
        base_18   = row_mid - 3 * mm   # size-18 cap ≈ 6mm → baseline 3mm below mid

        # Rank
        c.setFillColor(GOLD if i < 3 else GRAY_MID)
        set_font(c, bold=True, size=12)
        c.drawString(cols_x[0], base_12, str(i + 1))

        # District name + bars — block centred vertically in row
        # Block: name (4mm cap) + gap(1mm) + bar1(2.5mm) + gap(0.5mm) + bar2(2.5mm) = ~10.5mm
        # Centre: name_y such that mid of block = row mid
        ys  = entry.get("ys")
        gec = entry.get("gec")
        n_bars   = sum(1 for b in [ys, gec] if b)
        bar_h_px = 2.5 * mm
        bar_gap  = 0.5 * mm
        cap_h    = 4 * mm   # approx cap height at size 12
        name_gap = 1 * mm   # gap between name baseline and first bar top
        block_h  = cap_h + name_gap + n_bars * bar_h_px + max(0, n_bars - 1) * bar_gap
        name_y   = y_row + (row_h + block_h) / 2 - cap_h

        c.setFillColor(GRAY_DARK)
        set_font(c, bold=True, size=12)
        c.drawString(cols_x[1], name_y, entry["district_name"])

        # Stack bars immediately below name — no fixed offsets
        bar_w   = 50 * mm
        bar_top = name_y - name_gap - bar_h_px   # top bar bottom edge
        for bar_data, bar_color in [(gec, GOLD), (ys, GREEN_MID)]:
            if bar_data:
                score_bar(c, cols_x[1], bar_top, bar_w, bar_h_px, bar_data["total"], bar_color)
                bar_top -= (bar_h_px + bar_gap)

        # Score type badge — centred in row
        badge_w = 42 * mm
        badge_h = 6 * mm
        badge_y = y_row + (row_h - badge_h) / 2
        c.setFillColor(badge_color)
        c.roundRect(cols_x[2], badge_y, badge_w, badge_h, 1.5 * mm, fill=1, stroke=0)
        # Text: white on green/grey; dark on gold for contrast
        c.setFillColor(GREEN_DARK if badge_color == GOLD else WHITE)
        set_font(c, bold=True, size=9)
        c.drawCentredString(cols_x[2] + badge_w / 2, badge_y + 1.8 * mm, st_label)

        # Score number — black, centred
        c.setFillColor(GRAY_DARK)
        set_font(c, bold=True, size=18)
        c.drawCentredString(col_ctr[0], base_18, str(score))

        # AED/sqft — centred
        set_font(c, bold=False, size=12)
        psf = entry.get("median_psf_12m")
        c.drawCentredString(col_ctr[1], base_12,
                            f"AED {fmt_num(psf)}" if psf else "—")

        # Transactions — centred
        c.drawCentredString(col_ctr[2], base_12,
                            fmt_num(entry.get("tx_count_12m")))

        y_row -= row_h

    page_footer(c, page_num)


def page_score_breakdown(c, scores, page_num):
    c.setFillColor(OFF_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    hdr_h = 28 * mm
    c.setFillColor(GREEN_DARK)
    c.rect(0, H - hdr_h, W, hdr_h, fill=1, stroke=0)
    draw_og_logo(c, M, H - 23 * mm, 32 * mm)
    c.setFillColor(WHITE)
    set_font(c, bold=True, size=17)
    c.drawRightString(W - M, H - 16 * mm, "INVESTMENT SCORE DEEP-DIVE")
    c.setFillColor(GOLD)
    set_font(c, bold=False, size=8.5)
    c.drawRightString(W - M, H - 23 * mm, "Factor breakdown per district · exclusive to ADInteract.co")

    ranked = sorted(scores.values(), key=lambda x: x["score"], reverse=True)[:10]

    GAP_COL = 5 * mm
    GAP_ROW = 3 * mm
    PAD     = 4 * mm
    col_w   = (W - 2 * M - GAP_COL) / 2
    n_rows  = 5
    top     = H - hdr_h - 5 * mm
    bottom  = 10 * mm + 5 * mm
    row_h   = (top - bottom - (n_rows - 1) * GAP_ROW) / n_rows

    for i, entry in enumerate(ranked):
        col  = i % 2
        row  = i // 2
        bx   = M + col * (col_w + GAP_COL)
        by   = top - (row + 1) * row_h - row * GAP_ROW

        stype = entry.get("score_type", "")
        st_label, _ = score_type_label(stype)
        if stype == "yield_stability":
            type_color = GREEN_MID
        elif stype == "growth_early_cycle":
            type_color = GOLD
        else:
            type_color = GRAY_MID

        score = entry["score"]
        ys    = entry.get("ys")
        gec   = entry.get("gec")

        # Card
        c.setFillColor(WHITE)
        c.roundRect(bx, by, col_w, row_h, 2.5 * mm, fill=1, stroke=0)

        # District name + score
        name_y = by + row_h - PAD - 4.5 * mm
        c.setFillColor(GRAY_DARK)
        set_font(c, bold=True, size=13)
        c.drawString(bx + PAD, name_y, entry["district_name"][:26])
        c.drawRightString(bx + col_w - PAD, name_y, str(score))

        # Score type label
        type_y = name_y - 5 * mm
        c.setFillColor(type_color)
        set_font(c, bold=True, size=8)
        c.drawString(bx + PAD, type_y, st_label)

        # Divider
        div_y = type_y - 3 * mm
        c.setStrokeColor(GRAY_LIGHT)
        c.setLineWidth(0.5)
        c.line(bx + PAD, div_y, bx + col_w - PAD, div_y)

        # Factor bars
        factors_ys  = [
            ("Momentum",   ys["momentum"]["score"],     30),
            ("Yield",      ys["yield"]["score"],        25),
            ("Liquidity",  ys["liquidity"]["score"],    20),
            ("Stability",  ys["stability"]["score"],    15),
            ("Appreciation",    ys["appreciation"]["score"], 10),
        ] if ys else []
        factors_gec = [
            ("Velocity",   gec["velocity"]["score"],    30),
            ("Momentum",   gec["momentum"]["score"],    25),
            ("Appreciation",    gec["appreciation"]["score"],20),
            ("Developers", gec["developer"]["score"],   15),
            ("Entry",      gec["entry"]["score"],       10),
        ] if gec else []
        factors  = factors_ys or factors_gec
        bar_clr  = GREEN_MID if (ys and not gec) else GOLD

        lbl_w    = 23 * mm
        score_w  = 11 * mm
        bar_x    = bx + PAD + lbl_w
        bar_area = col_w - 2 * PAD - lbl_w - score_w
        bar_h    = 3.5 * mm

        f_top = div_y - 2 * mm
        f_bot = by + PAD
        f_row = (f_top - f_bot) / max(len(factors), 1)

        for j, (f_lbl, f_score, f_max) in enumerate(factors):
            fy_mid = f_top - (j + 0.5) * f_row
            fy_bar = fy_mid - bar_h / 2

            c.setFillColor(GRAY_MID)
            set_font(c, bold=False, size=8)
            c.drawString(bx + PAD, fy_mid - 1.5 * mm, f_lbl)

            c.setFillColor(GRAY_LIGHT)
            c.roundRect(bar_x, fy_bar, bar_area, bar_h, bar_h / 2, fill=1, stroke=0)
            c.setFillColor(bar_clr)
            fill_w = max((f_score / f_max) * bar_area, bar_h)
            c.roundRect(bar_x, fy_bar, fill_w, bar_h, bar_h / 2, fill=1, stroke=0)

            c.setFillColor(GRAY_DARK)
            set_font(c, bold=True, size=8)
            c.drawRightString(bx + col_w - PAD, fy_mid - 1.5 * mm, f"{f_score}/{f_max}")

    page_footer(c, page_num)


def page_methodology(c, page_num):
    """Investment Score Methodology."""
    from reportlab.lib.utils import simpleSplit

    c.setFillColor(OFF_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    hdr_h = 28 * mm
    c.setFillColor(GREEN_DARK)
    c.rect(0, H - hdr_h, W, hdr_h, fill=1, stroke=0)
    draw_og_logo(c, M, H - 23 * mm, 32 * mm)
    c.setFillColor(WHITE)
    set_font(c, bold=True, size=17)
    c.drawRightString(W - M, H - 16 * mm, "INVESTMENT SCORE METHODOLOGY")
    c.setFillColor(GOLD)
    set_font(c, bold=False, size=8.5)
    c.drawRightString(W - M, H - 23 * mm, "How districts are classified and scored · ADInteract.co")

    # ── Constants ─────────────────────────────────────────────────────────────
    FONT_S    = 8.5        # body / description font size
    LINE_H    = 4.2 * mm   # line height at size 8.5
    SEC_HDR_H = 9 * mm     # section header bar height
    PAD       = 4 * mm

    # Section 1 fixed content
    box_gap     = 4 * mm
    box_w       = (W - 2*M - box_gap) / 2
    BOX_H       = 32 * mm
    sec1_h      = SEC_HDR_H + 4*mm + BOX_H + 4*mm

    # Factor rows — 10 rows distributed across available space (no section 4)
    n_factors   = 10
    available   = H - hdr_h - 5*mm - 10*mm    # 5mm top gap, 10mm bottom gap
    sec_gaps    = 2 * (4 * mm)               # 2 gaps between 3 sections
    factor_area = available - sec1_h - 2*SEC_HDR_H - sec_gaps
    row_h       = factor_area / n_factors

    # ── Helper: section header bar ────────────────────────────────────────────
    def sec_hdr(y_top, text):
        c.setFillColor(GREEN_DARK)
        c.rect(0, y_top - SEC_HDR_H, W, SEC_HDR_H, fill=1, stroke=0)
        c.setFillColor(GOLD)
        set_font(c, bold=True, size=10)
        c.drawString(M, y_top - SEC_HDR_H + 2.5*mm, text.upper())
        return y_top - SEC_HDR_H

    # ── Helper: factor rows ───────────────────────────────────────────────────
    def factor_rows(y_top, factors, accent):
        NAME_W     = 50 * mm
        WT_W       = 16 * mm
        DESC_X     = M + NAME_W + WT_W
        DESC_W     = W - M - DESC_X - 4*mm
        NAME_LINE_H = 4.5 * mm   # line-height for size-10 name text
        y = y_top
        for fname, wt, desc in factors:
            rh  = row_h
            mid = y - rh / 2

            c.setFillColor(WHITE)
            c.rect(M, y - rh, W - 2*M, rh, fill=1, stroke=0)
            c.setFillColor(accent)
            c.rect(M, y - rh, 3, rh, fill=1, stroke=0)

            # Split name at "\n" or "(" to wrap long names
            if "\n" in fname:
                name_lines = fname.split("\n")
            elif "(" in fname:
                idx = fname.index("(")
                name_lines = [fname[:idx].rstrip(), fname[idx:]]
            else:
                name_lines = [fname]

            n_name = len(name_lines)
            # All three columns share the same optical centre: mid - 1.5mm
            VCTR = mid - 1.5 * mm

            # Name block: top-line baseline rises by half the block above centre
            name_y0 = VCTR + (n_name - 1) * NAME_LINE_H / 2
            c.setFillColor(GRAY_DARK)
            set_font(c, bold=True, size=10)
            for li, nl in enumerate(name_lines):
                c.drawString(M + 5*mm, name_y0 - li * NAME_LINE_H, nl)

            # Weight — always centred independently (not tied to name line)
            c.setFillColor(accent)
            set_font(c, bold=True, size=10)
            c.drawString(M + NAME_W, VCTR, f"{wt} pts")

            # Description — two-bullet block centred vertically
            # desc is a (stat_text, plain_text) tuple
            from reportlab.pdfbase.pdfmetrics import stringWidth as sw
            stat_text, plain_text = desc
            BULLET_LH  = 3.8 * mm
            stat_pfx   = "• Statistical explanation: "
            plain_pfx  = "• Plain English: "
            sp_w = sw(stat_pfx,  "Montserrat-Bold",   FONT_S)
            pp_w = sw(plain_pfx, "Montserrat-Bold",   FONT_S)
            stat_parts  = simpleSplit(stat_text,  "Montserrat",        FONT_S, DESC_W - sp_w)[:2]
            plain_parts = simpleSplit(plain_text, "Montserrat-Italic", FONT_S, DESC_W - pp_w)[:2]
            total_lines = len(stat_parts) + len(plain_parts)
            block_h     = total_lines * BULLET_LH
            d_y         = VCTR + block_h / 2 - BULLET_LH / 2
            c.setFillColor(GRAY_DARK)
            for i, ln in enumerate(stat_parts):
                if i == 0:
                    c.setFont("Montserrat-Bold", FONT_S)
                    c.drawString(DESC_X, d_y, stat_pfx)
                    c.setFont("Montserrat", FONT_S)
                    c.drawString(DESC_X + sp_w, d_y, ln)
                else:
                    c.setFont("Montserrat", FONT_S)
                    c.drawString(DESC_X, d_y, ln)
                d_y -= BULLET_LH
            for i, ln in enumerate(plain_parts):
                if i == 0:
                    c.setFont("Montserrat-Bold", FONT_S)
                    c.drawString(DESC_X, d_y, plain_pfx)
                    c.setFont("Montserrat-Italic", FONT_S)
                    c.drawString(DESC_X + pp_w, d_y, ln)
                else:
                    c.setFont("Montserrat-Italic", FONT_S)
                    c.drawString(DESC_X, d_y, ln)
                d_y -= BULLET_LH

            c.setStrokeColor(GRAY_LIGHT)
            c.setLineWidth(0.3)
            c.line(M, y - rh, W - M, y - rh)
            y -= rh
        return y

    # ── Section 1: Dual scoring ───────────────────────────────────────────────
    y = H - hdr_h - 5 * mm
    y = sec_hdr(y, "1 · Dual scoring by market maturity")
    y -= 4 * mm

    # Framework boxes
    BPAD = 6 * mm   # inner padding for boxes (wider than PAD to keep text clear of edges)
    for bi, (title, col, desc, eg) in enumerate([
        ("Yield & Stability",    GREEN_MID,
         ">60% of all-time transactions are ready/secondary. Established districts with rental benchmarks and multi-year price history. Mirrors MSCI/IPD total-return logic.",
         "e.g. Khalifa City, Al Reem Island"),
        ("Growth & Early-Cycle", GOLD,
         "<40% of all-time transactions are ready — predominantly off-plan. Mirrors CBRE/PGIM emerging-market logic: demand velocity, developer confidence, forward appreciation.",
         "e.g. Al Hidayriyyat, Al Jubail Island"),
    ]):
        bx = M + bi * (box_w + box_gap)
        by = y - BOX_H
        c.setFillColor(WHITE)
        c.roundRect(bx, by, box_w, BOX_H, 2*mm, fill=1, stroke=0)
        c.setFillColor(col)
        c.rect(bx, by, 3, BOX_H, fill=1, stroke=0)
        c.setFillColor(col)
        set_font(c, bold=True, size=10)
        c.drawString(bx + BPAD, y - BPAD - 1*mm, title.upper())
        set_font(c, bold=False, size=FONT_S)
        c.setFillColor(GRAY_DARK)
        inner_w = box_w - 2 * BPAD
        dlines = simpleSplit(desc, "Montserrat", FONT_S, inner_w)[:4]
        ty = y - BPAD - 6*mm
        for ln in dlines:
            c.drawString(bx + BPAD, ty, ln)
            ty -= LINE_H
        c.setFillColor(GRAY_MID)
        set_font(c, bold=False, size=FONT_S)
        eg_lines = simpleSplit(eg, "Montserrat", FONT_S, inner_w)
        c.drawString(bx + BPAD, by + 3*mm, eg_lines[0] if eg_lines else eg)
    y -= BOX_H + 4 * mm

    # ── Section 2: Y&S factors ────────────────────────────────────────────────
    y = sec_hdr(y, "2 · Yield & Stability — Factor Weights")
    y = factor_rows(y, [
        ("Price Momentum (ready only)", "30", ("% change in median AED/sqft for ready/resale transactions, last 12m vs prior 12m. Off-plan excluded. Capped ±40%.", "Are prices going up? Compares price per sqft this year vs last year for completed homes. Bigger rise = more points.")),
        ("Gross Rental Yield",          "25", ("Median ADREC-registered annual rent ÷ median sale price. >8% → 25 pts; 6–8% → 22; 4–6% → 16; 2–4% → 8.", "How much rent does a landlord earn vs what they paid? Higher rent relative to purchase price = more points.")),
        ("Liquidity",                   "20", ("Transactions last 3m ÷ avg 3m over prior 9m. Log-scaled to prevent outliers dominating.", "How easy is it to buy or sell? More sales recently vs the past = an active, healthy market.")),
        ("Price Stability",             "15", ("Inverse CoV of quarterly median PSF over 24m — lower variance scores higher. CoV ≤0.05 → 15 pts; >0.30 → 2 pts.", "Are prices steady or all over the place? Consistent prices over 2 years score higher — wild swings score lower.")),
        ("Appreciation Signal",         "10", ("Ready median PSF ÷ off-plan median PSF (last 12m). Ratio >1 = completed units trade above off-plan entry.", "Do finished homes sell for more than off-plan? If yes, the area has proven its value over time.")),
    ], GREEN_MID)
    y -= 4 * mm

    # ── Section 3: G&EC factors ───────────────────────────────────────────────
    y = sec_hdr(y, "3 · Growth & Early-Cycle — Factor Weights")
    y = factor_rows(y, [
        ("Off-Plan Velocity",     "30", ("Off-plan transaction count last 6m vs prior 6m. Accelerating ratio = developer launches finding buyers. Ratio ≥3× → 30 pts.", "Are developers selling faster? More off-plan sales recently vs 6 months ago = strong buyer demand.")),
        ("Off-Plan Momentum",     "25", ("% change in off-plan median PSF, last 12m vs prior 12m. Capped ±40%.", "Are new-launch prices rising? Compares off-plan price per sqft this year vs last year.")),
        ("Appreciation Signal",   "20", ("Same ready/off-plan PSF ratio as Y&S, weighted higher (20 vs 10 pts) in early-cycle markets.", "Do finished homes sell above their off-plan price? Rarer in new areas, so it carries more weight here.")),
        ("Developer Activity",    "15", ("Unique projects with off-plan registrations last 12m vs prior 12m. Ratio ≥1.5 → 15 pts.", "Are more developers launching projects? More unique projects vs last year = a growing, competitive market.")),
        ("Market Entry\nMomentum", "10", ("Off-plan transactions last 3m vs rolling 3m avg over prior 9m. Ratio ≥1.5 → 10 pts.", "Is buying picking up right now? More sales in the last 3 months vs the usual pace = momentum building.")),
    ], GOLD)
    y -= 4 * mm

    # ── Section 4: Data & independence ───────────────────────────────────────
    page_footer(c, page_num)


# ── Screenshot capture ────────────────────────────────────────────────────────

def ensure_screenshots():
    """Capture adinteract.co screenshots for the closing page via playwright."""
    if SS_SALES.exists() and SS_INVESTORS.exists():
        return
    try:
        from playwright.sync_api import sync_playwright
        print("  Capturing website screenshots...")
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome")
            ctx = browser.new_context(viewport={"width": 1440, "height": 860})
            page = ctx.new_page()
            page.goto("https://adinteract.co", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2500)
            SS_SALES.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SS_SALES), full_page=False)
            page.goto("https://adinteract.co/investors", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2500)
            page.screenshot(path=str(SS_INVESTORS), full_page=False)
            browser.close()
    except Exception as e:
        print(f"  Warning: screenshot capture failed - closing page will show placeholders")


def page_closing(c, page_num):
    """Closing CTA page — cover aesthetic with screenshots and Instagram handle."""
    from reportlab.lib.utils import ImageReader

    # ── Full dark background ──────────────────────────────────────────────────
    c.setFillColor(GREEN_DARK)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # ── Top: logo + gold rule ─────────────────────────────────────────────────
    logo_size = 22 * mm
    draw_square_logo(c, M, H - M - logo_size, logo_size)
    c.setFillColor(GOLD)
    set_font(c, bold=True, size=11)
    c.drawString(M + logo_size + 4*mm, H - M - 8*mm, "ADInteract.co")
    c.setFillColor(GOLD_LIGHT)
    set_font(c, bold=False, size=8)
    c.drawString(M + logo_size + 4*mm, H - M - 14*mm, "Abu Dhabi Property Transactions")
    c.setFillColor(GOLD)
    c.rect(M, H - M - logo_size - 5*mm, W - 2*M, 1, fill=1, stroke=0)

    # ── Headline ──────────────────────────────────────────────────────────────
    hl_y = H - M - logo_size - 18*mm
    set_font(c, bold=True, size=24)
    c.setFillColor(WHITE)
    c.drawString(M, hl_y, "EXPLORE THE FULL PLATFORM")
    c.setFont("Montserrat-Italic", 12)
    c.setFillColor(GOLD_LIGHT)
    c.drawString(M, hl_y - 9*mm, "Live ADREC data  ·  Awesome investor tools  ·  Updated daily")

    # ── Two screenshots ───────────────────────────────────────────────────────
    gap      = 5 * mm
    img_w    = (W - 2*M - gap) / 2
    img_h    = img_w * (860 / 1440)   # preserve 1440×860 aspect ratio
    img_y    = hl_y - 16*mm - img_h
    xs       = [M, M + img_w + gap]
    captions = ["Sales & Rental Dashboard", "Investor Tools"]
    paths    = [SS_SALES, SS_INVESTORS]

    for x, path, caption in zip(xs, paths, captions):
        # Screenshot or placeholder
        if path.exists():
            try:
                img = ImageReader(str(path))
                c.drawImage(img, x, img_y, width=img_w, height=img_h,
                            preserveAspectRatio=False, mask='auto')
            except Exception:
                c.setFillColor(GREEN_MID)
                c.roundRect(x, img_y, img_w, img_h, 2*mm, fill=1, stroke=0)
        else:
            c.setFillColor(GREEN_MID)
            c.roundRect(x, img_y, img_w, img_h, 2*mm, fill=1, stroke=0)
        # Caption below screenshot
        c.setFillColor(GOLD)
        set_font(c, bold=True, size=14)
        c.drawString(x, img_y - 9*mm, caption.upper())

    # ── Feature bullets ───────────────────────────────────────────────────────
    feat_y = img_y - 27*mm   # gap below screenshot captions
    features = [
        ("Transaction Explorer",   "Search & filter 97,000+ ADREC sales by district, project, layout, date range and sale type."),
        ("Rental Index",           "Benchmark annual rents by community — median, lower and upper band per layout."),
        ("Price & Volume Trends",  "Track median price, AED/sqft and transaction volume over time."),
        ("ROI Calculator",         "Model net yield, capital gain CAGR and total ROI before you commit — off-plan or ready property."),
    ]
    col_w    = (W - 2*M - gap) / 2
    dot_r    = 1.5 * mm
    row_h_f  = 20 * mm   # more breathing room between bullet rows
    DESC_LH  = 4.5 * mm  # line height for description text
    for fi, (title, desc) in enumerate(features):
        col  = fi % 2
        row  = fi // 2
        fx   = M + col * (col_w + gap)
        fy   = feat_y - row * row_h_f
        c.setFillColor(GOLD)
        c.circle(fx + dot_r, fy + 3*mm, dot_r, fill=1, stroke=0)
        set_font(c, bold=True, size=12)
        c.setFillColor(WHITE)
        c.drawString(fx + 5*mm, fy + 2*mm, title)
        set_font(c, bold=False, size=10)
        c.setFillColor(GOLD_LIGHT)
        from reportlab.lib.utils import simpleSplit
        dlines = simpleSplit(desc, "Montserrat", 10, col_w - 6*mm)[:2]
        dy = fy - 3*mm
        for ln in dlines:
            c.drawString(fx + 5*mm, dy, ln)
            dy -= DESC_LH

    # ── Gold divider ──────────────────────────────────────────────────────────
    div_y = feat_y - 2*row_h_f - 8*mm
    c.setFillColor(GOLD)
    c.rect(M, div_y, W - 2*M, 1, fill=1, stroke=0)

    # ── CTA: website ──────────────────────────────────────────────────────────
    cta_y = div_y - 14*mm
    set_font(c, bold=True, size=18)
    c.setFillColor(GOLD)
    c.drawRightString(W - M, cta_y, "ADInteract.co")
    set_font(c, bold=False, size=10)
    c.setFillColor(WHITE)
    c.drawRightString(W - M, cta_y - 7*mm, "Free. Independent. Built on official ADREC data.")

    # ── Bottom date ───────────────────────────────────────────────────────────
    c.setFillColor(GRAY_MID)
    set_font(c, bold=False, size=7.5)
    c.drawString(M, 5*mm, f"Generated {datetime.now().strftime('%B %Y')}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== ADInteract Price Guide Generator ===")
    ensure_fonts()
    ensure_screenshots()
    df = pd.read_parquet(PARQUET)
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    scores = json.load(open(SCORES_JSON))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(OUTPUT), pagesize=A4)
    c.setTitle("AD Interact - Abu Dhabi Property Investor Guide 2026")
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

    print("  Page 11: Score Methodology")
    page_methodology(c, 11)
    c.showPage()

    print("  Page 12: Closing / CTA")
    page_closing(c, 12)
    c.showPage()

    c.save()
    size_kb = OUTPUT.stat().st_size // 1024
    print(f"\nOK Generated {OUTPUT}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
