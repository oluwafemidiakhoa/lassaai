"""
LassaAI — Feature Engineering
==============================
Builds a modelling-ready feature matrix from data/lassa/lassa-merged.csv.

Output: data/lassa/features.csv

Usage:
  python scripts/lassa/build-features.py
"""

import csv
import math
import sys
from datetime import date, timedelta
from pathlib import Path
from collections import defaultdict

SRC  = Path("data/lassa/lassa-merged.csv")
OUT  = Path("data/lassa/features.csv")

# Top-10 endemic states by historical confirmed cases (from merge report)
HIGH_RISK_STATES = {
    "Edo", "Ondo", "Bauchi", "Taraba", "Ebonyi",
    "Anambra", "Delta", "Benue", "Kogi", "Nasarawa",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def to_float(v, default=0.0):
    try:
        f = float(v)
        return default if math.isnan(f) else f
    except (TypeError, ValueError):
        return default


def epi_week_to_approx_month(year: int, epi_week: int) -> int:
    """Approximate month from ISO week number."""
    try:
        d = date.fromisocalendar(year, epi_week, 4)  # Thursday of that ISO week
        return d.month
    except ValueError:
        return 1


def dry_season_flag(month: int) -> int:
    """Nigeria dry season: Nov–Apr."""
    return 1 if month in {11, 12, 1, 2, 3, 4} else 0


def weeks_into_dry_season(year: int, epi_week: int, month: int) -> int:
    """Weeks elapsed since November 1 of the current dry-season cycle."""
    if not dry_season_flag(month):
        return 0
    # Nov 1 of the relevant year
    if month in {11, 12}:
        nov1_year = year
    else:  # Jan–Apr: dry season started in previous calendar year
        nov1_year = year - 1
    try:
        nov1 = date(nov1_year, 11, 1)
        current = date.fromisocalendar(year, epi_week, 4)
        delta = (current - nov1).days
        return max(0, delta // 7)
    except ValueError:
        return 0


# ── Load & sort ───────────────────────────────────────────────────────────────

rows = []
with open(SRC, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        try:
            rows.append({
                "state":      r["state"],
                "year":       int(r["year"]),
                "epi_week":   int(r["epi_week"]),
                "confirmed":  to_float(r.get("confirmed_cases")),
                "deaths":     to_float(r.get("deaths")),
                "rainfall":   to_float(r.get("rainfall")),
                "humidity":   to_float(r.get("humidity")),
                "temp_max":   to_float(r.get("temp_max")),
            })
        except (ValueError, KeyError):
            continue

rows.sort(key=lambda r: (r["state"], r["year"], r["epi_week"]))

# ── Build per-state time series ───────────────────────────────────────────────

by_state = defaultdict(list)
for r in rows:
    by_state[r["state"]].append(r)

# ── Feature engineering ───────────────────────────────────────────────────────

FEATURE_COLS = [
    "state", "year", "epi_week",
    # time
    "month", "dry_season", "weeks_into_dry_season",
    # lag cases
    "cases_lag1", "cases_lag2", "cases_lag4", "cases_lag8",
    "deaths_lag4",
    # rolling
    "cases_roll4", "cases_roll8", "cases_roll4_trend",
    # weather lag
    "rain_lag4", "rain_lag8", "humidity_lag4", "temp_lag4",
    # state dummies
    "is_edo", "is_ondo", "is_bauchi", "is_high_risk",
    # target
    "outbreak",
]


def lag(series: list, idx: int, k: int) -> float:
    j = idx - k
    return series[j]["confirmed"] if j >= 0 else 0.0


def roll_mean(series: list, idx: int, window: int) -> float:
    vals = [series[j]["confirmed"] for j in range(max(0, idx - window), idx)]
    return sum(vals) / len(vals) if vals else 0.0


def future_cases(series: list, idx: int, horizon: int = 4) -> float:
    """Sum confirmed cases over the next `horizon` weeks."""
    total = 0.0
    for k in range(1, horizon + 1):
        j = idx + k
        if j < len(series):
            total += series[j]["confirmed"]
    return total


feature_rows = []

for state, series in by_state.items():
    for i, r in enumerate(series):
        year, week = r["year"], r["epi_week"]
        month = epi_week_to_approx_month(year, week)

        # Need at least 8 lag weeks before and 4 future weeks after
        if i < 8 or i + 4 >= len(series):
            continue

        c_lag1 = lag(series, i, 1)
        c_lag2 = lag(series, i, 2)
        c_lag4 = lag(series, i, 4)
        c_lag8 = lag(series, i, 8)
        d_lag4 = series[i - 4]["deaths"] if i >= 4 else 0.0

        roll4 = roll_mean(series, i, 4)
        roll8 = roll_mean(series, i, 8)

        rain_lag4    = series[i - 4]["rainfall"] if i >= 4 else 0.0
        rain_lag8    = series[i - 8]["rainfall"] if i >= 8 else 0.0
        hum_lag4     = series[i - 4]["humidity"] if i >= 4 else 0.0
        temp_lag4    = series[i - 4]["temp_max"] if i >= 4 else 0.0

        next4_cases = future_cases(series, i, 4)
        outbreak = 1 if next4_cases > 5 else 0

        feature_rows.append({
            "state":                 state,
            "year":                  year,
            "epi_week":              week,
            "month":                 month,
            "dry_season":            dry_season_flag(month),
            "weeks_into_dry_season": weeks_into_dry_season(year, week, month),
            "cases_lag1":            round(c_lag1, 3),
            "cases_lag2":            round(c_lag2, 3),
            "cases_lag4":            round(c_lag4, 3),
            "cases_lag8":            round(c_lag8, 3),
            "deaths_lag4":           round(d_lag4, 3),
            "cases_roll4":           round(roll4, 3),
            "cases_roll8":           round(roll8, 3),
            "cases_roll4_trend":     round(roll4 - roll8, 3),
            "rain_lag4":             round(rain_lag4, 3),
            "rain_lag8":             round(rain_lag8, 3),
            "humidity_lag4":         round(hum_lag4, 3),
            "temp_lag4":             round(temp_lag4, 3),
            "is_edo":                1 if state == "Edo" else 0,
            "is_ondo":               1 if state == "Ondo" else 0,
            "is_bauchi":             1 if state == "Bauchi" else 0,
            "is_high_risk":          1 if state in HIGH_RISK_STATES else 0,
            "outbreak":              outbreak,
        })

# ── Write output ──────────────────────────────────────────────────────────────

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FEATURE_COLS)
    writer.writeheader()
    writer.writerows(feature_rows)

total      = len(feature_rows)
outbreaks  = sum(r["outbreak"] for r in feature_rows)
pct        = 100 * outbreaks / total if total else 0

print(f"Feature matrix written: {OUT}")
print(f"  Total rows   : {total:,}")
print(f"  Outbreak = 1 : {outbreaks:,}  ({pct:.1f}%)")
print(f"  Outbreak = 0 : {total - outbreaks:,}  ({100 - pct:.1f}%)")
print(f"  Class ratio  : 1 : {(total - outbreaks) / outbreaks:.1f}" if outbreaks else "  No positive examples!")
print(f"  States       : {len(by_state)}")
print(f"  Year range   : {min(r['year'] for r in feature_rows)}–{max(r['year'] for r in feature_rows)}")
