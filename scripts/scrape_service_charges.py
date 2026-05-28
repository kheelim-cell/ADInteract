"""
ADREC Service Charge Scraper — v5 (targeted)
=============================================
1. You paste the ArcGIS token (from DevTools).
2. Script fetches ALL projects from the FeatureServer in one call.
3. For each project, calls the public ServiceCharge API (no token needed)
   to get year-by-year fee breakdown.
4. Saves static/data/service_charges.json + scripts/service_charges.csv

Requirements:  pip install requests
Usage:         python scripts/scrape_service_charges.py
"""

import json
import time
import csv
import sys
from pathlib import Path
import urllib.parse
import urllib.request

OUT_JSON = Path(__file__).parent.parent / "static" / "data" / "service_charges.json"
OUT_CSV  = Path(__file__).parent / "service_charges.csv"

FEATURE_URL = (
    "https://gis.adres.ae/server/rest/services/"
    "ADREC_INTERACTIVE_MAP/AnalysisMap/MapServer/5/query"
)
CHARGE_URL = "https://gis.adres.ae/interactivemap"

CATEGORIES = ["RESIDENTIAL", "COMMERCIAL"]


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def fetch_json(url: str, params: dict) -> dict:
    qs  = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"{url}?{qs}",
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": "https://adrec.gov.ae/",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


# ── Step 1: get all projects from FeatureServer ───────────────────────────────

def fetch_all_projects(token: str) -> list[dict]:
    projects = []
    for category in CATEGORIES:
        offset = 0
        while True:
            params = {
                "f":                  "json",
                "where":              f"service_charge_year=1000 and sub_project_category='{category}' and sub_project_type='All types'",
                "outFields":          "OBJECTID,developer_name,district,project_name,project_nmber,service_charge_avg,service_charge_max,service_charge_min,sub_project_category",
                "returnGeometry":     "false",
                "resultRecordCount":  "2000",
                "resultOffset":       str(offset),
                "token":              token,
            }
            try:
                data = fetch_json(FEATURE_URL, params)
            except Exception as e:
                print(f"  [error] FeatureServer fetch failed: {e}")
                break

            features = data.get("features", [])
            if not features:
                break

            for f in features:
                a = f.get("attributes", {})
                projects.append({
                    "project_name":    a.get("project_name", ""),
                    "project_number":  a.get("project_nmber", ""),
                    "district":        (a.get("district") or "").title(),
                    "developer_name":  (a.get("developer_name") or "").title(),
                    "category":        a.get("sub_project_category", ""),
                    "sc_avg":          a.get("service_charge_avg"),
                    "sc_min":          a.get("service_charge_min"),
                    "sc_max":          a.get("service_charge_max"),
                })

            print(f"  {category}: fetched {len(features)} (offset {offset})")
            if len(features) < 2000:
                break
            offset += 2000

    # Deduplicate by project_number
    seen, unique = set(), []
    for p in projects:
        k = p["project_number"]
        if k and k not in seen:
            seen.add(k)
            unique.append(p)
    return unique


# ── Step 2: enrich with detailed ServiceCharge data ──────────────────────────

def fetch_service_charge(project_number: str, district: str) -> dict | None:
    """
    Call the public (no-token) ServiceCharge handler.
    Returns {latest_year, sub_projects: [{name, category, type, fee}]}
    """
    params = {
        "handler":          "ServiceCharge",
        "project_number":   project_number,
        "district":         district.upper(),
        "sub_project_type": "All types",
    }
    try:
        data = fetch_json(CHARGE_URL, params)
    except Exception as e:
        print(f"    [warn] {project_number}: {e}")
        return None

    # Response is HTML-parsed by WebFetch but raw Python gets JSON directly
    if not isinstance(data, (list, dict)):
        return None

    # Normalise — the API may return a list of charge rows or a dict
    rows = data if isinstance(data, list) else data.get("serviceCharges", [])
    if not rows:
        return None

    # Find latest year
    latest_year = max((r.get("year", 0) for r in rows), default=None)
    latest_rows = [r for r in rows if r.get("year") == latest_year]

    return {
        "latest_year": latest_year,
        "sub_projects": [
            {
                "name":     r.get("subProjectName", ""),
                "category": r.get("category", ""),
                "type":     r.get("subProjectType", ""),
                "fee":      r.get("feesAEDPerSqFt"),
            }
            for r in latest_rows
        ],
    }


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    Path(OUT_JSON).parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("ADREC Service Charge Scraper v5")
    print("=" * 60)
    print()
    print("Paste the ArcGIS token from DevTools (the 'token=...' part")
    print("of the FeatureServer query URL you shared earlier).")
    print("Then press Enter.")
    print()
    token = input("Token: ").strip()
    if not token:
        print("No token provided — exiting.")
        sys.exit(1)

    # ── fetch all projects ────────────────────────────────────────────────
    print()
    print(f"[1/2] Fetching all projects from FeatureServer…")
    projects = fetch_all_projects(token)
    print(f"  → {len(projects)} unique projects found")

    if not projects:
        print("No projects returned. Token may have expired.")
        print("Refresh the ADREC map, click a project, copy the new token from DevTools.")
        sys.exit(1)

    # ── enrich each project with detailed service charge data ─────────────
    print()
    print(f"[2/2] Fetching detailed service charges (public API, no token)…")
    enriched = []
    for i, proj in enumerate(projects, 1):
        pn  = proj["project_number"]
        dis = proj["district"].upper()
        print(f"  [{i}/{len(projects)}] {proj['project_name']} ({dis})")

        detail = fetch_service_charge(pn, dis)
        if detail:
            proj["latest_year"]  = detail["latest_year"]
            proj["sub_projects"] = detail["sub_projects"]
            # Primary fee = first sub-project fee (or avg as fallback)
            proj["primary_fee"]  = (
                detail["sub_projects"][0]["fee"]
                if detail["sub_projects"]
                else proj["sc_avg"]
            )
        else:
            proj["latest_year"]  = None
            proj["sub_projects"] = []
            proj["primary_fee"]  = proj["sc_avg"]

        enriched.append(proj)
        time.sleep(0.15)   # polite rate-limit

    # ── save JSON ─────────────────────────────────────────────────────────
    import datetime
    output = {
        "last_updated": datetime.date.today().isoformat(),
        "total":        len(enriched),
        "projects":     enriched,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n✓ JSON saved → {OUT_JSON}")

    # ── save CSV ──────────────────────────────────────────────────────────
    cols = [
        "project_name", "project_number", "district", "developer_name",
        "category", "latest_year", "primary_fee", "sc_min", "sc_avg", "sc_max",
    ]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for p in enriched:
            w.writerow({k: p.get(k, "") for k in cols})
    print(f"✓ CSV saved  → {OUT_CSV}")
    print()
    print("Next steps:")
    print("  1. Check scripts/service_charges.csv to verify the data")
    print("  2. git add static/data/service_charges.json")
    print('  3. git commit -m "data: ADREC service charges"')


if __name__ == "__main__":
    main()
