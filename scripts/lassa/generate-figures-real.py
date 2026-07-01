"""
generate-figures-real.py — figures for the REAL national Lassa analysis.
Input : data/lassa/lassa_fever_timeseries_full.csv (validated NCDC weekly, 2020-2025)
Output: docs/lassa/figures/figure{1,2,3,4}_*.png
Mirrors the modelling in build-real-national.py so figures match the manuscript exactly.
"""
import csv, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import roc_curve, auc
import xgboost as xgb

OUT = Path("docs/lassa/figures"); OUT.mkdir(parents=True, exist_ok=True)
TEAL, AMBER, RED, GREY = "#14b8a6", "#f59e0b", "#dc2626", "#94a3b8"

rows = list(csv.DictReader(open("data/lassa/lassa_fever_timeseries_full.csv", encoding="utf-8")))
rows.sort(key=lambda r: (int(r["epi_year"]), int(r["epi_week"])))
conf = [int(r["confirmed_cases"] or 0) for r in rows]
year = [int(r["epi_year"]) for r in rows]
week = [int(r["epi_week"]) for r in rows]
n = len(rows)

def lag(i,k): return conf[i-k] if i-k>=0 else 0
def roll(i,w):
    s=conf[max(0,i-w):i]; return sum(s)/len(s) if s else 0.0
def future4(i): return sum(conf[i+1:i+5]) if i+5<=n else None

# ── Figure 1: national weekly incidence with dry-season shading ──
fig, ax = plt.subplots(figsize=(11,4))
ax.plot(range(n), conf, color=TEAL, lw=1.4)
ax.fill_between(range(n), conf, alpha=0.15, color=TEAL)
for i in range(n):
    if week[i] <= 17 or week[i] >= 45:
        ax.axvspan(i-0.5, i+0.5, color=AMBER, alpha=0.06, lw=0)
yr_ticks=[i for i in range(n) if week[i]==1]
ax.set_xticks(yr_ticks); ax.set_xticklabels([str(year[i]) for i in yr_ticks])
ax.set_ylabel("Confirmed cases / week"); ax.set_xlim(0,n-1)
ax.set_title("Figure 1  National weekly confirmed Lassa fever cases, Nigeria 2020–2025\n(amber = dry season, Nov–Apr; source: NCDC Weekly Epidemiological Reports)",
             fontsize=11, fontweight="bold")
ax.grid(color="#eee", lw=0.6)
plt.tight_layout(); plt.savefig(OUT/"figure1_national_incidence.png", dpi=300, bbox_inches="tight"); plt.close()

# ── Build model + baseline (identical to build-real-national.py) ──
train_f4=[future4(i) for i in range(n) if year[i]<=2023 and future4(i) is not None]
THRESH=float(np.median(train_f4))
X,y,yrs,roll4v=[],[],[],[]
for i in range(n):
    f4=future4(i)
    if i<8 or f4 is None: continue
    dry=1 if week[i]<=17 or week[i]>=45 else 0
    X.append([lag(i,1),lag(i,2),lag(i,4),lag(i,8),roll(i,4),roll(i,8),roll(i,4)-roll(i,8),week[i],dry])
    y.append(1 if f4>THRESH else 0); yrs.append(year[i]); roll4v.append(roll(i,4))
X,y,yrs,roll4v=np.array(X,float),np.array(y),np.array(yrs),np.array(roll4v)
FEATS=["conf_lag1","conf_lag2","conf_lag4","conf_lag8","roll4","roll8","roll_trend","epi_week","dry_season"]
LABELS=["cases lag1","cases lag2","cases lag4","cases lag8","4-wk mean","8-wk mean","rolling trend","epi week","dry season"]
tr=yrs<=2023; te=yrs==2024
m=xgb.XGBClassifier(n_estimators=300,max_depth=3,learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,
    scale_pos_weight=(y[tr]==0).sum()/max(1,(y[tr]==1).sum()),eval_metric="logloss")
m.fit(X[tr],y[tr]); p=m.predict_proba(X[te])[:,1]

# ── Figure 2: ROC model vs naive baseline ──
f_m,t_m,_=roc_curve(y[te],p); a_m=auc(f_m,t_m)
f_b,t_b,_=roc_curve(y[te],roll4v[te]); a_b=auc(f_b,t_b)
fig,ax=plt.subplots(figsize=(6.2,5.6))
ax.plot(f_m,t_m,color=TEAL,lw=2.5,label=f"XGBoost, 9 features (AUROC={a_m:.3f})")
ax.plot(f_b,t_b,color="#b45309",lw=2,linestyle=(0,(4,2)),label=f"Naive: recent 4-wk mean (AUROC={a_b:.3f})")
ax.plot([0,1],[0,1],"--",color=GREY,lw=1.1,label="Chance (0.50)")
ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
ax.set_title("Figure 2  ROC — model vs naive baseline (2024 hold-out, real data)\nModel exceeds trivial persistence by ~0.03 AUROC",
             fontsize=10.5,fontweight="bold")
ax.legend(loc="lower right",fontsize=9); ax.grid(color="#eee",lw=0.6)
plt.tight_layout(); plt.savefig(OUT/"figure2_roc_baseline.png",dpi=300,bbox_inches="tight"); plt.close()

# ── Figure 3: feature importance ──
imp=sorted(zip(LABELS,m.feature_importances_),key=lambda t:t[1])
fig,ax=plt.subplots(figsize=(7,4.5))
cols=[RED if l=="dry season" else TEAL for l,_ in imp]
ax.barh([l for l,_ in imp],[v*100 for _,v in imp],color=cols)
ax.set_xlabel("Gain importance (%)")
ax.set_title("Figure 3  Feature importance — real national model\nDry-season timing dominates (epidemiologically correct)",
             fontsize=10.5,fontweight="bold")
ax.grid(axis="x",color="#eee",lw=0.6)
plt.tight_layout(); plt.savefig(OUT/"figure3_feature_importance.png",dpi=300,bbox_inches="tight"); plt.close()

# ── Figure 4: seasonality (mean confirmed by epi-week) ──
byw={}
for i in range(n): byw.setdefault(week[i],[]).append(conf[i])
wk=sorted(w for w in byw if w<=52); mean=[np.mean(byw[w]) for w in wk]
fig,ax=plt.subplots(figsize=(9,4))
ax.bar(wk,mean,color=[RED if (w<=17 or w>=45) else TEAL for w in wk])
ax.set_xlabel("Epidemiological week"); ax.set_ylabel("Mean confirmed cases")
ax.set_title("Figure 4  Seasonality of confirmed Lassa fever, Nigeria 2020–2025\n(red = dry season wks 45–17; peak Jan–Mar, matching SORMAS 2018–2021)",
             fontsize=10.5,fontweight="bold")
ax.grid(axis="y",color="#eee",lw=0.6)
plt.tight_layout(); plt.savefig(OUT/"figure4_seasonality.png",dpi=300,bbox_inches="tight"); plt.close()

print(f"Figures written. Model AUROC={a_m:.3f}  Naive AUROC={a_b:.3f}  threshold={THRESH:.0f}  pos_rate={y.mean():.2f}")
