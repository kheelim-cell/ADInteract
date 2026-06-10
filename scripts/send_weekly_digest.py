"""
send_weekly_digest.py
---------------------
Generates and emails the weekly ADInteract market digest to info@notadubaibroker.com.

Rotates focus each week across 4 sections:
  Week 0 (mod 4): Volume & price overview
  Week 1 (mod 4): Top districts leaderboard
  Week 2 (mod 4): Top projects & notable deals
  Week 3 (mod 4): Rental yield & investor spotlight

Always includes:
  - Last 7-day stats vs prior 7-day
  - Clear CTA to adinteract.co

Required env vars:
  GOOGLE_CREDENTIALS_JSON  — service account (for Google Sheet)
  GMAIL_APP_PASSWORD       — Gmail App Password for info@notadubaibroker.com
  GMAIL_SENDER             — sender address (default: info@notadubaibroker.com)

Usage:
  python scripts/send_weekly_digest.py
"""

import base64
import json
import os
import smtplib
import tempfile
from datetime import date, datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# ── Config ────────────────────────────────────────────────────────────────────
SHEET_ID      = "1c9Xc6qsXfTwmnZ4gGMwvyCQ3bTDXBIO9ZyfnfwMl3tw"
GID           = 39002702
SITE_URL      = "https://adinteract.co"
RECIPIENT     = "info@notadubaibroker.com"
SENDER        = os.environ.get("GMAIL_SENDER", "info@notadubaibroker.com")
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# Rotation: which week number mod 4 maps to which focus
FOCUS_NAMES = [
    "Volume & Price Overview",
    "Top Districts Leaderboard",
    "Top Projects & Notable Deals",
    "Rental Yield & Investor Spotlight",
]

# ── Brand colours ─────────────────────────────────────────────────────────────
GREEN  = "#1e4d3a"
GOLD   = "#c9a84c"
LIGHT  = "#f5f5f0"
WHITE  = "#ffffff"
GRAY   = "#6b7280"
BORDER = "#e5e7eb"


# ── Credentials ───────────────────────────────────────────────────────────────
def get_credentials() -> Credentials:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds_file = os.environ.get("GOOGLE_CREDENTIALS_FILE")
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON", "").strip()

    if creds_file:
        return Credentials.from_service_account_file(creds_file, scopes=scopes)

    if creds_json.startswith("{"):
        info = json.loads(creds_json)
    else:
        padded = creds_json + "=" * (4 - len(creds_json) % 4)
        info = json.loads(base64.b64decode(padded).decode())

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(info, tmp)
    tmp.close()
    creds = Credentials.from_service_account_file(tmp.name, scopes=scopes)
    os.unlink(tmp.name)
    return creds


# ── Data loading ──────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    print("Loading data from Google Sheet...")
    gc = gspread.authorize(get_credentials())
    sh = gc.open_by_key(SHEET_ID)
    ws = next(s for s in sh.worksheets() if s.id == GID)
    rows = ws.get_all_values()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df["sale_date"] = pd.to_datetime(df["Sale Application Date"], errors="coerce")
    df["price_aed"] = pd.to_numeric(
        df["Property Sale Price (AED)"].str.replace(",", "", regex=False),
        errors="coerce"
    )
    df["rate_sqm"] = pd.to_numeric(
        df["Rate (AED per SQM)"].str.replace(",", "", regex=False),
        errors="coerce"
    )
    # AED/sqft = rate_sqm / 10.7639
    df["rate_sqft"] = df["rate_sqm"] / 10.7639
    df = df.dropna(subset=["sale_date", "price_aed"])
    print(f"  Loaded {len(df):,} rows, max date: {df['sale_date'].max().date()}")
    return df


# ── Stats helpers ─────────────────────────────────────────────────────────────
def week_stats(df: pd.DataFrame, start: date, end: date) -> dict:
    mask = (df["sale_date"].dt.date >= start) & (df["sale_date"].dt.date <= end)
    w = df[mask]
    prices = w["price_aed"].dropna()
    rates  = w["rate_sqft"].dropna()
    return {
        "volume":       len(w),
        "median_price": prices.median() if len(prices) else 0,
        "median_rate":  rates.median()  if len(rates)  else 0,
        "total_value":  prices.sum()    if len(prices) else 0,
    }


def fmt_aed(v: float) -> str:
    if v >= 1_000_000_000:
        return f"AED {v/1_000_000_000:.1f}B"
    if v >= 1_000_000:
        return f"AED {v/1_000_000:.1f}M"
    return f"AED {v:,.0f}"


