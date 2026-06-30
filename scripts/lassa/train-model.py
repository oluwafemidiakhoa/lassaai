"""
LassaAI — Outbreak Prediction Model (XGBoost)
=============================================
Temporal cross-validation:
  Train  : 2012–2021
  Validate: 2022–2023
  Test   : 2024–2025

Usage:
  python scripts/lassa/train-model.py
"""

import csv
import pickle
import sys
from pathlib import Path
from collections import Counter

import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report,
)
from sklearn.calibration import calibration_curve
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC           = Path("data/lassa/features.csv")
MODEL_OUT     = Path("models/lassa/outbreak-model-v1.pkl")
FI_OUT        = Path("data/lassa/feature-importance.csv")
CALIB_OUT     = Path("data/lassa/calibration-curve.png")

FEATURE_COLS = [
    "month", "dry_season", "weeks_into_dry_season",
    "cases_lag1", "cases_lag2", "cases_lag4", "cases_lag8",
    "deaths_lag4",
    "cases_roll4", "cases_roll8", "cases_roll4_trend",
    "rain_lag4", "rain_lag8", "humidity_lag4", "temp_lag4",
    "is_edo", "is_ondo", "is_bauchi", "is_high_risk",
]
TARGET = "outbreak"

# -- Load data ----------------------------------------------------------------─

rows = []
with open(SRC, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        try:
            rows.append({
                "year":    int(r["year"]),
                **{c: float(r[c]) for c in FEATURE_COLS},
                TARGET:    int(r[TARGET]),
            })
        except (ValueError, KeyError):
            continue

print(f"Loaded {len(rows):,} rows from {SRC}")

# -- Temporal split ------------------------------------------------------------

train_rows = [r for r in rows if r["year"] <= 2021]
val_rows   = [r for r in rows if 2022 <= r["year"] <= 2023]
test_rows  = [r for r in rows if 2024 <= r["year"] <= 2025]

print(f"\nTemporal split:")
print(f"  Train  (<=2021): {len(train_rows):,} rows  pos={sum(r[TARGET] for r in train_rows):,}")
print(f"  Val  (2022-23): {len(val_rows):,} rows  pos={sum(r[TARGET] for r in val_rows):,}")
print(f"  Test (2024-25): {len(test_rows):,} rows  pos={sum(r[TARGET] for r in test_rows):,}")


def to_xy(rlist):
    X = np.array([[r[c] for c in FEATURE_COLS] for r in rlist], dtype=np.float32)
    y = np.array([r[TARGET] for r in rlist], dtype=np.int32)
    return X, y


X_train, y_train = to_xy(train_rows)
X_val,   y_val   = to_xy(val_rows)
X_test,  y_test  = to_xy(test_rows)

# Class imbalance weight
neg, pos = Counter(y_train)[0], Counter(y_train)[1]
spw = neg / pos if pos > 0 else 1.0
print(f"\n  scale_pos_weight = {spw:.2f}  (neg={neg:,} pos={pos:,})")

# -- Train --------------------------------------------------------------------─

params = dict(
    n_estimators=500,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=spw,
    random_state=42,
    eval_metric="logloss",
    early_stopping_rounds=30,
    verbosity=0,
)

model = XGBClassifier(**params)
model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=False,
)
print(f"\n  Best iteration: {model.best_iteration}")

# -- Evaluate ------------------------------------------------------------------

def evaluate(X, y, label, threshold=0.5):
    probs = model.predict_proba(X)[:, 1]
    preds = (probs >= threshold).astype(int)
    auroc = roc_auc_score(y, probs)
    prec  = precision_score(y, preds, zero_division=0)
    rec   = recall_score(y, preds, zero_division=0)
    f1    = f1_score(y, preds, zero_division=0)
    cm    = confusion_matrix(y, preds)
    return auroc, prec, rec, f1, cm, probs


sep = "=" * 60
print(f"\n{sep}")
print("EVALUATION RESULTS")
print(sep)

