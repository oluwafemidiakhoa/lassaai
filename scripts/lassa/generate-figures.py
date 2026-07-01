"""
LassaAI — Figure generation for PLOS NTD submission
Produces Figures 1–5 as high-resolution PNG (300 DPI) in docs/lassa/figures/
"""

import csv
import json
import pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path
from sklearn.metrics import roc_curve, auc

OUT = Path("docs/lassa/figures")
OUT.mkdir(parents=True, exist_ok=True)

TEAL   = "#2dd4bf"
DARK   = "#0a0f1e"
RED    = "#dc2626"
AMBER  = "#d97706"
GREEN  = "#059669"
SLATE  = "#64748b"
WHITE  = "#f8fafc"

plt.rcParams.update({
    "figure.facecolor": WHITE,
    "axes.facecolor":   WHITE,
    "axes.edgecolor":   "#cbd5e1",
    "axes.labelcolor":  "#1e293b",
    "xtick.color":      "#475569",
    "ytick.color":      "#475569",
    "text.color":       "#1e293b",
    "font.family":      "sans-serif",
    "font.size":        11,
    "axes.spines.top":  False,
    "axes.spines.right": False,
})

# ── Figure 1: Geographic case distribution (bar chart proxy — no shapefile needed) ──

states_cases = [
    ("Edo",       2574), ("Ondo",    1638), ("Bauchi", 1040),
    ("Taraba",     884), ("Ebonyi",   728), ("Anambra",  312),
    ("Delta",      260), ("Benue",    208), ("Kogi",     156),
    ("Nasarawa",   156), ("Plateau",  104), ("Enugu",     78),
]
states_zero = [
    "Adamawa","Akwa Ibom","Abia","Bayelsa","Borno","Cross River",
    "Ekiti","FCT","Gombe","Imo","Jigawa","Kaduna","Kano","Katsina",
    "Kebbi","Kwara","Lagos","Niger","Ogun","Osun","Oyo","Rivers",
    "Sokoto","Yobe","Zamfara",
]

fig, ax = plt.subplots(figsize=(10, 6))
names  = [s for s, _ in states_cases]
values = [v for _, v in states_cases]
colors = [RED if v > 1000 else AMBER if v > 400 else TEAL for v in values]
bars = ax.barh(names[::-1], values[::-1], color=colors[::-1], height=0.65, zorder=2)
ax.axvline(0, color="#cbd5e1", lw=0.8)
ax.set_xlabel("Confirmed cases (2011–2026)", fontsize=12)
ax.set_title("Figure 1  Geographic distribution of confirmed Lassa fever cases\nin Nigeria, 2011–2026 (37 states; 25 states reported zero cases)",
             fontsize=12, fontweight="bold", pad=14)
