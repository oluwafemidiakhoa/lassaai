"""
LassaAI — Current Outbreak Forecast
=====================================
Loads the trained model and generates outbreak probabilities
for all Nigerian states for the next 4 weeks.

Usage:
  python scripts/lassa/forecast-now.py
"""

import csv
import json
import pickle
import math
import sys
from datetime import date
from pathlib import Path
from collections import defaultdict

import numpy as np

MODEL_PATH   = Path("models/lassa/outbreak-model-v1.pkl")
FEATURES_CSV = Path("data/lassa/features.csv")
MERGED_CSV   = Path("data/lassa/lassa-merged.csv")
FORECAST_OUT = Path("data/lassa/current-forecast.json")

FEATURE_COLS = [
    "month", "dry_season", "weeks_into_dry_season",
    "cases_lag1", "cases_lag2", "cases_lag4", "cases_lag8",
    "deaths_lag4",
    "cases_roll4", "cases_roll8", "cases_roll4_trend",
    "rain_lag4", "rain_lag8", "humidity_lag4", "temp_lag4",
    "is_edo", "is_ondo", "is_bauchi", "is_high_risk",
]

HIGH_RISK_STATES = {
    "Edo", "Ondo", "Bauchi", "Taraba", "Ebonyi",
    "Anambra", "Delta", "Benue", "Kogi", "Nasarawa",
}


def to_float(v, default=0.0):
    try:
        f = float(v)
        return default if math.isnan(f) else f
    except (TypeError, ValueError):
        return default


def epi_week_to_approx_month(year, epi_week):
    try:
        d = date.fromisocalendar(year, epi_week, 4)
        return d.month
    except ValueError:
        return 1


def dry_season_flag(month):
    return 1 if month in {11, 12, 1, 2, 3, 4} else 0


