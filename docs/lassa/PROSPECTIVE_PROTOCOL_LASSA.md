# LassaAI National Early-Warning — Prospective Validation Protocol (pre-registration)

**Status: CRITERIA COMMITTED v1.0 (2026-07-13).** The scientific criteria below were set by
the acting Chief Scientist on the author's delegation and are committed as of this git commit
— the commit timestamp is the pre-registration record. They may be amended **only before the
first scored forecast** (tracked as v1.x in git history); **no change is permitted after the
first scored forecast is logged.** The model code-commit hash and dataset content-hash (§2)
are stamped at the *pre-season freeze*, immediately before the first forecast, and must
reference a commit dated before it. The author (Oluwafemi Idiakhoa) retains final sign-off (§15)
and may adjust any committed value before the pre-season freeze.

This document pre-registers — *before outcomes are known* — how the national LassaAI
elevated-transmission model will be judged as a genuine forward forecaster during the
2026–2027 Nigerian Lassa season. It is modeled on the lockbox methodology in
`docs/PROSPECTIVE_VALIDATION_PROTOCOL.md` (the drug-side protocol). The goal is to make the
prospective claim **falsifiable and un-gameable**, not to assert a result.

---

## 1. What is (and is NOT) claimed
LassaAI scores, each week, the probability that the **next 4 weeks** of national confirmed
Lassa burden in Nigeria will be *elevated* (above a pre-frozen threshold). This protocol
evaluates **discrimination and calibration of that forward forecast against naive baselines.**
It does **not** claim clinical/therapeutic efficacy, per-state accuracy, causal insight, or
that a forecast prevents cases. Retrospective performance (out-of-time 2024): AUROC **0.880**
vs naive **0.849** (~0.03 gain). The honest open question this protocol answers: *does the
model beat a trivial seasonal baseline prospectively?*

## 2. Model under evaluation (frozen)
- **Model version:** `national-elevated-transmission-v1`
- **Fitting rule (frozen):** each forecast week, XGBoost is retrained on **all labelled weeks up to the forecast week** (expanding window) using the frozen 9-feature spec and the frozen hyperparameters in `scripts/lassa/national-forecast-now.py`. No manual tuning between weeks. (This rule is automation-safe: it needs no human in the loop.)
- **Feature set (frozen):** `conf_lag1,2,4,8`, `roll4`, `roll8`, `roll_trend`, `epi_week`, `dry_season`.
- **Elevated threshold (FROZEN = 32):** next-4-week confirmed burden **> 32**, the median 4-week burden of the training period (years ≤2023). This value is **fixed for the entire evaluation and never re-derived** from later data.
- **Stamped at the pre-season freeze, before the first forecast:** model code-commit hash `«stamp»` and dataset content-hash (SHA-256 of `lassa_fever_timeseries_full.csv`) `«stamp»`.
- Fitting rule, features, and threshold are frozen; any change = a new protocol version, disclosed in git history.

## 3. Data source, refresh & cadence
- **Source:** NCDC Weekly Epidemiological Reports (national weekly confirmed cases).
- **Refresh:** `scripts/lassa/refresh-national-series.py` (scrape → cumulative-to-weekly → append; gap-safe; cross-checked vs NCDC cumulative).
- **Cadence:** weekly, run **manually or on an automated weekly schedule**. Automation is permitted **only if** it: (a) runs the *same* honesty-guarded logger unchanged; (b) treats the refresh cross-check (§6) and gap/negative-diff detection as a **HARD GATE** — on any anomaly it **aborts and alerts a human, and logs nothing** (a bad scrape must never silently enter the record); (c) uses the frozen fitting rule + threshold (§2); and (d) records each forecast as its own **git commit** (the commit timestamp is the tamper-evident proof the forecast preceded the outcome). No path may write a forecast that bypasses the logger.

## 4. Endpoint definitions
- **Forecast horizon:** 4 weeks ahead of the last observed week.
- **Weekly forecast:** `P(elevated)` = model probability that the sum of confirmed cases over the next 4 ISO weeks exceeds the frozen threshold (§2).
- **Primary endpoint:** prospective **AUROC** of `P(elevated)` vs the realized binary outcome across all scored weeks, **and** the **AUROC gain over the best naive baseline** (§7). Both reported with 95% bootstrap CIs.
- **Co-primary:** **calibration** — Brier score and a reliability curve; Expected Calibration Error (ECE).

## 5. Inclusion / exclusion
- **Include** every ISO week in the evaluation window (§10) for which, *at forecast time*, ≥8 weeks of prior history are available **and** the forecast was logged with `window_is_future = true`.
- **Exclude** weeks that could not be logged before their outcome window began (the logger refuses these).

