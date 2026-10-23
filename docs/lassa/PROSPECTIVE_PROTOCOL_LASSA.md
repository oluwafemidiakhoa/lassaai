# LassaAI National Early-Warning — Prospective Validation Protocol (pre-registration)

**Status: CRITERIA COMMITTED v1.1 (pre-freeze amendment 2026-09-22).** The original
v1.0 scientific criteria were committed on 2026-07-13 before prospective outcomes were known.
Before any scored 2026–27 forecast was logged, the pre-freeze challenger audit exposed a
scientific weakness in the original comparator set: persistence alone was not a sufficiently
strong test for a highly seasonal disease. v1.1 therefore **strengthens the benchmark** by
adding explicit seasonal and seasonal+persistence comparators and dependence-aware paired
uncertainty. The model endpoint remains >32 confirmed cases over the next four weeks.
The git history preserves both versions. **No change is permitted after the first scored
forecast is logged.** The model code-commit
hash and dataset content-hash (§2) are stamped at the *pre-season freeze*, immediately before
the first forecast, and must reference a commit dated before it. **Scientific responsibility,
approval, and final sign-off remain with the accountable human researcher (§15).** AI
systems may assist with analysis, coding, checking, and documentation, but they do not approve,
amend, or sign off on this protocol.

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
vs naive **0.849** (~0.03 gain). The honest open question this protocol answers is: *does the model add forward skill beyond
both persistence and explicit seasonality prospectively?*

## 2. Model under evaluation (frozen)
- **Model version:** `national-elevated-transmission-v1`
- **Fitting rule (frozen):** each forecast week, XGBoost is retrained on **all labelled weeks up to the forecast week** (expanding window) using the frozen 9-feature spec and the frozen hyperparameters in `scripts/lassa/national-forecast-now.py`. No manual tuning between weeks. (This rule is automation-safe: it needs no human in the loop.)
- **Runtime environment (frozen):** Python **3.11.x**, with exact package pins in `scripts/lassa/prospective-requirements.txt`: `numpy==1.26.4`, `scikit-learn==1.4.2`, `xgboost==2.0.3`. The exact Python 3.11 patch version and platform are recorded in the one-time freeze manifest. A scored forecast generated under a different frozen package set is rejected by the logger.
- **Feature set (frozen):** `conf_lag1,2,4,8`, `roll4`, `roll8`, `roll_trend`, `epi_week`, `dry_season`.
- **Elevated threshold (FROZEN = 32):** next-4-week confirmed burden **> 32**, the median 4-week burden of the training period (years ≤2023). This value is **fixed for the entire evaluation and never re-derived** from later data.
- **Stamped at the pre-season freeze, before the first scored forecast:** the one-time manifest `data/lassa/lassa-national-2026-27-freeze.json` records the reviewed git commit plus SHA-256 hashes of this protocol, the forecast code, logger, outcome recorder, prospective readout code, exact prospective environment lock, and the pre-season dataset snapshot. The protocol text is not self-edited to insert those hashes, because doing so would change the protocol hash it is meant to freeze.
- Fitting rule, features, and threshold are frozen; any change = a new protocol version, disclosed in git history.

## 3. Data source, refresh & cadence
- **Source:** NCDC Weekly Epidemiological Reports (national weekly confirmed cases).
- **Refresh:** `scripts/lassa/refresh-national-series.py` (scrape → cumulative-to-weekly → append; gap-safe; cross-checked vs NCDC cumulative).
- **Cadence:** weekly, run **manually or on an automated weekly schedule**. Automation is permitted **only if** it: (a) runs the *same* honesty-guarded logger unchanged; (b) treats the refresh cross-check (§6) and gap/negative-diff detection as a **HARD GATE** — on any anomaly it **aborts and alerts a human, and logs nothing** (a bad scrape must never silently enter the record); (c) uses the frozen fitting rule + threshold (§2); (d) passes the freeze-manifest hash checks before logging; and (e) commits the resulting forecast-log record to git before the outcome window can resolve. An external proof-of-anteriority anchor may strengthen that record, but must never be claimed unless its verifier succeeds. No path may write a scored forecast that bypasses the logger.

