"""
national-forecast-now.py — Forward forecast from the RETROSPECTIVELY EVALUATED national Lassa model.

Uses the same real national weekly series, the same 9 features, and the same
"elevated 4-week burden" target as build-real-national.py (retrospective evaluation:
out-of-time 2024 AUROC 0.880 vs 0.849 naive). Trains on every labelled week, then
outputs a single honest national probability that the NEXT 4 weeks will be an
elevated-transmission period.

Output: data/lassa/national-forecast.json

HONESTY GUARD: this forecasts the 4 weeks AFTER the latest available data week.
If the data is stale, that window may already be in the PAST — the output sets
`window_is_future` accordingly so the logger never records a stale forecast as
"prospective". To produce a genuine prospective forecast, refresh the data first
(scripts/lassa/refresh-national-series.py) so the series reaches the current epi-week.
"""
import csv
import json
import platform
from datetime import datetime, timezone, date, timedelta

import numpy as np
import sklearn
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

CSV = "data/lassa/lassa_fever_timeseries_full.csv"
OUT = "data/lassa/national-forecast.json"
MODEL_VERSION = "national-elevated-transmission-v1"
# Frozen by the 2026-2027 prospective protocol before the first scored forecast.
# Never re-derive this from refreshed/revised data during the prospective season.
FROZEN_ELEVATED_THRESHOLD = 32.0

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


# Integrity check for the pre-registered endpoint. The historical training-period
# median is expected to be 32, but the prospective threshold itself is a FROZEN
# constant. If an accidental rewrite/revision of the <=2023 source rows changes the
# recomputed median, fail closed rather than silently changing the endpoint mid-study.
train_f4 = [future4(i) for i in range(n) if year[i] <= 2023 and future4(i) is not None]
historical_train_median = float(np.median(train_f4))
if historical_train_median != FROZEN_ELEVATED_THRESHOLD:
    raise RuntimeError(
        f"Prospective protocol integrity failure: <=2023 median is {historical_train_median}, "
        f"expected frozen threshold {FROZEN_ELEVATED_THRESHOLD}. "
        "Do not generate/log a forecast until the historical-data drift is adjudicated."
    )
THRESH = FROZEN_ELEVATED_THRESHOLD

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
    random_state=0,
    n_jobs=1,
)
model.fit(X, y)

# Prospectively score the same naive baselines used in the retrospective paper.
# AUROC for the primary baseline is the raw recent-4-week mean. For Brier/ECE we
# need a probability, so fit a monotonic one-feature logistic calibrator ONLY on
# the frozen <=2023 training era. This preserves the baseline ranking while making
# the probability mapping explicit and reproducible.
baseline_y, baseline_roll4, baseline_lag1 = [], [], []
for j in range(n):
    f4 = future4(j)
    if j < 8 or f4 is None or year[j] > 2023:
        continue
    baseline_y.append(1 if f4 > THRESH else 0)
    baseline_roll4.append(roll(j, 4))
    baseline_lag1.append(lag(j, 1))

def calibrated_baseline_probability(values, current_value):
    calibrator = LogisticRegression(solver="lbfgs")
    calibrator.fit(np.asarray(values, dtype=float).reshape(-1, 1), np.asarray(baseline_y, dtype=int))
    return float(calibrator.predict_proba(np.asarray([[current_value]], dtype=float))[0, 1])

# Forecast the latest available week: its next-4-week outcome is unknown.
i = n - 1
prob = float(model.predict_proba(np.array([feats(i)], float))[:, 1][0])
primary_baseline_score = float(roll(i, 4))
secondary_baseline_score = float(lag(i, 1))
primary_baseline_probability = calibrated_baseline_probability(baseline_roll4, primary_baseline_score)
secondary_baseline_probability = calibrated_baseline_probability(baseline_lag1, secondary_baseline_score)

# Stronger pre-specified scientific comparators added in protocol amendment v1.1.
# They use only labelled history available before forecast time and are refit
# mechanically each week under the same expanding-window information boundary.
def harmonic_features(epi_week):
    angle1 = 2.0 * np.pi * (epi_week - 1) / 52.0
    angle2 = 2.0 * angle1
    return [np.sin(angle1), np.cos(angle1), np.sin(angle2), np.cos(angle2)]

seasonal_X = []
seasonal_persist_X = []
for j in range(n):
    f4 = future4(j)
    if j < 8 or f4 is None:
        continue
    h = harmonic_features(week[j])
    seasonal_X.append(h)
    seasonal_persist_X.append(
        h + [roll(j, 4), lag(j, 1), roll(j, 4) - roll(j, 8)]
    )

seasonal_model = LogisticRegression(solver="lbfgs", max_iter=5000)
seasonal_model.fit(np.asarray(seasonal_X, dtype=float), y)
seasonal_probability = float(
    seasonal_model.predict_proba(
        np.asarray([harmonic_features(week[i])], dtype=float)
    )[0, 1]
)

seasonal_persist_model = make_pipeline(
    StandardScaler(),
    LogisticRegression(solver="lbfgs", max_iter=5000),
)
seasonal_persist_model.fit(np.asarray(seasonal_persist_X, dtype=float), y)
current_h = harmonic_features(week[i])
seasonal_persist_probability = float(
    seasonal_persist_model.predict_proba(
        np.asarray([current_h + [
            roll(i, 4), lag(i, 1), roll(i, 4) - roll(i, 8)
        ]], dtype=float)
    )[0, 1]
)

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
    "threshold_contract": {
        "value": FROZEN_ELEVATED_THRESHOLD,
        "rule": "confirmed national burden over the next 4 weeks > 32",
        "historical_train_median_check": historical_train_median,
        "frozen": True,
    },
    "baseline": {
        "primary": {
            "name": "recent_4_week_case_average",
            "raw_score": round(primary_baseline_score, 6),
            "probability": round(primary_baseline_probability, 6),
            "probability_mapping": "one_feature_logistic_calibration_fit_on_epi_year_le_2023",
        },
        "secondary": {
            "name": "previous_week_case_count",
            "raw_score": round(secondary_baseline_score, 6),
            "probability": round(secondary_baseline_probability, 6),
            "probability_mapping": "one_feature_logistic_calibration_fit_on_epi_year_le_2023",
        },
        "seasonal_climatology": {
            "name": "seasonal_climatology_harmonic",
            "probability": round(seasonal_probability, 6),
            "definition": "logistic regression on first+second annual sin/cos harmonics; expanding labelled history only",
        },
        "seasonal_plus_persistence": {
            "name": "seasonal_plus_persistence",
            "probability": round(seasonal_persist_probability, 6),
            "definition": "standardized logistic regression on first+second annual harmonics + roll4 + lag1 + roll4-roll8; expanding labelled history only",
        },
    },
    "trained_on_labelled_weeks": int(len(y)),
    "data_through": {"epi_year": year[i], "epi_week": week[i], "week_end_date": wkend[i]},
    "forecast_window": {"start": window_start.isoformat(), "end": window_end.isoformat(), "horizon_weeks": 4},
    "window_is_future": window_is_future,
    "national_probability_elevated": round(prob, 4),
    "risk": risk,
    "feature_values": {f: round(float(v), 3) for f, v in zip(FEATS, feats(i))},
    "environment": {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
        "xgboost": xgb.__version__,
    },
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