for X, y, label in [(X_val, y_val, "VALIDATION (2022-23)"),
                     (X_test, y_test, "TEST       (2024-25)")]:
    auroc, prec, rec, f1, cm, probs = evaluate(X, y, label)
    print(f"\n-- {label} --")
    print(f"  AUROC     : {auroc:.4f}")
    print(f"  Precision : {prec:.4f}")
    print(f"  Recall    : {rec:.4f}")
    print(f"  F1        : {f1:.4f}")
    print(f"  Confusion matrix (rows=actual, cols=predicted):")
    print(f"    TN={cm[0,0]:>5}  FP={cm[0,1]:>5}")
    print(f"    FN={cm[1,0]:>5}  TP={cm[1,1]:>5}")

# Success criterion
_, _, _, _, _, test_probs = evaluate(X_test, y_test, "test")
test_auroc = roc_auc_score(y_test, test_probs)
print(f"\n{sep}")
if test_auroc >= 0.80:
    print(f"  RESULT: EXCELLENT  (AUROC {test_auroc:.4f} >= 0.80) — write the paper!")
elif test_auroc >= 0.75:
    print(f"  RESULT: GOOD       (AUROC {test_auroc:.4f} >= 0.75) — write the paper!")
elif test_auroc >= 0.70:
    print(f"  RESULT: ACCEPTABLE (AUROC {test_auroc:.4f} >= 0.70)")
else:
    print(f"  RESULT: BELOW THRESHOLD (AUROC {test_auroc:.4f} < 0.70)")
print(sep)

# -- Feature importance --------------------------------------------------------

importances = model.feature_importances_
fi = sorted(zip(FEATURE_COLS, importances), key=lambda x: -x[1])

print("\nTop 15 Feature Importances:")
print(f"  {'Feature':<28} {'Importance':>10}")
print("  " + "-" * 40)
for feat, imp in fi[:15]:
    bar = "#" * int(imp * 200)
    print(f"  {feat:<28} {imp:>10.4f}  {bar}")

FI_OUT.parent.mkdir(parents=True, exist_ok=True)
with open(FI_OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["feature", "importance"])
    w.writerows(fi)
print(f"\nFeature importance saved: {FI_OUT}")

# -- Calibration curve --------------------------------------------------------─

# Use all non-train data for calibration
X_eval = np.vstack([X_val, X_test])
y_eval = np.concatenate([y_val, y_test])
all_probs = model.predict_proba(X_eval)[:, 1]

fig, ax = plt.subplots(figsize=(7, 6))
ax.set_facecolor("#0f172a")
fig.patch.set_facecolor("#0f172a")

fraction_pos, mean_pred = calibration_curve(y_eval, all_probs, n_bins=10, strategy="quantile")
ax.plot(mean_pred, fraction_pos, "o-", color="#06b6d4", lw=2, markersize=6, label="LassaAI model")
ax.plot([0, 1], [0, 1], "--", color="#475569", lw=1.5, label="Perfect calibration")

ax.set_xlabel("Mean predicted probability", color="#94a3b8", fontsize=11)
ax.set_ylabel("Fraction of positives (actual outbreak rate)", color="#94a3b8", fontsize=11)
ax.set_title("Calibration Curve — LassaAI Outbreak Model", color="#e2e8f0", fontsize=13)
ax.legend(facecolor="#1e293b", edgecolor="#334155", labelcolor="#e2e8f0")
ax.tick_params(colors="#94a3b8")
for spine in ax.spines.values():
    spine.set_edgecolor("#334155")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

# Annotate AUROC
ax.text(0.05, 0.92, f"Test AUROC = {test_auroc:.4f}", transform=ax.transAxes,
        color="#06b6d4", fontsize=11, fontweight="bold")

plt.tight_layout()
CALIB_OUT.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(CALIB_OUT, dpi=150)
print(f"Calibration curve saved: {CALIB_OUT}")

# -- Save model ----------------------------------------------------------------

MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
with open(MODEL_OUT, "wb") as f:
    pickle.dump({"model": model, "features": FEATURE_COLS}, f)
print(f"Model saved: {MODEL_OUT}")