## 4. Endpoint definitions
- **Forecast horizon:** 4 weeks ahead of the last observed week.
- **Weekly forecast:** `P(elevated)` = model probability that the sum of confirmed cases over the next 4 ISO weeks exceeds the frozen threshold (§2).
- **Primary endpoint:** prospective **AUROC** of `P(elevated)` vs the realized binary outcome across all scored weeks, **and** the **AUROC gain over the strongest pre-specified comparator** (§7). Added-skill uncertainty uses the paired moving-block procedure in §8.
- **Co-primary:** **calibration** — Brier score and a reliability curve; Expected Calibration Error (ECE).

## 5. Inclusion / exclusion
- **Include** every ISO week in the evaluation window (§10) for which, *at forecast time*, ≥8 weeks of prior history are available **and** the forecast was logged with `window_is_future = true`.
- **Exclude** weeks that could not be logged before their outcome window began (the logger refuses these).

## 6. Missing-data handling (pre-specified)
- If a required input week is missing at forecast time, no forecast is logged that week; it is recorded as **"not forecastable — missing data,"** and is **not** counted as a hit or miss.
- If an outcome week's sitrep is missing at evaluation, that forecast is **excluded from the primary analysis** and reported separately. Missing weeks are **never** silently interpolated.

## 7. Baselines and confirmatory comparators (pre-specified)
The original v1.0 persistence baselines remain in place:
- **Primary persistence baseline:** recent-4-week case average (retrospective 2024 AUROC 0.849).
- **Secondary persistence baseline:** previous-week case count (retrospective 2024 AUROC 0.848).

v1.1 adds two stronger comparators, fixed before the first scored forecast:
- **Seasonal climatology:** logistic regression using first- and second-harmonic sine/cosine terms of epidemiological week.
- **Seasonal + persistence:** standardized logistic regression using the same four harmonic terms plus recent-4-week average, previous-week count, and the roll4-minus-roll8 trend.

Both seasonal comparators are refit mechanically on labelled history available before each
forecast, under the same expanding-window information boundary as the model. They are logged
alongside every scored forecast. No future outcome may enter their fit.

For the binding added-skill claim, the comparison is against the **best pre-specified
comparator by AUROC on the same scoreable prospective weeks** among these four baselines.
This is intentionally stricter than the original v1.0 persistence-only comparison.

## 8. Metrics and dependence-aware uncertainty
- **Discrimination:** AUROC (threshold-free).
- **Calibration method (frozen):** the model uses its raw XGBoost `predict_proba` output with **no post-hoc recalibration during the prospective season**. Persistence-baseline probabilities use a one-feature logistic calibration fit only on the frozen ≤2023 era. Seasonal comparators use their native logistic-regression probabilities.
- **Calibration metrics (frozen):** Brier score + reliability curve + ECE using **5 equal-width probability bins over [0,1]**; the reliability curve uses the same five bins.
- **Primary paired uncertainty:** moving-block bootstrap of model-minus-comparator AUROC and Brier differences with **4-week blocks**, reflecting the overlapping four-week outcome horizon.
- **Sensitivity uncertainty:** repeat the paired moving-block bootstrap with **8-week blocks**.
- **Bootstrap implementation (frozen):** **4,000 requested replicates**, deterministic seed **20260922**. The readout code is `scripts/lassa/prospective-readout.py`, and its SHA-256 is recorded in the pre-season freeze manifest.
- Ordinary iid bootstrap intervals are not the binding uncertainty analysis for the added-skill claim because adjacent outcomes overlap.

## 9. Decision threshold / risk bands (operational only; do not affect primary AUROC)
- Alert if `P(elevated) ≥ 0.50`. Risk bands: LOW <0.25, MODERATE 0.25–0.50, HIGH 0.50–0.75, VERY HIGH ≥0.75. Frozen at registration.

## 10. Evaluation window & readout dates (committed)
- **Logging starts:** on or before **2026-10-01** (before dry-season onset), once the series is refreshed to the current epi-week.
- **Primary evaluation window:** dry season, forecast issue/data-through ISO weeks **2026-W45 → 2027-W17** (≈ Nov–Apr). This week key is the `data_through` week stored in each immutable forecast record.
- **Readouts (published pass / neutral / fail, no cherry-picking):** interim at **2027-W05**; **primary** after **2027-W21** (allowing the last 4-week outcome window to close).