def fmt_pct(current: float, prior: float) -> str:
    if prior == 0:
        return ""
    pct = (current - prior) / prior * 100
    arrow = "↑" if pct >= 0 else "↓"
    color = "#16a34a" if pct >= 0 else "#dc2626"
    return f'<span style="color:{color};font-weight:600">{arrow} {abs(pct):.1f}%</span>'


# ── HTML builders ─────────────────────────────────────────────────────────────
def base_style() -> str:
    return f"""
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
      body {{ margin:0; padding:0; background:{LIGHT}; font-family:'Montserrat',sans-serif; }}
      .wrap {{ max-width:620px; margin:0 auto; background:{WHITE}; border-radius:12px; overflow:hidden; }}
      .header {{ background:{GREEN}; padding:0; }}
      .header a.banner {{ display:block; text-decoration:none; }}
      .header a.banner img {{ display:block; width:100%; height:auto; }}
      .header-meta {{ padding:14px 32px 18px; }}
      .header-meta p {{ margin:0; color:rgba(255,255,255,0.65); font-size:12px; font-family:'Montserrat',sans-serif; }}
      .header-meta p.focus {{ margin-top:4px; color:{GOLD}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; }}
      .top-cta {{ background:{GOLD}; text-align:center; padding:11px 20px; }}
      .top-cta a {{ color:{GREEN}; font-weight:800; font-size:13px; text-decoration:none; letter-spacing:0.2px; font-family:'Montserrat',sans-serif; }}
      .body {{ padding:28px 32px; }}
      .stat-row {{ display:flex; gap:12px; margin-bottom:20px; }}
      .stat {{ flex:1; background:{LIGHT}; border-radius:10px; padding:14px 16px; }}
      .stat .label {{ font-size:11px; font-weight:600; color:{GRAY}; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px; }}
      .stat .value {{ font-size:20px; font-weight:800; color:{GREEN}; line-height:1.1; }}
      .stat .change {{ font-size:12px; margin-top:3px; }}
      h2 {{ font-size:15px; font-weight:700; color:{GREEN}; margin:24px 0 12px; border-left:3px solid {GOLD}; padding-left:10px; }}
      table {{ width:100%; border-collapse:collapse; font-size:13px; font-family:'Montserrat',sans-serif; }}
      th {{ text-align:left; padding:8px 10px; background:{LIGHT}; color:{GRAY}; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.4px; font-family:'Montserrat',sans-serif; }}
      td {{ padding:9px 10px; border-bottom:1px solid {BORDER}; color:#111827; font-family:'Montserrat',sans-serif; }}
      tr:last-child td {{ border-bottom:none; }}
      .cta {{ margin:28px 0 0; background:{GREEN}; border-radius:10px; padding:22px 24px; text-align:center; }}
      .cta p {{ margin:0 0 14px; color:rgba(255,255,255,0.8); font-size:14px; line-height:1.5; }}
      .cta a {{ display:inline-block; background:{GOLD}; color:{GREEN}; font-weight:800; font-size:14px; padding:12px 28px; border-radius:8px; text-decoration:none; }}
      .footer {{ padding:20px 32px; text-align:center; font-size:11px; color:{GRAY}; border-top:1px solid {BORDER}; }}
      .badge {{ display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; font-weight:600; }}
      .off-plan {{ background:#fef9c3; color:#854d0e; }}
      .ready    {{ background:#dcfce7; color:#166534; }}
    </style>
    """


def stat_card(label: str, value: str, change_html: str = "") -> str:
    return f"""
    <div class="stat">
      <div class="label">{label}</div>
      <div class="value">{value}</div>
      {f'<div class="change">{change_html}</div>' if change_html else ''}
    </div>"""


def section_volume(this_w: dict, prev_w: dict) -> str:
    return f"""
    <h2>Last 7 Days — Market Pulse</h2>
    <div class="stat-row">
      {stat_card("Transactions", f"{this_w['volume']:,}", fmt_pct(this_w['volume'], prev_w['volume']))}
      {stat_card("Median Price", fmt_aed(this_w['median_price']), fmt_pct(this_w['median_price'], prev_w['median_price']))}
    </div>
    <div class="stat-row">
      {stat_card("Median AED/sqft", f"AED {this_w['median_rate']:,.0f}", fmt_pct(this_w['median_rate'], prev_w['median_rate']))}
      {stat_card("Total Value", fmt_aed(this_w['total_value']), fmt_pct(this_w['total_value'], prev_w['total_value']))}
    </div>"""


