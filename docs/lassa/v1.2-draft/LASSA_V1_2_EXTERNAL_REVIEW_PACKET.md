# LassaAI v1.2 — External Pre-Freeze Review Packet

**Written for:** an independent statistician, epidemiologist or infectious-disease researcher with
no stake in this project.

**What we want from you: attack this protocol.** We are not asking you to endorse GaiaLab, and a
favourable review is not the useful outcome. The useful outcome is the specific reason this design
would not survive peer review, or would produce a number that cannot mean what it appears to mean.
If you think the whole framing is wrong, that is the most valuable answer you can give.

**Nothing is frozen.** No forecast has been issued, no study is active, no manifest exists. The
protocol can still be changed in any respect, including abandoned. Once it is frozen it cannot,
which is why this review happens now.

Time required: about 60–90 minutes for the ten questions. Deeper dives are welcome but optional.

---

## 1. What is being proposed

A prospective, pre-registered test of whether a frozen machine-learning model can predict
**elevated national Lassa fever burden in Nigeria** over a **fully future four-week window**,
better than pre-specified naive baselines, judged by probability quality rather than accuracy.

| Element | Proposed value |
|---|---|
| Lead offset | **L = 4** weeks from the last officially published data week |
| Target | ISO weeks t+4 … t+7 (four full weeks) |
| Endpoint | confirmed cases over the target window **> 32** |
| Eligibility | `issued_at < 00:00:00Z` on the Monday of week t+4 (strict) |
| Base model | XGBoost, 9 features, fitted on epi-years **≤ 2022**, no per-lead tuning |
| Calibrator | Platt scaling fitted on **2023 only**, then frozen and never refit |
| Primary endpoint | paired **Brier-score difference** vs the strongest pre-specified comparator |
| Comparators | recent-4-week persistence; lag-1 persistence; harmonic seasonal climatology; seasonal+persistence logistic |
| Uncertainty | paired moving-block bootstrap, 4-week blocks (8-week sensitivity) |
| Evaluation data never used for fitting or selection | 2024 (untouched), 2025 (reserved) |

Threshold 32 is the median four-week target burden over the ≤2023 development era, and it is
unchanged at every lead tested (L=2,3,4,5).

## 2. Where the numbers come from

All figures were produced by committed scripts in a pinned environment (Python 3.11.16, numpy
1.26.4, scikit-learn 1.4.2, xgboost 2.0.3) and read from CI runs, not from a developer machine.
Everything below is **retrospective**. No prospective skill has been demonstrated, and none is
claimed.

**Calibration at L=4, pooled 2024 + reserved 2025 (n=104):**

| Variant | AUROC | Brier | ECE(5) | Log loss |
|---|---:|---:|---:|---:|
| raw | 0.8097 | 0.2490 | 0.2796 | 0.9381 |
| **Platt** | 0.8097 | **0.1602** | **0.1463** | **0.4832** |
| isotonic | 0.7988 | 0.2264 | 0.1892 | 1.8543 |

**Paired Brier differences at L=4 (model − comparator; negative favours the model):**

| Comparator | Brier 95% interval |
|---|---|
| lag-1 persistence | [−0.1040, **−0.0013**] |
| recent-4 | [−0.1164, −0.0108] |
| seasonal | [−0.1580, −0.0186] |
| seasonal+persistence | [−0.1584, −0.0173] |

**Cohort precision by size** (paired moving-block bootstrap; "below 0" = 95% interval entirely
below zero):

| N | ≈ seasons | lag-1 | recent-4 | seasonal | seasonal+persistence |
|---:|---:|---|---|---|---|
| 53 | 4.0 | crosses | crosses | crosses | crosses |
| 80 | 6.1 | crosses | below 0 | below 0 | below 0 |
| 106 | 8.0 | below 0 | below 0 | below 0 | below 0 |
| 150 | 11.4 | below 0 | below 0 | below 0 | below 0 |

Realistic prospective yield is **≈13.2 eligible forecasts per 25-week dry season**, because NCDC
publishes in batches: 11 of 19 observed 2026 release timestamps covered more than one week, and
only the latest information boundary in a batch may be forecast.

## 3. Things we think are weak, stated before you ask

We would rather hand you these than have you find them and wonder what else is missing.

1. **The lag-1 result is thin.** The upper bound is −0.0013. On 104 retrospective observations,
   against the hardest comparator, that is barely distinguishable from zero.
2. **The favourable result depends entirely on the calibrator.** The *uncalibrated* model at L=4 is
   worse than all four comparators on Brier (lag-1 +0.0495). Platt is doing the work.
3. **Platt is not uniformly better.** In **2024 alone it is worse than raw on both Brier (0.1232 vs
   0.1153) and ECE (0.1430 vs 0.1311)**. The whole pooled gain comes from 2025, where raw
   calibration collapses. It is a robustness measure against bad years, not a general improvement.
4. **The publication-lag evidence is a proxy.** Lag is measured by HTTP `Last-Modified`, an
   upload-time proxy, not first-publication time. It is good enough to rule L=2 out (0 of 36
   observed weeks would have been eligible) and to rank leads; it is not publication truth, and we
   refuse to treat it as such. This is the open blocker to freezing the lead.
5. **L=4 does not cover the measured lag tail.** It tolerates 21 days against an observed p90 of
   25 and a maximum of 44, so some releases will be refused as ineligible.
6. **A previous version of this protocol was wrong in a way we did not catch for a month.** The
   original lead choice rested on a "six-day publication lag" that was a week-boundary subtraction
   artifact — all seven observations showed exactly 6 days with zero variance, which should have
   been the tell. A study frozen on it would have logged zero eligible forecasts. That is also why
   we are asking for outside review before freezing rather than after.