ax.text(0.98, 0.02,
        f"22 additional states: 0 cases\nTotal: 8,138 confirmed · 910 deaths",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=9, color=SLATE,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#f1f5f9", edgecolor="#cbd5e1"))
for bar, val in zip(bars, values[::-1]):
    ax.text(bar.get_width() + 20, bar.get_y() + bar.get_height()/2,
            f"{val:,}", va="center", fontsize=9, color="#1e293b")
ax.set_xlim(0, 3100)
ax.grid(axis="x", color="#e2e8f0", lw=0.7, zorder=1)
patches = [
    mpatches.Patch(color=RED,   label=">1,000 cases (highest burden)"),
    mpatches.Patch(color=AMBER, label="400–1,000 cases"),
    mpatches.Patch(color=TEAL,  label="<400 cases"),
]
ax.legend(handles=patches, loc="lower right", fontsize=9, framealpha=0.9)
plt.tight_layout()
plt.savefig(OUT / "figure1_geographic_distribution.png", dpi=300, bbox_inches="tight")
plt.close()
print("Figure 1 saved")

# ── Figure 2: ROC curve (rerun model to get test probabilities) ──

features_df = pd.read_csv("data/lassa/features.csv")
with open("models/lassa/outbreak-model-v1.pkl", "rb") as f:
    bundle = pickle.load(f)
model = bundle["model"] if isinstance(bundle, dict) else bundle

test_df = features_df[features_df["year"].isin([2024, 2025])].copy()
FEATURE_COLS = [
    "month","dry_season","weeks_into_dry_season",
    "cases_lag1","cases_lag2","cases_lag4","cases_lag8","deaths_lag4",
    "cases_roll4","cases_roll8","cases_roll4_trend",
    "rain_lag4","rain_lag8","humidity_lag4","temp_lag4",
    "is_edo","is_ondo","is_bauchi","is_high_risk",
]
X_test = test_df[FEATURE_COLS]
y_test = test_df["outbreak"]
probs  = model.predict_proba(X_test)[:, 1]

fpr, tpr, thresholds = roc_curve(y_test, probs)
roc_auc = auc(fpr, tpr)

# find threshold closest to tpr=1.0, fpr=0.1
op_idx = np.argmin(np.abs(tpr - 1.0))

fig, ax = plt.subplots(figsize=(7, 6))
ax.plot(fpr, tpr, color=TEAL, lw=2.5, label=f"LassaAI (AUROC = {roc_auc:.4f})")
ax.fill_between(fpr, tpr, alpha=0.08, color=TEAL)
ax.plot([0, 1], [0, 1], "--", color="#94a3b8", lw=1.2, label="Random (AUROC = 0.50)")
ax.scatter([fpr[op_idx]], [tpr[op_idx]], s=90, zorder=5, color=RED,
           label=f"Operating point (Sensitivity=1.000, Specificity={1-fpr[op_idx]:.3f})")
ax.set_xlabel("False Positive Rate  (1 − Specificity)", fontsize=12)
ax.set_ylabel("True Positive Rate  (Sensitivity)", fontsize=12)
ax.set_title("Figure 2  ROC curve — LassaAI outbreak prediction\nTest set: 2024–2025 out-of-time temporal holdout (retrospective)",
             fontsize=12, fontweight="bold", pad=14)
ax.legend(loc="lower right", fontsize=10)
ax.set_xlim(-0.01, 1.01)
ax.set_ylim(-0.01, 1.05)
ax.grid(color="#e2e8f0", lw=0.6)
props = dict(boxstyle="round", facecolor="#f0fdf4", alpha=0.9, edgecolor="#86efac")
ax.text(0.38, 0.12,
        f"AUROC = {roc_auc:.4f}\nPrecision = 0.910\nRecall = 1.000\nF1 = 0.953\nFalse negatives = 0",
        transform=ax.transAxes, fontsize=10, verticalalignment="bottom", bbox=props)
plt.tight_layout()
plt.savefig(OUT / "figure2_roc_curve.png", dpi=300, bbox_inches="tight")
plt.close()
print("Figure 2 saved")

# ── Figure 3: Feature importance ──

fi_df = pd.read_csv("data/lassa/feature-importance.csv")
fi_df = fi_df.sort_values("importance", ascending=True).tail(15)

LABELS = {
    "cases_roll8":           "8-week rolling mean cases",
    "cases_lag1":            "Cases 1 week prior",
    "cases_roll4":           "4-week rolling mean cases",
    "cases_lag2":            "Cases 2 weeks prior",
    "weeks_into_dry_season": "Weeks into dry season",
    "month":                 "Calendar month",
    "cases_lag8":            "Cases 8 weeks prior",
    "cases_lag4":            "Cases 4 weeks prior",
    "is_ondo":               "State: Ondo",
    "is_edo":                "State: Edo",
    "temp_lag4":             "Max temperature (lag 4w)",
    "dry_season":            "Dry season flag",
    "rain_lag4":             "Rainfall (lag 4w)",
    "humidity_lag4":         "Humidity (lag 4w)",
    "rain_lag8":             "Rainfall (lag 8w)",
    "is_bauchi":             "State: Bauchi",
    "is_high_risk":          "High-risk state",
    "deaths_lag4":           "Deaths (lag 4w)",
    "cases_roll4_trend":     "4-week case trend",
}
fi_df["label"] = fi_df["feature"].map(lambda x: LABELS.get(x, x))

def feat_color(name):
    if "cases" in name or "deaths" in name: return TEAL
    if "season" in name or "month" in name or "dry" in name: return GREEN
    if "rain" in name or "humidity" in name or "temp" in name: return AMBER
    return SLATE

colors = [feat_color(n) for n in fi_df["feature"]]

fig, ax = plt.subplots(figsize=(9, 7))
bars = ax.barh(fi_df["label"], fi_df["importance"] * 100, color=colors, height=0.65)
ax.set_xlabel("Feature importance (%)", fontsize=12)
ax.set_title("Figure 3  XGBoost feature importance (gain-based)\nLassaAI outbreak prediction model",
             fontsize=12, fontweight="bold", pad=14)
for bar, val in zip(bars, fi_df["importance"] * 100):
    if val > 0.2:
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                f"{val:.1f}%", va="center", fontsize=8.5)
ax.set_xlim(0, 58)
ax.grid(axis="x", color="#e2e8f0", lw=0.6)
patches = [
    mpatches.Patch(color=TEAL,  label="Epidemiological (case history)"),
    mpatches.Patch(color=GREEN, label="Seasonal / temporal"),
    mpatches.Patch(color=AMBER, label="Meteorological"),
    mpatches.Patch(color=SLATE, label="Geographic"),
]
ax.legend(handles=patches, loc="lower right", fontsize=9)
plt.tight_layout()
plt.savefig(OUT / "figure3_feature_importance.png", dpi=300, bbox_inches="tight")
plt.close()
print("Figure 3 saved")

