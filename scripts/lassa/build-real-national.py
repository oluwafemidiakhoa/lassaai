"""
build-real-national.py — REAL national weekly Lassa model from validated NCDC data.

Input : data/lassa/lassa_fever_timeseries_full.csv  (Kaggle NCDC-WER series, 2020-2025,
        cross-validated against NCDC published annual totals and an independent scrape).
Output: data/lassa/features-real.csv + honest metrics printed (model vs naive baseline).

Target: "elevated-transmission week" = confirmed cases over the NEXT 4 weeks exceed the
median 4-week burden of the training period. Chosen because national weekly incidence is
always > 0 (Lassa is endemic), so a ">0" or ">5" target would be trivially always-true;
predicting whether the coming month is ABOVE typical burden is the operationally useful,
non-degenerate question.
"""
import csv, numpy as np
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
import xgboost as xgb

rows = list(csv.DictReader(open("data/lassa/lassa_fever_timeseries_full.csv", encoding="utf-8")))
rows.sort(key=lambda r: (int(r["epi_year"]), int(r["epi_week"])))
conf = [int(r["confirmed_cases"] or 0) for r in rows]
year = [int(r["epi_year"]) for r in rows]
week = [int(r["epi_week"]) for r in rows]
n = len(rows)

def lag(i, k): return conf[i-k] if i-k >= 0 else 0
def roll(i, w):
    s = conf[max(0,i-w):i]; return sum(s)/len(s) if s else 0.0
def future4(i): return sum(conf[i+1:i+5]) if i+5 <= n else None

# training-period median 4-week burden (train = years <= 2023) sets the "elevated" threshold
train_f4 = [future4(i) for i in range(n) if year[i] <= 2023 and future4(i) is not None]
THRESH = float(np.median(train_f4))

X, y, yrs = [], [], []
for i in range(n):
    f4 = future4(i)
    if i < 8 or f4 is None:      # need 8 wks history + 4 wks future
        continue
    dry = 1 if week[i] <= 17 or week[i] >= 45 else 0   # dry season Nov-Apr
    feats = [lag(i,1), lag(i,2), lag(i,4), lag(i,8), roll(i,4), roll(i,8),
             roll(i,4)-roll(i,8), week[i], dry]
    X.append(feats); y.append(1 if f4 > THRESH else 0); yrs.append(year[i])
X, y, yrs = np.array(X, float), np.array(y), np.array(yrs)
FEATS = ["conf_lag1","conf_lag2","conf_lag4","conf_lag8","roll4","roll8","roll_trend","epi_week","dry_season"]

tr = yrs <= 2023; te = yrs == 2024   # honest out-of-time split; 2025 held for later prospective-style check
print(f"Total usable weeks: {len(y)}  | 'elevated' threshold (4-wk burden > {THRESH:.0f})  | positive rate {y.mean():.2f}")
print(f"Train (<=2023): {tr.sum()}  Test (2024): {te.sum()}  test positives: {int(y[te].sum())}")

m = xgb.XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05,
                      subsample=0.8, colsample_bytree=0.8,
                      scale_pos_weight=(y[tr]==0).sum()/max(1,(y[tr]==1).sum()), eval_metric="logloss")
m.fit(X[tr], y[tr])
p = m.predict_proba(X[te])[:,1]; pred = (p>=0.5).astype(int)

# naive baseline: most recent 4-week rolling mean (conf) alone
naive = X[te][:, FEATS.index("roll4")]

print("\n=== HONEST 2024 out-of-time test (REAL national data) ===")
if y[te].sum() > 0 and y[te].sum() < te.sum():
    print(f"XGBoost (9 features)          AUROC={roc_auc_score(y[te],p):.3f}  P={precision_score(y[te],pred):.3f} R={recall_score(y[te],pred):.3f} F1={f1_score(y[te],pred):.3f}")
    print(f"NAIVE baseline (4-wk mean)    AUROC={roc_auc_score(y[te],naive):.3f}")
    print(f"NAIVE baseline (conf_lag1)    AUROC={roc_auc_score(y[te], X[te][:,0]):.3f}")
else:
    print("test set degenerate (all one class) — need different split/threshold")
imp = sorted(zip(FEATS, m.feature_importances_), key=lambda t:-t[1])
print("\nTop features:", [(f, round(float(v),3)) for f,v in imp[:5]])
