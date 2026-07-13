"""
national-forecast-now.py — Forward forecast from the VALIDATED national Lassa model.

Uses the same real national weekly series, the same 9 features, and the same
"elevated 4-week burden" target as build-real-national.py (the validated model:
out-of-time 2024 AUROC 0.880 vs 0.849 naive). Trains on every labelled week, then
outputs a single honest national probability that the NEXT 4 weeks will be an
elevated-transmission period.

Output: data/lassa/national-forecast.json

HONESTY GUARD: this forecasts the 4 weeks AFTER the latest available data week.
If the data is stale, that window may already be in the PAST — the output sets
`window_is_future` accordingly so the logger never records a stale forecast as
"prospective". To produce a genuine prospective forecast, refresh the data first
(scripts/lassa/rebuild-ncdc-real.py) so the series reaches the current epi-week.
"""
import csv
import json
from datetime import datetime, timezone, date, timedelta

import numpy as np
import xgboost as xgb

CSV = "data/lassa/lassa_fever_timeseries_full.csv"
OUT = "data/lassa/national-forecast.json"
MODEL_VERSION = "national-elevated-transmission-v1"

rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
rows.sort(key=lambda r: (int(r["epi_year"]), int(r["epi_week"])))
conf  = [int(r["confirmed_cases"] or 0) for r in rows]
year  = [int(r["epi_year"]) for r in rows]
week  = [int(r["epi_week"]) for r in rows]
wkend = [r["week_end_date"] for r in rows]
n = len(rows)


def lag(i, k):  return conf[i - k] if i - k >= 0 else 0
def roll(i, w):
    s = conf[max(0, i - w):i]
    return sum(s) / len(s) if s else 0.0
def future4(i): return sum(conf[i + 1:i + 5]) if i + 5 <= n else None


# "elevated" threshold = median 4-week future burden over the training period
# (years <= 2023) — identical definition to the validated model, for consistency.
train_f4 = [future4(i) for i in range(n) if year[i] <= 2023 and future4(i) is not None]
THRESH = float(np.median(train_f4))

FEATS = ["conf_lag1", "conf_lag2", "conf_lag4", "conf_lag8",
         "roll4", "roll8", "roll_trend", "epi_week", "dry_season"]


def feats(i):
    dry = 1 if week[i] <= 17 or week[i] >= 45 else 0   # dry season Nov-Apr
    return [lag(i, 1), lag(i, 2), lag(i, 4), lag(i, 8),
            roll(i, 4), roll(i, 8), roll(i, 4) - roll(i, 8), week[i], dry]


# Train on every week whose 4-week outcome is known (all labelled history).
X, y = [], []
for i in range(n):
    f4 = future4(i)
    if i < 8 or f4 is None:
        continue
    X.append(feats(i))
    y.append(1 if f4 > THRESH else 0)
X, y = np.array(X, float), np.array(y)

model = xgb.XGBClassifier(
    n_estimators=300, max_depth=3, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8,
    scale_pos_weight=(y == 0).sum() / max(1, (y == 1).sum()),
    eval_metric="logloss",
)
model.fit(X, y)

# Forecast the latest available week: its next-4-week outcome is unknown.
i = n - 1
prob = float(model.predict_proba(np.array([feats(i)], float))[:, 1][0])
risk = ("VERY HIGH" if prob >= 0.75 else
        "HIGH"      if prob >= 0.50 else
        "MODERATE"  if prob >= 0.25 else "LOW")

# Forecast window = the 4 weeks AFTER the last data week.
last_end     = date.fromisoformat(wkend[i])
window_start = last_end + timedelta(days=1)
window_end   = last_end + timedelta(days=28)
today        = datetime.now(tz=timezone.utc).date()
window_is_future = window_end > today

out = {
    "generated_at": datetime.now(tz=timezone.utc).isoformat(),
    "model_version": MODEL_VERSION,
    "scope": "national",
    "target": "P(next 4 weeks' confirmed burden exceeds the training-median 4-week burden = 'elevated-transmission period')",
    "elevated_threshold_4wk_burden": round(THRESH, 1),
    "trained_on_labelled_weeks": int(len(y)),
    "data_through": {"epi_year": year[i], "epi_week": week[i], "week_end_date": wkend[i]},
    "forecast_window": {"start": window_start.isoformat(), "end": window_end.isoformat(), "horizon_weeks": 4},
    "window_is_future": window_is_future,
    "national_probability_elevated": round(prob, 4),
    "risk": risk,
    "feature_values": {f: round(float(v), 3) for f, v in zip(FEATS, feats(i))},
    "note": (
        "Genuine prospective forecast — the outcome window is in the future."
        if window_is_future else
        "RETROSPECTIVE ONLY: the forecast window has already passed (data is stale). "
        "Refresh the series (scripts/lassa/rebuild-ncdc-real.py) to the current epi-week "
        "before logging a prospective record."
    ),
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)

print(json.dumps({k: out[k] for k in [
    "model_version", "data_through", "forecast_window", "window_is_future",
    "national_probability_elevated", "risk", "elevated_threshold_4wk_burden"]}, indent=2))
print(f"\nWrote {OUT}")
