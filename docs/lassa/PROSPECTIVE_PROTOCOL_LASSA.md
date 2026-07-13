# LassaAI National Early-Warning — Prospective Validation Protocol (pre-registration)

**Status: DRAFT v0.1 — NOT YET FROZEN.** Values marked **«CONFIRM»** are proposed by the
analyst and must be reviewed, adjusted, and confirmed by the author before this protocol is
frozen. Freezing = committing a version with `Status: FROZEN v1.0` and the hashes in §2; the
git commit timestamp is the pre-registration record. Nothing here is binding until frozen,
and freezing must occur **before** any prospective forecast is scored.

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

## 2. Model under evaluation (frozen at registration)
- **Model version:** `national-elevated-transmission-v1`
- **Code commit hash:** «CONFIRM — fill the `git rev-parse HEAD` at freeze»
- **Feature set (frozen):** 9 features — `conf_lag1,2,4,8`, `roll4`, `roll8`, `roll_trend`, `epi_week`, `dry_season` (see `scripts/lassa/build-real-national.py`)
- **Training data:** national weekly series 2020–2025 (`data/lassa/lassa_fever_timeseries_full.csv`), content hash «CONFIRM — SHA-256 at freeze»
- **Elevated threshold (frozen):** next-4-week confirmed burden **> 32** (median 4-week burden of the training period, years ≤2023). **«CONFIRM»** — freeze the exact integer.
- The model and threshold are **frozen**; any change after freeze = a new protocol version, disclosed in git history.

## 3. Data source & refresh
- **Source:** NCDC Weekly Epidemiological Reports (national weekly confirmed cases).
- **Refresh:** `scripts/lassa/refresh-national-series.py` (scrape → cumulative-to-weekly → append; gap-safe; cross-checked vs NCDC cumulative). Run weekly before forecasting.

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

## 10. Evaluation window & readout dates (pre-specified) — **«CONFIRM»**
- **Logging starts:** «CONFIRM — target on/before 2026-10-01, before dry-season onset».
- **Primary evaluation window:** dry season, ISO weeks 2026-W45 → 2027-W17 (≈ Nov–Apr).
- **Readouts (published pass/fail/neutral, no cherry-picking):** interim at 2027-W05; **primary** after 2027-W21 (allowing the last 4-week outcome window to close).

## 11. Success / neutral / failure criteria — **«CONFIRM: author owns these thresholds»**
*Proposed, principled defaults (modest, consistent with the ~0.88/+0.03 retrospective result and allowing for prospective degradation). The author must confirm or change these before freeze.*
- **SUCCESS:** prospective AUROC ≥ **0.75** **and** AUROC exceeds the best naive baseline by ≥ **0.02** (95% CI lower bound of the gain > 0) **and** Brier ≤ the baseline's.
- **NEUTRAL / no added skill (a legitimate, publishable result):** model AUROC ≈ baseline (gain < 0.02, or CI of the gain spans 0) — i.e., seasonality explains the signal.
- **FAILURE:** prospective AUROC < baseline, **or** AUROC < **0.70**, **or** fewer than **10** scoreable weeks with both outcome classes (insufficient power — reported as inconclusive-underpowered).

## 12. Revised NCDC data (pre-specified)
NCDC revises prior weeks. The **primary analysis uses the values as first published / as-logged** (frozen at log and at evaluation). A **sensitivity analysis** repeats the evaluation on the latest revised values. **Both** are reported; the primary verdict is not changed by later revisions.

## 13. Publication commitment
Results are published at `/validation` and `/lassa`, and in any manuscript update, **regardless of outcome — positive, neutral, or negative** — together with the full append-only forecast log (`data/lassa/national-prospective-log.jsonl`). No cherry-picking. A negative or neutral result will be stated as plainly as a positive one.

## 14. Anti-gaming safeguards & honest limitations
**Enforced by the workflow:** the logger (`national-forecast-logger.py`) refuses to log a forecast whose outcome window is not in the future (`window_is_future`), is append-only, idempotent per (year, week), and stores a SHA-256 of each forecast.
**Limitations (NOT tamper-proof — disclosed honestly):** the log is append-only *by convention*, not WORM; there is no hash-chain linking records; and a direct database/SQL write can bypass the logger entirely. Therefore the pre-registration's integrity rests on the **git commit history of this frozen protocol + the append-only JSONL**, not on cryptographic immutability. Model training data predates the forecasts, but for a purely forward forecast (window strictly in the future) leakage is not applicable to the outcome.

## 15. Freeze / sign-off (to be completed by the author)
- [ ] Author has reviewed and confirmed/adjusted all **«CONFIRM»** items (§2, §10, §11).
- [ ] Threshold, model version, code commit hash, and dataset hash filled in §2.
- [ ] Status changed to `FROZEN v1.0` and committed **before** the first scored forecast.

*Author:* Oluwafemi Idiakhoa · *Contact:* partnerships@gailabai.com