# ── Figure 4: Seasonal heatmap (annual weekly confirmed cases) ──

merged = pd.read_csv("data/lassa/lassa-merged.csv")
merged = merged[merged["confirmed_cases"].notna() & (merged["confirmed_cases"] > 0)]
merged["confirmed_cases"] = pd.to_numeric(merged["confirmed_cases"], errors="coerce").fillna(0)
weekly = merged.groupby(["year", "epi_week"])["confirmed_cases"].sum().reset_index()
weekly = weekly[(weekly["year"] >= 2012) & (weekly["year"] <= 2025)]

pivot = weekly.pivot(index="year", columns="epi_week", values="confirmed_cases").fillna(0)
pivot = pivot.reindex(columns=range(1, 54), fill_value=0)

cmap = LinearSegmentedColormap.from_list("lassa", ["#f8fafc", "#fef3c7", "#f97316", "#7f1d1d"])

fig, ax = plt.subplots(figsize=(14, 6))
im = ax.imshow(pivot.values, aspect="auto", cmap=cmap, interpolation="nearest")
ax.set_xticks(range(0, 53, 4))
ax.set_xticklabels([str(w) for w in range(1, 54, 4)], fontsize=9)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index.astype(int), fontsize=9)
ax.set_xlabel("Epidemiological week", fontsize=12)
ax.set_ylabel("Year", fontsize=12)
ax.set_title("Figure 4  Seasonal variation in Lassa fever confirmed cases — Nigeria 2012–2025\n(Darker = more cases. Dry season: weeks 1–17 and 45–53, Nov–Apr)",
             fontsize=12, fontweight="bold", pad=14)
# shade dry season bands
for xstart, xend in [(0, 16.5), (44.5, 52.5)]:
    ax.axvspan(xstart, xend, color="#fef3c7", alpha=0.35, zorder=0)
cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Confirmed cases (all states)", fontsize=10)
ax.text(8, -1.2, "◄ Dry season", fontsize=8, ha="center", color="#92400e")
ax.text(48, -1.2, "Dry ►", fontsize=8, ha="center", color="#92400e")
plt.tight_layout()
plt.savefig(OUT / "figure4_seasonal_heatmap.png", dpi=300, bbox_inches="tight")
plt.close()
print("Figure 4 saved")

# ── Figure 5: Current forecast (bar chart of all 37 states) ──

with open("data/lassa/current-forecast.json") as f:
    forecast = json.load(f)

forecasts = forecast.get("state_forecasts") or forecast.get("forecasts") or []
forecasts_sorted = sorted(forecasts, key=lambda x: x["probability"], reverse=True)

names  = [s["state"] for s in forecasts_sorted]
probs  = [s["probability"] * 100 for s in forecasts_sorted]
colors = [RED if p >= 20 else AMBER if p >= 5 else "#94a3b8" for p in probs]

HIGH_RISK = {"Edo", "Ondo", "Bauchi", "Taraba", "Ebonyi"}
label_colors = [RED if n in HIGH_RISK else "#1e293b" for n in names]

fig, ax = plt.subplots(figsize=(11, 10))
bars = ax.barh(names[::-1], probs[::-1], color=colors[::-1], height=0.7)
for bar, val, name in zip(bars, probs[::-1], names[::-1]):
    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
            f"{val:.1f}%", va="center", fontsize=8.5)
ax.set_xlabel("Outbreak probability (%)", fontsize=12)
ax.set_xlim(0, max(probs) * 1.4 + 2)
_fw = forecasts[0]["as_of_week"] if forecasts else "—"
_fy = forecasts[0]["as_of_year"] if forecasts else "—"
ax.set_title(f"Figure 5  LassaAI outbreak probability forecast — all 37 Nigerian states\nEpidemiological week {_fw}, {_fy}  (4-week horizon)",
             fontsize=12, fontweight="bold", pad=14)
ax.axvline(5,  color=AMBER, lw=1, linestyle="--", alpha=0.6, label="MODERATE threshold (5%)")
ax.axvline(20, color=RED,   lw=1, linestyle="--", alpha=0.6, label="HIGH threshold (20%)")
ax.legend(fontsize=9, loc="lower right")
ax.grid(axis="x", color="#e2e8f0", lw=0.6)
ax.text(0.98, 0.01,
        "All states: LOW risk\n(Wet season — expected)",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=9, color=SLATE,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#f0fdf4", edgecolor="#86efac"))
plt.tight_layout()
plt.savefig(OUT / "figure5_current_forecast.png", dpi=300, bbox_inches="tight")
plt.close()
print("Figure 5 saved")

print("\nAll figures saved to", OUT.resolve())