7. **Reserved-2025 Platt ECE is 0.3064.** Calibration on a single bad season is poor even after
   Platt.
8. **The one-season yield (~13) is far below the 104 retrospective observations**, so prospective
   intervals will be much wider than the historical ones for many years.

## 4. The proposed study structure

Because at four seasons *nothing* clears zero — not even the climatological baselines — and
because the "strongest comparator" rule makes lag-1 the binding comparator, we propose two
explicitly separate phases, **both declared before activation**:

- **Phase 1 — integrity cohort (4 dry seasons, ≈53 forecasts).** Pre-declared **underpowered** and
  **incapable of returning a superiority verdict**. It tests the instrument prospectively: every
  forecast issued before its target opened, every refusal recorded, hash chain unbroken, nothing
  rewritten, calibrator unchanged, and the realised yield compared against the ~13.2/season
  assumption. Descriptive results published with intervals, labelled interim.
- **Phase 2 — superiority cohort (continuing, same frozen contract).** Minimum **N=150** against
  the strongest comparator, calendar backstop at season 12, then `SUCCESS` / `FAILURE` /
  `NEUTRAL` / `UNDERPOWERED` per a pre-declared contract with no rescue rule.

## 5. The ten questions

Please answer in whatever depth you think each deserves. Short, blunt answers are fine.

1. **Is the information boundary legitimate?** The claim is that at issuance the entire target
   window lies in the future, and the model has seen only data through week t, where t is the
   latest officially published week. Does anything here still leak future information?
2. **Is L=4 scientifically useful?** A four-week burden forecast starting four weeks after the last
   published week means a horizon of 4–7 weeks ahead of data that is itself ~17 days old. Is that
   operationally meaningful for Lassa response in Nigeria, or is it too far out to act on?
3. **Is Brier the right primary endpoint?** We chose it over AUROC because the output is intended
   as a calibrated risk, and over log loss because log loss was far less precise at L=2 (it is
   better behaved at L=4). Would you choose differently?
4. **Is the strongest-comparator rule acceptable?** It is conservative, but it makes lag-1 the de
   facto sole primary comparator and therefore sets the study's power alone. Is that the right
   trade, or does it make the study answer a less interesting question than it could?
5. **Is the paired moving-block bootstrap adequate** for weekly surveillance data with strong
   seasonality and autocorrelation, at 4-week blocks with an 8-week sensitivity check? What would
   you use?
6. **Is a calendar stop defensible at all**, and is the two-phase split honest or evasive? Phase 1
   cannot return a superiority verdict by construction — does that read as rigour or as hedging?
7. **Is the calibration strategy defensible** given that calibration is load-bearing, is not
   uniformly better year to year, and is frozen from a single calibration year (2023, n=52)?
8. **Is the study interpretable if lag-1 stays neutral for a decade?** If the honest answer in 2037
   is "better than climatology, indistinguishable from persistence," is that a publishable result
   or a null project?
9. **Are any data-source or revision assumptions problematic?** Primary analysis uses
   as-first-published weekly values with source hashes; later NCDC revisions enter only a labelled
   sensitivity analysis. Does that bias anything in a direction we have not noticed?
10. **What would make this protocol unpublishable?** The single change you would insist on before
    this is frozen.

## 6. What we are *not* asking

- We are not asking whether GaiaLab is a good system.
- We are not asking for help improving the model's scores. The model, calibrator, features and
  threshold were frozen before the held-out years were inspected, and tuning them now against
  2024/2025 would destroy the only untouched evaluation data that exists.
- We are not asking about Lassa biology, host ecology or therapeutics. Those are separate tracks
  and are deliberately out of scope here.

## 7. Supporting documents

| Document | Contents |
|---|---|
| [`LASSA_V1_2_PRE_FREEZE_REVIEW.md`](LASSA_V1_2_PRE_FREEZE_REVIEW.md) | Full evidence packet, sections A–X, with every measured figure |
| [`LASSA_V1_2_DECISION_PACKAGE.md`](LASSA_V1_2_DECISION_PACKAGE.md) | The three open contract decisions and their recommendations |
| [`PROSPECTIVE_PROTOCOL_LASSA_V1_2_DRAFT.md`](PROSPECTIVE_PROTOCOL_LASSA_V1_2_DRAFT.md) | Protocol draft, incl. withdrawn L=2 history |
| [`NCDC_REPORTING_LAG_AUDIT_2026-10-08_CORRECTION.md`](NCDC_REPORTING_LAG_AUDIT_2026-10-08_CORRECTION.md) | How the six-day figure failed and what replaced it |
| [`LASSA_V1_2_FREEZE_READINESS.md`](LASSA_V1_2_FREEZE_READINESS.md) | Gate memo and remaining blockers |
| [`LASSA_V1_2_IMPLEMENTATION_PLAN.md`](LASSA_V1_2_IMPLEMENTATION_PLAN.md) | Ledger schemas, outcome adjudication, integrity tests |

All analysis scripts are committed under `scripts/lassa/` and reproduce in the pinned environment.

## 8. Reviewer response

**Overall:** `PROTOCOL DEFENSIBLE AS WRITTEN` / `DEFENSIBLE AFTER CHANGES` / `NOT DEFENSIBLE`

Required changes before freeze:

1. ______________________________________________
2. ______________________________________________
3. ______________________________________________

The single most likely reason this protocol would fail peer review:

______________________________________________

Reviewer: ______________________  Affiliation: ______________________  Date (UTC): ____________

No conflict-of-interest statement is requested beyond: do you have any relationship to this
project or its authors? `Yes / No`