## 11. Success / neutral / failure criteria (committed v1.1)
**The binding test is added skill over the strongest pre-specified comparator (§7), not
absolute AUROC.** A high absolute AUROC can be generated largely by seasonality and
autocorrelation; the scientific claim is whether the model contributes information beyond
those simpler structures.
- **SUCCESS:** prospective AUROC gain over the best pre-specified comparator ≥ **0.02**, with the **4-week paired moving-block bootstrap 95% CI lower bound > 0**, **and** Brier score no worse than that comparator's. Absolute AUROC ≥ **0.70** remains only a catastrophic-degradation floor. The 8-week block analysis is reported as a required sensitivity check.
- **NEUTRAL / INCONCLUSIVE:** any result that is neither SUCCESS nor FAILURE, including gain < **0.02**, the binding 4-week paired interval spanning 0, **or** Brier score worse than the strongest comparator despite otherwise favorable discrimination → **no demonstrated added skill beyond the strongest comparator under the full pre-specified contract**. Fewer than **10** scoreable weeks, or absence of both outcome classes, is reported specifically as **inconclusive-underpowered** and does not count as evidence that the model failed.
- **FAILURE:** with a scoreable evaluation containing both outcome classes, model AUROC is below the strongest comparator, **or** absolute AUROC < **0.70**. This is the pre-specified refuting outcome.

## 12. Revised NCDC data (pre-specified)
NCDC revises prior weeks. The **primary analysis uses the values as first published / as-logged** (frozen at log and at evaluation). A **sensitivity analysis** repeats the evaluation on the latest revised values. **Both** are reported; the primary verdict is not changed by later revisions.

## 13. Publication commitment
Results are published at `/validation` and `/lassa`, and in any manuscript update, **regardless of outcome — positive, neutral, or negative** — together with the full append-only forecast log (`data/lassa/national-prospective-log.jsonl`). No cherry-picking. A negative or neutral result will be stated as plainly as a positive one.

## 14. Anti-gaming safeguards & honest limitations
**Enforced by the workflow:** before a scored record can be appended, the logger requires the one-time pre-season freeze manifest and verifies the frozen hashes of this protocol, forecast code, logger, and outcome recorder. It also refuses a forecast whose outcome window is not in the future (`window_is_future`), is idempotent per (year, week), and links every forecast record to the previous record by SHA-256. Outcomes are written to a separate hash-chained ledger keyed to the original forecast-record hash.
**Limitations (tamper-evident, not WORM):** a JSONL hash chain detects alteration relative to a previously observed/committed chain head; it does not prevent a repository administrator from rewriting both a file and repository history. The git commit containing each forecast record is therefore part of the anteriority record. An independently verifiable external timestamp/anchor is stronger still, but is evidence of timing only—not scientific correctness—and is not claimed unless its verifier succeeds.

## 15. Human sign-off & pre-season freeze
- [x] Original scientific criteria committed as **v1.0 on 2026-07-13**.
- [x] **v1.1 pre-freeze amendment on 2026-09-22:** stronger seasonal comparators + paired moving-block uncertainty added before any scored 2026–27 forecast; endpoint/model family unchanged.
- [x] **Accountable human researcher final sign-off (2026-09-22):** the accountable human researcher explicitly confirmed: “I have reviewed the LassaAI National Early-Warning Prospective Validation Protocol v1.1, including §11. I approve the scientific design and give my final accountable-human-researcher sign-off for the 2026–27 prospective study freeze.” No scientific value may now be silently changed before or after the first scored forecast; any later methodological change requires a new explicitly versioned study.
- [ ] **Pre-season freeze (one-time, before first scored forecast):** refresh and manually review the national series to the current epi-week; run the final code/test audit; generate `data/lassa/lassa-national-2026-27-freeze.json`; review and commit that manifest; then permit weekly scored logging under §3.
- [ ] After the first scored forecast is logged: **no further changes** to §2, §7, §8, or §11.
- [ ] AI systems have **no scientific sign-off authority** under this protocol; their role is limited to computational assistance, implementation, verification support, and documentation.

*Accountability:* final scientific sign-off was explicitly provided by the accountable human researcher on 2026-09-22. AI systems recorded that decision but did not make or substitute for it.