def weeks_into_dry_season(year, epi_week, month):
    if not dry_season_flag(month):
        return 0
    if month in {11, 12}:
        nov1_year = year
    else:
        nov1_year = year - 1
    try:
        nov1 = date(nov1_year, 11, 1)
        current = date.fromisocalendar(year, epi_week, 4)
        return max(0, (current - nov1).days // 7)
    except ValueError:
        return 0


# ── Load model ────────────────────────────────────────────────────────────────

with open(MODEL_PATH, "rb") as f:
    bundle = pickle.load(f)
model = bundle["model"]
print(f"Model loaded: {MODEL_PATH}")

# ── Load most recent merged data ──────────────────────────────────────────────

raw = []
with open(MERGED_CSV, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        try:
            raw.append({
                "state":     r["state"],
                "year":      int(r["year"]),
                "epi_week":  int(r["epi_week"]),
                "confirmed": to_float(r.get("confirmed_cases")),
                "deaths":    to_float(r.get("deaths")),
                "rainfall":  to_float(r.get("rainfall")),
                "humidity":  to_float(r.get("humidity")),
                "temp_max":  to_float(r.get("temp_max")),
            })
        except (ValueError, KeyError):
            continue

raw.sort(key=lambda r: (r["state"], r["year"], r["epi_week"]))
by_state = defaultdict(list)
for r in raw:
    by_state[r["state"]].append(r)

# ── Build feature vector for the latest available week per state ──────────────

today = date.today()
iso   = today.isocalendar()
current_year, current_week = iso[0], iso[1]


def build_latest_features(state: str, series: list) -> dict | None:
    """Build features from the last row that has at least 8 prior rows."""
    # Find the latest index with enough history
    for i in range(len(series) - 1, 7, -1):
        r = series[i]
        year, week = r["year"], r["epi_week"]
        month = epi_week_to_approx_month(year, week)

        def lag(k):
            return series[i - k]["confirmed"] if i >= k else 0.0

        def roll_mean(window):
            vals = [series[j]["confirmed"] for j in range(max(0, i - window), i)]
            return sum(vals) / len(vals) if vals else 0.0

        roll4 = roll_mean(4)
        roll8 = roll_mean(8)

        return {
            "state":                 state,
            "year":                  year,
            "epi_week":              week,
            "month":                 month,
            "dry_season":            dry_season_flag(month),
            "weeks_into_dry_season": weeks_into_dry_season(year, week, month),
            "cases_lag1":            lag(1),
            "cases_lag2":            lag(2),
            "cases_lag4":            lag(4),
            "cases_lag8":            lag(8),
            "deaths_lag4":           series[i - 4]["deaths"] if i >= 4 else 0.0,
            "cases_roll4":           roll4,
            "cases_roll8":           roll8,
            "cases_roll4_trend":     roll4 - roll8,
            "rain_lag4":             series[i - 4]["rainfall"] if i >= 4 else 0.0,
            "rain_lag8":             series[i - 8]["rainfall"] if i >= 8 else 0.0,
            "humidity_lag4":         series[i - 4]["humidity"] if i >= 4 else 0.0,
            "temp_lag4":             series[i - 4]["temp_max"] if i >= 4 else 0.0,
            "is_edo":                1 if state == "Edo" else 0,
            "is_ondo":               1 if state == "Ondo" else 0,
            "is_bauchi":             1 if state == "Bauchi" else 0,
            "is_high_risk":          1 if state in HIGH_RISK_STATES else 0,
        }
    return None


# Also build last-week features for change calculation
def build_prev_features(state: str, series: list) -> dict | None:
    for i in range(len(series) - 2, 8, -1):
        r = series[i]
        year, week = r["year"], r["epi_week"]
        month = epi_week_to_approx_month(year, week)

        def lag(k):
            return series[i - k]["confirmed"] if i >= k else 0.0

        def roll_mean(window):
            vals = [series[j]["confirmed"] for j in range(max(0, i - window), i)]
            return sum(vals) / len(vals) if vals else 0.0

        roll4 = roll_mean(4)
        roll8 = roll_mean(8)

        return {
            "month":                 month,
            "dry_season":            dry_season_flag(month),
            "weeks_into_dry_season": weeks_into_dry_season(year, week, month),
            "cases_lag1":            lag(1),
            "cases_lag2":            lag(2),
            "cases_lag4":            lag(4),
            "cases_lag8":            lag(8),
            "deaths_lag4":           series[i - 4]["deaths"] if i >= 4 else 0.0,
            "cases_roll4":           roll4,
            "cases_roll8":           roll8,
            "cases_roll4_trend":     roll4 - roll8,
            "rain_lag4":             series[i - 4]["rainfall"] if i >= 4 else 0.0,
            "rain_lag8":             series[i - 8]["rainfall"] if i >= 8 else 0.0,
            "humidity_lag4":         series[i - 4]["humidity"] if i >= 4 else 0.0,
            "temp_lag4":             series[i - 4]["temp_max"] if i >= 4 else 0.0,
            "is_edo":                1 if state == "Edo" else 0,
            "is_ondo":               1 if state == "Ondo" else 0,
            "is_bauchi":             1 if state == "Bauchi" else 0,
            "is_high_risk":          1 if state in HIGH_RISK_STATES else 0,
        }
    return None


# ── Predict ───────────────────────────────────────────────────────────────────

forecasts = []
for state, series in sorted(by_state.items()):
    curr = build_latest_features(state, series)
    prev = build_prev_features(state, series)
    if curr is None:
        continue

    X_curr = np.array([[curr[c] for c in FEATURE_COLS]], dtype=np.float32)
    prob = float(model.predict_proba(X_curr)[0, 1])

    change = None
    if prev is not None:
        X_prev = np.array([[prev[c] for c in FEATURE_COLS]], dtype=np.float32)
        prob_prev = float(model.predict_proba(X_prev)[0, 1])
        change = prob - prob_prev

    if prob >= 0.60:
        risk = "HIGH"
    elif prob >= 0.35:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    forecasts.append({
        "state":      state,
        "probability": round(prob, 3),
        "risk":       risk,
        "change_vs_last_week": round(change, 3) if change is not None else None,
        "as_of_year":  curr["year"],
        "as_of_week":  curr["epi_week"],
    })

forecasts.sort(key=lambda x: -x["probability"])

# ── Print table ───────────────────────────────────────────────────────────────

print(f"\n{'State':<18} {'Prob':>6}  {'Risk':<8}  {'Change':>12}")
print("-" * 55)
for fc in forecasts:
    ch = fc["change_vs_last_week"]
    ch_str = (f"+{ch:.3f}" if ch >= 0 else f"{ch:.3f}") if ch is not None else "   n/a"
    print(f"{fc['state']:<18} {fc['probability']:>6.3f}  {fc['risk']:<8}  {ch_str:>12}")

high   = [f for f in forecasts if f["risk"] == "HIGH"]
medium = [f for f in forecasts if f["risk"] == "MEDIUM"]
low    = [f for f in forecasts if f["risk"] == "LOW"]
print(f"\nSummary: HIGH={len(high)}  MEDIUM={len(medium)}  LOW={len(low)}")
print(f"Forecast horizon: next 4 weeks from latest available data")

# ── Save JSON ─────────────────────────────────────────────────────────────────

output = {
    "generated_at":   date.today().isoformat(),
    "forecast_horizon_weeks": 4,
    "model":          "outbreak-model-v1",
    "forecasts":      forecasts,
    "summary": {
        "high_risk_states":   [f["state"] for f in high],
        "medium_risk_states": [f["state"] for f in medium],
        "low_risk_states":    [f["state"] for f in low],
    },
}
FORECAST_OUT.parent.mkdir(parents=True, exist_ok=True)
FORECAST_OUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
print(f"\nForecast saved: {FORECAST_OUT}")