def section_top_districts(df: pd.DataFrame, start: date, end: date) -> str:
    mask = (df["sale_date"].dt.date >= start) & (df["sale_date"].dt.date <= end)
    w = df[mask]
    if w.empty:
        return ""
    top = (
        w.groupby("District")
        .agg(txns=("price_aed", "count"), median_price=("price_aed", "median"))
        .sort_values("txns", ascending=False)
        .head(8)
        .reset_index()
    )
    rows_html = ""
    for _, r in top.iterrows():
        rows_html += f"""
        <tr>
          <td><strong>{r['District']}</strong></td>
          <td style="text-align:right">{int(r['txns']):,}</td>
          <td style="text-align:right">{fmt_aed(r['median_price'])}</td>
        </tr>"""
    return f"""
    <h2>Top Districts by Volume (last 7 days)</h2>
    <table>
      <tr><th>District</th><th style="text-align:right">Txns</th><th style="text-align:right">Median Price</th></tr>
      {rows_html}
    </table>"""


def section_top_projects(df: pd.DataFrame, start: date, end: date) -> str:
    mask = (df["sale_date"].dt.date >= start) & (df["sale_date"].dt.date <= end)
    w = df[mask]
    if w.empty:
        return ""
    top = (
        w.groupby("Project Name")
        .agg(txns=("price_aed", "count"), median_price=("price_aed", "median"))
        .sort_values("txns", ascending=False)
        .head(6)
        .reset_index()
    )
    rows_html = ""
    for _, r in top.iterrows():
        rows_html += f"""
        <tr>
          <td><strong>{r['Project Name']}</strong></td>
          <td style="text-align:right">{int(r['txns']):,}</td>
          <td style="text-align:right">{fmt_aed(r['median_price'])}</td>
        </tr>"""
    return f"""
    <h2>Most Active Projects (last 7 days)</h2>
    <table>
      <tr><th>Project</th><th style="text-align:right">Txns</th><th style="text-align:right">Median Price</th></tr>
      {rows_html}
    </table>"""


def section_notable_deals(df: pd.DataFrame, start: date, end: date) -> str:
    mask = (df["sale_date"].dt.date >= start) & (df["sale_date"].dt.date <= end)
    w = df[mask].nlargest(5, "price_aed")
    if w.empty:
        return ""
    rows_html = ""
    for _, r in w.iterrows():
        sale_type = str(r.get("Sale Application Type", "")).strip().lower()
        badge_cls = "off-plan" if "off" in sale_type else "ready"
        badge_lbl = "Off-plan" if "off" in sale_type else "Ready"
        layout = str(r.get("Property Layout", "")).strip() or "—"
        rows_html += f"""
        <tr>
          <td>
            <strong>{r['Project Name']}</strong><br>
            <span style="font-size:11px;color:{GRAY}">{r['District']} · {layout}</span>
          </td>
          <td style="text-align:right"><strong>{fmt_aed(r['price_aed'])}</strong></td>
          <td style="text-align:right"><span class="badge {badge_cls}">{badge_lbl}</span></td>
        </tr>"""
    return f"""
    <h2>Notable Deals This Week</h2>
    <table>
      <tr><th>Property</th><th style="text-align:right">Price</th><th style="text-align:right">Type</th></tr>
      {rows_html}
    </table>"""


def section_rental_yield(df: pd.DataFrame, start: date, end: date) -> str:
    """Top districts by AED/sqft (proxy for yield signal when rental data unavailable)."""
    mask = (
        (df["sale_date"].dt.date >= start) &
        (df["sale_date"].dt.date <= end) &
        df["rate_sqft"].notna() &
        (df["rate_sqft"] > 0)
    )
    w = df[mask]
    if w.empty:
        return ""
    top = (
        w.groupby("District")
        .agg(median_rate=("rate_sqft", "median"), txns=("price_aed", "count"))
        .query("txns >= 3")
        .sort_values("median_rate", ascending=False)
        .head(8)
        .reset_index()
    )
    rows_html = ""
    for _, r in top.iterrows():
        rows_html += f"""
        <tr>
          <td><strong>{r['District']}</strong></td>
          <td style="text-align:right">AED {r['median_rate']:,.0f}/sqft</td>
          <td style="text-align:right">{int(r['txns']):,}</td>
        </tr>"""
    return f"""
    <h2>Highest AED/sqft Districts (last 7 days)</h2>
    <table>
      <tr><th>District</th><th style="text-align:right">Median AED/sqft</th><th style="text-align:right">Txns</th></tr>
      {rows_html}
    </table>
    <p style="font-size:12px;color:{GRAY};margin-top:8px">
      Higher AED/sqft = premium pricing. Visit ADInteract for full rental yield analysis by community.
    </p>"""