## 6. Missing-data handling (pre-specified)
- If a required input week is missing at forecast time, no forecast is logged that week; it is recorded as **"not forecastable — missing data,"** and is **not** counted as a hit or miss.
- If an outcome week's sitrep is missing at evaluation, that forecast is **excluded from the primary analysis** and reported separately. Missing weeks are **never** silently interpolated.

## 7. Baselines (pre-specified)
- **Primary baseline:** naive recent-4-week case average (retrospective AUROC 0.849).
- **Secondary baseline:** previous-week case count (0.848).
- Baselines are computed prospectively on the same weeks and logged alongside each forecast.

## 8. Metrics
- **Discrimination:** AUROC (threshold-free). **Calibration:** Brier score + reliability curve + ECE. All vs baselines, with bootstrap 95% CIs.

## 9. Decision threshold / risk bands (operational only; do not affect primary AUROC)
- Alert if `P(elevated) ≥ 0.50`. Risk bands: LOW <0.25, MODERATE 0.25–0.50, HIGH 0.50–0.75, VERY HIGH ≥0.75. Frozen at registration.

## 10. Evaluation window & readout dates (committed)
- **Logging starts:** on or before **2026-10-01** (before dry-season onset), once the series is refreshed to the current epi-week.
- **Primary evaluation window:** dry season, ISO weeks **2026-W45 → 2027-W17** (≈ Nov–Apr).
- **Readouts (published pass / neutral / fail, no cherry-picking):** interim at **2027-W05**; **primary** after **2027-W21** (allowing the last 4-week outcome window to close).

## 11. Success / neutral / failure criteria (committed v1.0)
**The binding test is the gain over the naive baseline (§7), not the absolute AUROC.** Because
elevated weeks are strongly autocorrelated and seasonal, a high *absolute* AUROC is largely
attributable to seasonality that the baseline also captures; the scientific claim is *added
skill over that baseline*.
- **SUCCESS:** prospective AUROC gain over the best naive baseline ≥ **0.02**, with **95% bootstrap CI lower bound > 0**, **and** Brier ≤ the baseline's. (Absolute AUROC ≥ 0.70 is a secondary catastrophic-degradation floor only.)
- **NEUTRAL — a legitimate, published result, and the most likely one given the retrospective gain was only ~0.03:** gain < 0.02, or its CI spans 0 → "no added skill over seasonality."
- **FAILURE:** AUROC below the baseline, **or** absolute AUROC < **0.70**, **or** fewer than **10** scoreable weeks with both outcome classes (reported as inconclusive-underpowered).

## 12. Revised NCDC data (pre-specified)
NCDC revises prior weeks. The **primary analysis uses the values as first published / as-logged** (frozen at log and at evaluation). A **sensitivity analysis** repeats the evaluation on the latest revised values. **Both** are reported; the primary verdict is not changed by later revisions.

## 13. Publication commitment
Results are published at `/validation` and `/lassa`, and in any manuscript update, **regardless of outcome — positive, neutral, or negative** — together with the full append-only forecast log (`data/lassa/national-prospective-log.jsonl`). No cherry-picking. A negative or neutral result will be stated as plainly as a positive one.

## 14. Anti-gaming safeguards & honest limitations
**Enforced by the workflow:** the logger (`national-forecast-logger.py`) refuses to log a forecast whose outcome window is not in the future (`window_is_future`), is append-only, idempotent per (year, week), and stores a SHA-256 of each forecast.
**Limitations (NOT tamper-proof — disclosed honestly):** the log is append-only *by convention*, not WORM; there is no hash-chain linking records; and a direct database/SQL write can bypass the logger entirely. Therefore the pre-registration's integrity rests on the **git commit history of this frozen protocol + the append-only JSONL**, not on cryptographic immutability. Model training data predates the forecasts, but for a purely forward forecast (window strictly in the future) leakage is not applicable to the outcome.

## 15. Sign-off & pre-season freeze
- [x] Scientific criteria (§2 fitting rule + frozen threshold, §10 dates, §11 success/neutral/failure) **committed v1.0** by the acting Chief Scientist on the author's delegation, 2026-07-13.
- [ ] Author (final sign-off): review §11 and amend any value **before** the first scored forecast; amendments are tracked as v1.x in git history.
- [ ] **Pre-season freeze (one-time, before first forecast):** refresh the series to the current epi-week, then stamp the model code-commit hash and dataset SHA-256 in §2 and bring the automated weekly cadence live (§3).
- [ ] After the first scored forecast is logged: **no further changes** to §2, §7, or §11.

*Author:* Oluwafemi Idiakhoa · *Contact:* partnerships@gailabai.com