def build_email(df: pd.DataFrame, week_num: int) -> tuple[str, str]:
    today      = date.today()
    week_start = today - timedelta(days=7)
    prev_start = today - timedelta(days=14)
    prev_end   = today - timedelta(days=8)

    this_w = week_stats(df, week_start, today)
    prev_w = week_stats(df, prev_start, prev_end)

    focus_idx  = week_num % 4
    focus_name = FOCUS_NAMES[focus_idx]

    date_range = f"{week_start.strftime('%d %b')} – {today.strftime('%d %b %Y')}"
    subject    = f"Abu Dhabi Property Market | {date_range} | {this_w['volume']:,} transactions"

    # Always include volume stats
    content = section_volume(this_w, prev_w)

    # Rotating focus section
    if focus_idx == 0:
        content += section_top_districts(df, week_start, today)
    elif focus_idx == 1:
        content += section_top_districts(df, week_start, today)
        content += section_notable_deals(df, week_start, today)
    elif focus_idx == 2:
        content += section_top_projects(df, week_start, today)
        content += section_notable_deals(df, week_start, today)
    else:
        content += section_rental_yield(df, week_start, today)
        content += section_top_districts(df, week_start, today)

    cta_text = {
        0: "Filter by district, set your date range, and export the full dataset.",
        1: "Drill into any district's price history and transaction volume.",
        2: "Explore project-level analytics and comparable pricing.",
        3: "Calculate net yield and capital gain for any Abu Dhabi property.",
    }[focus_idx]

    cta_links = {
        0: f"{SITE_URL}/",
        1: f"{SITE_URL}/investors/compare",
        2: f"{SITE_URL}/",
        3: f"{SITE_URL}/investors/calculator",
    }[focus_idx]

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{base_style()}</head>
    <body>
    <div style="padding:20px 16px;background:{LIGHT}">
    <div class="wrap">
      <div class="header">
        <a href="{SITE_URL}" class="banner">
          <img src="{SITE_URL}/brand/og-image.png" alt="ADInteract — Abu Dhabi Property Transactions" />
        </a>
        <div class="header-meta">
          <p>Abu Dhabi Property Market Weekly — {date_range}</p>
          <p class="focus">This week: {focus_name}</p>
        </div>
        <div class="top-cta">
          <a href="{cta_links}">View live dashboard on ADInteract.co &rarr;</a>
        </div>
      </div>
      <div class="body">
        {content}
        <div class="cta">
          <p>{cta_text}<br>97,000+ ADREC-registered transactions, updated daily.</p>
          <a href="{cta_links}">Explore on ADInteract.co →</a>
        </div>
      </div>
      <div class="footer">
        <p>ADInteract.co · Abu Dhabi Property Transactions · Powered by ADREC data</p>
        <p style="margin-top:4px"><a href="mailto:info@notadubaibroker.com?subject=Unsubscribe" style="color:{GRAY};text-decoration:underline;">Unsubscribe</a></p>
      </div>
    </div>
    </div>
    </body>
    </html>
    """

    return subject, html


# ── Send via Gmail SMTP ───────────────────────────────────────────────────────
def send_email(subject: str, html: str) -> None:
    if not GMAIL_PASSWORD:
        # No password configured — save HTML to file for manual review
        out = "scripts/data/weekly_digest.html"
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"GMAIL_APP_PASSWORD not set — digest saved to {out}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER
    msg["To"]      = RECIPIENT
    msg.attach(MIMEText(html, "html"))

    print(f"Sending digest to {RECIPIENT}...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER, GMAIL_PASSWORD)
        server.sendmail(SENDER, [RECIPIENT], msg.as_string())
    print("Sent.")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # Week number for rotation (ISO week mod 4)
    week_num = date.today().isocalendar()[1]

    df = load_data()
    subject, html = build_email(df, week_num)

    print(f"Subject: {subject}")
    send_email(subject, html)


if __name__ == "__main__":
    main()
