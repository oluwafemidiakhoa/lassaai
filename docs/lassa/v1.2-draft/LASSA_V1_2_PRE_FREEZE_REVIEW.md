# LassaAI v1.2 — pre-freeze review packet

**Status: DRAFT — NOT FROZEN — NOT ACTIVE. Requires accountable-human approval (section W).**

Scope: the proposed v1.2 prospective epidemiological study. Frozen v1.1
(`lassa-national-forecast-2026-27-v1.1`) is untouched by every artifact referenced here, and its
timing-contract mismatch and missed-start disclosure remain visible as historical evidence.

**Recommendation of this packet: REVISE.** Two blocking problems were found during verification,
both of which would have been frozen into the protocol had it been approved as drafted:

1. The six-day publication-lag figure that justified lead **L=2** is a measurement artifact. Under
   a genuine upload-time proxy, **0 of 36** observed 2026 weeks would have been eligible at L=2.
2. The candidate **200-scoreable-forecast** boundary implies roughly a **15-year** study at the
   realistic yield of ~13 eligible forecasts per dry season. Re-planning at L=4 lowers the
   requirement to ~150 (~11 seasons), so the boundary must be re-derived rather than inherited —
   but beating lag-1 persistence remains a multi-season commitment at any lead.

Neither problem affects scientific integrity if caught now. Both would have been fatal if frozen.

---

## A. Exact scientific question

Can GaiaLab, using only information officially published by NCDC at the moment of issuance,
assign better-calibrated probabilities to future elevated national Lassa fever burden than every
pre-specified persistence and seasonal comparator, where "better" is judged primarily by a proper
scoring rule on a fully future target window?

v1.2 exists to fix a design defect in v1.1 (section V), not to improve a disappointing result.
No v1.2 forecast has been issued, so **no prospective skill is claimed by this document.**

## B. Exact target

For data-through ISO week *t*, the target is the total confirmed national Lassa cases over the
four full ISO weeks *t+L … t+L+3*. The target window must be **entirely in the future** at
issuance (section P). The binary outcome is `total > threshold` (section D).

## C. Exact lead — **OPEN DECISION, L=2 WITHDRAWN**

| Lead | Max tolerated publication lag | Observed week coverage (n=36) | Eligible information boundaries | Est. forecasts / 25-week season |
|---|---:|---:|---:|---:|
| L=2 | < 8 days | **0 / 36 (0%)** | **0 / 19** | **~0** |
| L=3 | < 15 days | 13 / 36 (36%) | 13 / 19 | ~9.0 |
| **L=4** | **< 22 days** | 27 / 36 (75%) | **19 / 19** | **~13.2** |
| L=5 | < 29 days | 33 / 36 (92%) | 19 / 19 | ~13.2 |

Source: `scripts/lassa/v12-publication-lag-probe.py`, documented in
`docs/lassa/NCDC_REPORTING_LAG_AUDIT_2026-10-08_CORRECTION.md`.

**Recommended: L=4.** It is the smallest lead achieving full eligibility across every observed
2026 information boundary, and it tolerates lag up to 21 days against an observed p90 of 25 days
and a maximum of 44 days. L=5 adds no yield because the binding constraint is batch cadence, not
lag, once the ceiling exceeds the newest-week lag in each batch.

**Integrity guard on this choice.** L must be chosen by the eligibility constraint, which is an
operational pre-outcome criterion, and **never** by which lead scores best on 2024/2025. Those are
the untouched and reserved evaluation sets; selecting L by their scores would convert them into a
selection set. The audit sweeps were widened to L=1–6 (lead offset) and L=2–5 (calibration,
uncertainty) solely to confirm the lag-forced lead is usable, not to pick a winner.

**Precondition before freezing any L:** establish a first-publication timestamp source that does
not depend on HTTP `Last-Modified` (correction doc §6). The cheapest and cleanest is to begin
recording, from now on, the first date the detector observes each new week.

**On the primary endpoint, L=4 is stronger than L=2 — the lag constraint and the science agree.**
An earlier draft of this packet recorded the opposite, on the basis of AUROC alone. That was
incomplete and is corrected here.

AUROC gain over the strongest comparator does fall with lead (L=2 +0.0214, L=3 +0.0247,
**L=4 +0.0089**; lead-offset audit, train ≤2023). But AUROC is explicitly **not** the primary
endpoint (section H). On the primary endpoint — the paired Brier difference for the calibrated
candidate — L=4 is better against **every** comparator, and is the only lead tested at which the
lag-1 interval clears zero:

| Comparator | L=2 Brier 95% CI | L=4 Brier 95% CI |
|---|---|---|
| lag-1 | [−0.0829, **+0.0074**] crosses zero | [−0.1040, **−0.0013**] below zero |
| recent-4 | [−0.0962, +0.0013] crosses zero | [−0.1164, −0.0108] below zero |
| seasonal | [−0.1519, −0.0238] below zero | [−0.1580, −0.0186] below zero |
| seasonal+persistence | [−0.1465, −0.0161] below zero | [−0.1584, −0.0173] below zero |

Log loss behaves the same way (L=4 vs lag-1: [−0.2303, −0.0040], below zero; L=2 crossed). The
mechanism is unsurprising: over a four-week-further horizon, naive persistence loses skill faster
than a model carrying seasonality and trend. Calibrated Brier itself is nearly flat across leads
(L=2 0.1587, L=3 0.1618, L=4 0.1602, L=5 0.1617), so the longer lead costs little in probability
quality while degrading the baselines substantially.

Three cautions that keep this honest:

- the lag-1 upper bound at L=4 is **−0.0013**, only marginally below zero, so this is a thin
  historical margin and not a robust result;
- it leans harder on the frozen calibrator: the *uncalibrated* model at L=4 is worse than all four
  comparators on Brier (lag-1 +0.0495), whereas at L=2 it at least beat the seasonal pair;
- it is retrospective evidence on 2024+2025 and establishes no prospective skill.

The selection rule still stands: **L is chosen by eligibility, not by these scores.** It happens
that the lag-forced lead is also the better-supported one, which removes a tension rather than
creating a temptation. Had the scores pointed the other way, L=4 would still have been the only
operationally possible choice.

## D. Exact endpoint threshold

`> 32` confirmed cases over the four-week target window, derived as the median four-week target
burden over the ≤2023 development era. **Do not change 32 directly.**

**Resolved:** the widened calibration sweep confirms the frozen median rule yields **32 at every
lead tested (L=2, 3, 4, 5)**, so moving to L=4 requires no threshold change and no re-approval of
the endpoint. Had it shifted, the new value would have been a consequence of the frozen rule
rather than a retune, but would still have needed explicit approval.

## E. Exact model

`xgboost.XGBClassifier`, fitted on epi-years **≤ 2022**, with hyperparameters frozen before any
held-out year was inspected and **identical across all leads** (no per-lead tuning):

`n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
eval_metric="logloss", random_state=0, n_jobs=1`, plus
`scale_pos_weight = (negatives / positives)` computed on the fit set only.

Features, in this exact order, with no scaling and no imputation:
`conf_lag1, conf_lag2, conf_lag4, conf_lag8, roll4, roll8, roll_trend, epi_week, dry_season`,
where `dry_season = 1` iff `epi_week ≤ 17 or epi_week ≥ 45`, and a minimum of 8 prior weeks of
history is required.

## F. Exact calibration rule

**Platt scaling**: a one-dimensional `sklearn.linear_model.LogisticRegression(solver="lbfgs")`
fitted on the raw model probability, using **epi-year 2023 only**.

- **Frozen once approved.** No expanding-window recalibration, and no refit after any prospective
  outcome is observed, for the entire life of v1.2.
- **Isotonic regression is rejected** as primary: unstable on reserved 2025 (log loss 4.14 versus
  Platt 0.53) and pooled (2.72 versus 0.49).
- Reproducible candidate artifact: `scripts/lassa/v12-calibration-freeze-candidate.py` emits the
  fitted Platt coefficients and intercept, the booster SHA-256, the series SHA-256, the exact
  hyperparameters and the environment versions. It is generated **in the frozen environment by
  CI** (`lassa-v12-research-eval`), not on a developer machine, and is marked
  `CANDIDATE — NOT FROZEN, NOT ACTIVE`.

## G. Exact comparator set

All four are retained, including the one that is hardest to beat:

1. recent-4-week persistence;
2. **lag-1 persistence**;
3. harmonic seasonal climatology;
4. seasonal + persistence logistic regression.

Lag-1 is **not** removed for being strong. Section L declares in advance how the study behaves
when lag-1 is not beaten.

## H. Primary endpoint

Paired **Brier-score difference** between the calibrated model and the **strongest pre-specified
comparator on the same scoreable forecasts**, with a dependence-aware paired moving-block
bootstrap interval (4-week blocks primary, 8-week sensitivity, 4000 replicates, seed 20260922).

Rationale, stated before any prospective data exists: AUROC gain intervals cross zero against
every comparator even pooled across 2024+2025, so AUROC is **not** a primary or co-primary
endpoint. Probability quality, not ranking, is the claim.

## I. Secondary endpoints

AUROC; log loss; ECE (5 bins); reliability curve; 8-week block sensitivity; per-season descriptive
metrics. All are explicitly secondary and non-overriding; none can convert a neutral primary
result into a success.

## J. Information boundary — **OPEN DECISION, 200 IS INFEASIBLE**

Realistic prospective yield is about **13.2 eligible forecasts per 25-week dry season** at L=4
(19 information boundaries over 36 observed 2026 weeks, one forecast per boundary per section Q).
Crucially, the historical audits used roughly 52 observations per year, so **prospective evidence
accrues about four times more slowly than those analyses implicitly assume.**

| Option | Seasons to reach | Assessment |
|---|---:|---|
| 1 — N = 200 | ~15 | Derived at **L=2 vs lag-1**, where the interval crossed zero. **Not the right requirement for L=4** |
| 2 — N = 250 | ~19 | Same objection, worse feasibility |
| **3 — Hybrid: min N with a hard calendar stop** | configurable | **Recommended** |

**Measured at both leads (planning audit, paired Brier vs lag-1, the hardest comparator):**

| N | L=2 Brier | L=2 log loss | L=4 Brier | L=4 log loss |
|---:|---|---|---|---|
| 50 | crosses 0 | crosses 0 | crosses 0 | crosses 0 |
| 100 | crosses 0 | crosses 0 | crosses 0 (upper +0.0013) | **below 0** |
| 150 | crosses 0 (upper +0.0001) | crosses 0 | **below 0** (upper −0.0092) | **below 0** |
| 200 | **below 0** | crosses 0 | below 0 | below 0 |
| 300 | below 0 | **still crosses 0** | below 0 | below 0 |

Two things follow. The Brier requirement against lag-1 falls from roughly **N=200 at L=2 to
N=150 at L=4** — an improvement, but not a transformation. More striking is log loss: at L=2 it
**never** clears zero even at N=300, whereas at L=4 it clears at N=100. The two proper scores
therefore agree at L=4 and disagree at L=2, which is a further reason to prefer L=4.

**Honest consequence for scheduling.** At ~13.2 eligible forecasts per season, N=150 is roughly
**11 seasons**. Beating naive lag-1 persistence decisively is a long game whichever lead is
chosen. The seasonal and seasonal+persistence comparisons are a different matter: their intervals
sat entirely below zero at n=104 historically, so those are plausibly answerable within a few
seasons. The study should be framed accordingly — a near-term answer against climatological
baselines, and a long-term accumulation against persistence.

**Recommended: Option 3**, concretely — a hard calendar stop of **four completed dry seasons**
(first active season plus three), with the minimum N set from the L=4 planning audit rather than
inherited from L=2, and the final classification determined by section L applied to whatever N is
actually reached. Rationale:

- **CORRECTED 2026-10-08.** This rationale previously read: "A four-season study is expected to
  report NEUTRAL against lag-1 while plausibly being decisive against the seasonal baselines." The
  second clause was never measured — the planning audit only ever compared against lag-1 — and it
  is now **false**. Measured against all four comparators (CI run on `b7186795`, seed 20260923,
  same resampled index series applied to every comparator), at N=53 **no comparator's interval
  excludes zero**:

  | N | ≈ seasons | lag-1 | recent-4 | seasonal | seasonal+persistence |
  |---:|---:|---|---|---|---|
  | **53** | **4.0** | **crosses** | **crosses** | **crosses** | **crosses** |
  | 80 | 6.1 | crosses | below 0 | below 0 | below 0 |
  | 106 | 8.0 | below 0 | below 0 | below 0 | below 0 |
  | 150 | 11.4 | below 0 | below 0 | below 0 | below 0 |

  The seasonal interval at N=53 is [−0.1887, **+0.0066**] — close, but close is not a result.
  **A four-season study would be decisive against nothing.**
- **And the strongest-comparator rule makes this worse than it looks.** By median Brier difference
  the model's advantage is *smallest* against lag-1 (−0.0506) and largest against seasonal
  (−0.0834), so **lag-1 is the strongest comparator** and the primary endpoint is effectively the
  lag-1 comparison alone. Clearing the seasonal baselines at N=80 would therefore still report
  NEUTRAL. The study is powered by the lag-1 requirement and nothing else: **N ≈ 106–150, roughly
  8–11 seasons.**
- **The crossing point cannot be stated precisely.** The original lag-1-only sweep put it at N=150
  (N=100 crossing, upper +0.0013); the new pass puts it at N=106 (upper −0.0007, N=80 crossing).
  Different resampling streams move the boundary. The honest statement is **"around N≈100–150"**,
  and the earlier flat "N=150" was quoted with more precision than the method supports — read it
  as the conservative end of the range.
- A bounded study that reports honestly beats an unbounded one that never reports. If the L=4
  figure still implies more seasons than you are willing to commit to, the honest response is to
  declare the calendar stop anyway and accept an UNDERPOWERED classification as a real possible
  outcome (section N).

The planning audit is explicitly **not a formal power calculation**, and no N should be described
as a guaranteed sufficient sample size.

## K. Interim-season rule

The first active season is **interim evidence accumulation, not a pass/fail verdict.**

- **Start condition:** protocol frozen and approved; calibration artifact frozen; eligibility
  guard active; first eligible information boundary reached.
- **End condition:** the season's last eligible data-through week inside the declared window has
  its four-week outcome fully published.
- **Published each season:** every forecast, every outcome, the primary paired Brier difference
  with its interval, all secondary metrics, every ineligible opportunity and its machine-readable
  reason, and the running N against the boundary.
- **Permitted claims:** "interim, underpowered, N of M forecasts accumulated."
- **Prohibited claims:** any statement of validated skill, any success declaration, any selective
  reporting of the comparator that happens to look worst, and any use of the word "validated"
  before the boundary in section J is reached.
- **Continuation:** automatic into the next season unless a data-integrity failure (section O)
  occurs. Methodology may not change between seasons; any change starts v1.3.

## L. Final success criteria (all required)

1. The section J boundary is reached (minimum N, or the calendar stop with N disclosed);
2. calibrated model Brier **<** strongest pre-specified comparator Brier;
3. the paired dependence-aware 95% interval for that Brier difference lies **entirely below zero**
   under the primary 4-week blocks, with the 8-week result reported as sensitivity;
4. calibration not materially degraded (section M.3);
5. no data-integrity failure (section O).

## M. Failure criteria (any one)

1. Calibrated model Brier significantly **worse** than the strongest comparator, i.e. the paired
   interval lies entirely **above** zero;
2. the model is beaten by the strongest comparator on both Brier and log loss with intervals
   excluding zero;
3. **material calibration failure**: ECE (5 bins) exceeding 0.25 on the **accumulated**
   prospective cohort, declared now rather than after seeing results.

   This is deliberately **not** applied per season, and the reason is quantitative: under the
   candidate model the reserved 2025 season alone has Platt ECE **0.3064** at the proposed L=4
   (0.2887 at the withdrawn L=2), which would exceed
   this threshold, while the pooled 2024+2025 cohort had ECE **0.1439**, which passes comfortably.
   A single-season ECE near 0.29 is therefore within observed behaviour for this model and must
   not auto-fail the study. Per-season ECE is reported as a secondary diagnostic (section I).

## N. Neutral / inconclusive criteria

- Point estimate favourable but the paired interval crosses zero — **the expected outcome against
  every comparator at four seasons**, not just lag-1 (section J, corrected);
- fewer than the declared minimum N at the calendar stop → **UNDERPOWERED / INCONCLUSIVE**;
- insufficient outcome-class variation (fewer than 5 positive or 5 negative outcomes);
- primary metric or interval undefined.

A neutral result is a publishable scientific finding, not a failure to be reframed.

## O. Data-integrity failure criteria

Classify the study **DATA-INTEGRITY FAILURE** and publish it as such if any of these occur:

- a ledger hash chain breaks, or any committed forecast record is altered after the fact;
- a forecast is found to have been logged with its target window already started;
- the frozen model, calibrator, threshold, feature set or comparator set is changed mid-study;
- surveillance data provenance cannot be traced to official NCDC material;
- an outcome is written into the forecast ledger rather than the separate outcome ledger.

No favourable fallback exists for any of these. The result is reported, not rescued.

## P. Eligibility guard — **implemented and verified**

> A forecast is eligible only if `issued_at < 00:00:00Z` on the Monday of ISO week `t + L`.

This is strictly stronger than v1.1's `window_end > today`, which admitted forecasts whose target
had already partly elapsed (section V). Implementation: `scripts/lassa/lib/v12_eligibility.py` —
pure, side-effect-free date logic, not wired to any generator, logger, ledger or workflow. Week
arithmetic is done by calendar-day offset from the data-through Monday, never by incrementing ISO
week numbers, so year boundaries and 52/53-week years need no special cases.

Verified by 32 boundary cases (`scripts/lassa/v12-eligibility-selftest.py`, asserted in
`tests/lassa-v12-eligibility.test.js`), all passing: one second before target start eligible;
exactly at start ineligible; after start ineligible; non-UTC offsets normalised; naive timestamps
refused; ISO year boundary; 2026-W53 valid and 2025-W53 malformed; leap-year window spanning
29 February; week 0/54/non-numeric malformed; duplicate data-through week refused; lead 0 refused.
The matrix covers both the proposed L=4 windows and the withdrawn L=2 ones.

**The guard has no default lead.** `lead` is a required argument of `target_window`,
`target_start_instant` and `check_eligibility`, and three cases prove each raises `TypeError` when
it is omitted, plus one asserting the module exposes no `DEFAULT_LEAD`. This is deliberate: a
module-level default would let a caller that forgot to pass `lead` silently forecast against the
wrong target window — the precise error the guard exists to prevent — and the stale default would
have been the now-withdrawn L=2. `PROPOSED_LEAD_PENDING_APPROVAL = 4` exists as documentation and
is never read as a fallback.

Refusal reasons are machine-readable: `target_already_started`, `malformed_source_week`,
`duplicate_data_through_week`, `naive_timestamp_rejected`. **A late release is simply ineligible.
The guard is never weakened to admit one.**

Worked example, which also shows why this matters: the current real boundary is 2026-W36. At the
proposed L=4 its target is 2026-09-28 … 2026-10-25, which opened on 28 September — so **v1.2 would
refuse a forecast today**, exactly as it would have at the withdrawn L=2 (target 2026-09-14 …
2026-10-11). The guard is not theoretical, and the refusal is recorded as an ineligible
opportunity rather than resolved in the forecast's favour.

## Q. Late and batched release policy

NCDC publishes in batches: 11 of 19 observed 2026 upload timestamps covered more than one week.

- Refresh the series in week order, preserving append-only integrity;
- determine the **single latest** information boundary available;
- evaluate eligibility for that boundary only;
- issue **at most one** forecast per batch;
- **never** reconstruct forecasts for earlier weeks in the batch. Once a later week is known, an
  earlier week's forecast would be contaminated by future information and is forbidden;
- record every skipped week as an ineligible opportunity with its reason, and never backfill it.

## R. Missing and revised data policy

- **Missing input week at issuance:** no forecast; record "not forecastable — missing data";
  neither a hit nor a miss.
- **Missing outcome week at evaluation:** that forecast is excluded from the primary analysis and
  reported separately. Missing weeks are never interpolated.
- **NCDC revisions:** the primary analysis uses values **as first published and as logged**. A
  sensitivity analysis repeats the evaluation on latest revised values. Both are reported, and the
  primary verdict is not changed by later revisions.
- **Prolonged publication gap:** opportunities are ineligible, N accrues more slowly, and the
  calendar stop still applies. A gap is a yield problem, never a licence to relax the guard.

## S. Multi-season continuation rule

Model, lead, threshold, feature set, calibration mapping, comparator set and success rule are
fixed for the life of v1.2. Any change to any of them starts a new explicitly versioned protocol
(v1.3) with its own study ID, ledger and receipts. Seasons accumulate into one cohort; the
boundary in section J governs when a final classification may be issued.

## T. Publication commitment

Every forecast, outcome, ineligible opportunity and seasonal interim result is published
regardless of direction — positive, neutral, negative, underpowered or data-integrity failure — at
`/lassa-prospective` and in any manuscript update, together with the full append-only ledgers. No
cherry-picking. A negative or neutral result is stated as plainly as a positive one.

## U. Known limitations

1. **Publication lag is not yet reliably measured.** The replacement figure is an upload-time
   proxy that may overstate true lag; the superseded six-day figure measured nothing. L cannot be
   frozen until a defensible first-publication source exists.
2. **Feasibility.** Yield is roughly 13 eligible forecasts per season, about four times slower
   than the historical analyses' ~52/year. The 15-year figure applies to the **L=2** cohort
   requirement; at L=4 the historical interval already clears zero against every comparator, so
   the requirement is smaller and must be re-derived from the L=4 planning audit. An
   UNDERPOWERED outcome remains a genuine possibility and is predeclared in section N.
3. **Single endpoint, single country, single pathogen.** No generalisation beyond national Lassa
   incidence in Nigeria.
4. **Development evidence is retrospective.** Every number in section V is historical and must
   never be presented as prospective validation.
5. **Batch cadence, not lag, is the binding yield constraint** once L ≥ 4.
6. Threshold 32 may need recomputation under the frozen rule if L changes (section D).

## V. Historical evidence summary (retrospective — not prospective validation)

All figures below were produced by the committed audit scripts in the frozen environment
(Python 3.11.16, numpy 1.26.4, scikit-learn 1.4.2, xgboost 2.0.3) and were read from the
`lassa-v12-research-eval` CI run on PR #447, not from a developer machine. **All are for L=2 and
are therefore conditional on a lead that section C now withdraws.**

### L=4 — the proposed lead *(added 2026-10-08, CI run 37796979614)*

Produced in the same frozen environment (Python 3.11.16, numpy 1.26.4, scikit-learn 1.4.2,
xgboost 2.0.3) by `scripts/lassa/v12-calibration-audit.py`, read from the
`lassa-v12-research-eval` run on commit `ba02e4ce`.

| Cohort | Variant | n | AUROC | Brier | ECE(5) | Log loss |
|---|---|---:|---:|---:|---:|---:|
| 2024 (untouched) | raw | 52 | 0.9047 | **0.1153** | **0.1311** | 0.4555 |
| 2024 | Platt | 52 | 0.9047 | 0.1232 | 0.1430 | **0.4026** |
| 2024 | isotonic | 52 | 0.9000 | 0.1488 | 0.1089 | 1.0302 |
| 2025 (reserved) | raw | 52 | 0.7862 | 0.3826 | 0.4619 | 1.4207 |
| 2025 | Platt | 52 | 0.7862 | **0.1971** | **0.3064** | **0.5637** |
| 2025 | isotonic | 52 | 0.7554 | 0.3039 | 0.3336 | 2.6783 |
| pooled | raw | 104 | 0.8097 | 0.2490 | 0.2796 | 0.9381 |
| pooled | **Platt** | 104 | 0.8097 | **0.1602** | **0.1463** | **0.4832** |
| pooled | isotonic | 104 | 0.7988 | 0.2264 | 0.1892 | 1.8543 |

Three things to read honestly from this table rather than from the pooled row alone:

1. **In 2024 alone, Platt is worse than raw on both Brier (0.1232 vs 0.1153) and ECE (0.1430 vs
   0.1311)**, and only better on log loss. At L=2 the same inversion appeared on Brier only. The
   entire pooled gain comes from 2025, where raw calibration collapses (Brier 0.3826 → 0.1971).
   Platt is therefore a *robustness* measure against bad years, not a uniform improvement.
2. **Reserved-2025 Platt ECE is 0.3064 at L=4** (0.2887 at L=2). This is the figure that governs
   the ECE failure criterion in section L: a per-season ECE auto-fail set at 0.25 would fail the
   model on a season the candidate already produces, so the criterion must apply to the
   accumulated cohort only.
3. **Isotonic remains rejected.** Its pooled log loss is 1.8543 against Platt's 0.4832 — better
   than its L=2 value of 2.7198, but still roughly four times worse.

**Reproduction cross-check (candidate ↔ audit).** The freeze-candidate generator and the
calibration audit are separate scripts sharing one fitting code path, so they must agree. At L=4
in the same run they do: endpoint threshold **32.0** from the frozen median rule in both, base
fit n = **149** (epi-years ≤2022) in both, Platt calibration n = **52** (2023 only) in both, and
the audit's pooled Platt Brier (0.1602) matches the cross-lead figure quoted in section C. The
candidate additionally pins booster SHA-256
`0701058318184a8164e70cfcd875b9421c7a948becd00988b47e1b57cd766e2c`, Platt coefficient 2.6934365596
and intercept −0.7160969922, against series SHA-256 `e34fb6c31dcd3ccd…` (349 rows, through
2026-W36). No disagreement was found, so nothing was forced.

**Reproducibility limit found while cross-checking — affects how a freeze manifest must be
written.** Two independent CI runs of the same commit in the same pinned environment (37796979614
and 37797997426) produced a bit-identical booster, threshold and input-series hash, but **not** a
bit-identical calibrator: the Platt coefficient came out as 2.6934365595797853 and
2.693436559579785, a relative difference of 1.6×10⁻¹⁶ — one float64 ULP, from L-BFGS summation
order. The effect on any emitted probability is ≤1.1×10⁻¹⁶ and is scientifically irrelevant.

The consequence is procedural, not scientific, and it is load-bearing: **a freeze manifest cannot
verify the calibrator by exact string or hash equality.** It must compare at a declared numeric
tolerance or a declared precision, and the freeze must state which. This also corrects an
over-claim in the generator, which promised a reviewer could reproduce the predictor
"bit-for-bit"; that is true of the booster and false of the calibrator.

**Where the drift lives, measured rather than assumed.** CI run 37798884968 generates the
candidate twice *within one job* and the two calibrators came out bit-identical — the gate's
optional drift note did not fire. The 1-ULP difference therefore appears **across runners, not
within a single machine**, which is consistent with a thread- or BLAS-level summation-order
difference rather than anything non-deterministic in the script. Two consequences, stated so the
gate is not over-trusted:

- the in-job gate proves within-machine determinism and would catch genuine instability (an
  unseeded component, a data-order dependence); it does **not** exercise the cross-runner case
  where the ULP actually appeared;
- therefore the freeze manifest's calibrator tolerance cannot be inferred from a green CI run. It
  must be declared explicitly, and verification must be assumed to run on a different machine from
  the one that produced the frozen values. A reference value is deliberately **not** committed to
  the repository here, because a stored expected calibrator could be mistaken for a frozen
  parameter, and nothing is frozen.

**Calibration — base ≤2022, Platt on 2023, L=2 *(withdrawn lead, retained for comparison)*:**

| Cohort | Variant | AUROC | Brier | ECE(5) | Log loss |
|---|---|---:|---:|---:|---:|
| 2024 (untouched) | raw | 0.8859 | 0.1364 | 0.1332 | 0.4977 |
| 2024 | Platt | 0.8859 | 0.1377 | 0.1210 | 0.4439 |
| 2025 (reserved) | raw | 0.7826 | 0.3468 | 0.4074 | 1.2183 |
| 2025 | Platt | 0.7826 | 0.1797 | 0.2887 | 0.5280 |
| pooled | raw | 0.8195 | 0.2416 | 0.2535 | 0.8580 |
| pooled | **Platt** | 0.8195 | **0.1587** | **0.1439** | **0.4860** |
| pooled | isotonic | 0.7966 | 0.2176 | 0.2051 | 2.7198 |

Platt leaves AUROC unchanged (it is monotonic) and substantially improves Brier, ECE and log
loss pooled. Note honestly that in **2024 alone** Platt's Brier is marginally *worse* than raw
(0.1377 vs 0.1364); the gain comes from 2025, where raw calibration degrades badly.

**Calibrated proper-score differences (model − comparator; negative favours GaiaLab), L=2,
pooled 2024+2025, 4-week blocks:**

| Comparator | Brier point | Brier 95% interval | Log-loss point | Log-loss 95% interval |
|---|---:|---|---:|---|
| lag-1 | −0.0324 | [−0.0829, **+0.0074**] crosses zero | −0.0479 | [−0.1637, **+0.0419**] crosses zero |
| recent-4 | −0.0457 | [−0.0962, **+0.0013**] crosses zero | −0.0891 | [−0.1984, +0.0188] crosses zero |
| seasonal | −0.0784 | [−0.1519, −0.0238] below zero | −0.1860 | [−0.3913, −0.0445] below zero |
| seasonal+persistence | −0.0722 | [−0.1465, −0.0161] below zero | −0.1781 | [−0.4063, −0.0244] below zero |

8-week blocks agree in sign and conclusion.

**Two provenance cautions that must not be repeated in any downstream summary:**

1. **Do not mix the two training designs.** The lead-offset audit trains on ≤2023 and reports
   2024 AUROC 0.8734 (gain +0.0172 over seasonal) and pooled 0.8121 (gain +0.0214 over lag-1).
   The calibration and proper-score audits train on ≤2022 with a 2023 calibrator — a **different
   model**, whose 2024 AUROC is 0.8859 and pooled is 0.8195. The frozen candidate is the ≤2022 +
   Platt specification, so its discrimination figures are the latter pair. Quoting 0.8734
   alongside Platt's Brier describes a model that does not exist.
2. **Report the raw model too.** The *uncalibrated* model's Brier is **worse** than lag-1 (its
   paired difference has median +0.034 with ~78% probability of being worse). The favourable
   proper-score result depends entirely on the frozen calibrator. Presenting only the calibrated
   comparison would overstate the evidence.

**Planning audit (not a power calculation), L=2, calibrated, vs lag-1:** the paired Brier interval
crosses zero materially at N=25 and N=50, slightly at N=100, approximately touches zero at N=150,
and lies below zero at N=200 (median −0.0346, interval up to −0.0040), N=250 and N=300. Log loss
remains indecisive even at N=300.

## W. Human decision gate

**This packet's recommendation: REVISE.** Specifically:

1. **Withdraw L=2.** Adopt L=4 subject to item 2. — *Done in the artifacts as of 2026-10-08; the
   adoption itself still requires the signature below.*
2. **Establish a defensible first-publication timestamp source**, then re-estimate lag and confirm
   the lead. Begin recording detector first-observation dates immediately — it costs nothing and
   is the cleanest source available. — **OUTSTANDING. This is the binding blocker to any freeze.**
   The current figures rest on an HTTP `Last-Modified` upload-time proxy, which must not be
   promoted into first-publication truth.
3. **Re-run the audit sweep for the chosen lead** and recompute the threshold by the frozen rule,
   recording whether it remains 32. — **Done.** CI run 37796979614 (commit `ba02e4ce`), frozen
   environment: threshold **32.0** at L=4, identical at L=2, 3 and 5; per-cohort L=4 calibration
   table published in section V; freeze-candidate generator and calibration audit agree on
   threshold, base fit n and calibrator n.
4. **Replace the 200-forecast boundary** with the calendar-bounded hybrid in section J, setting the
   minimum N from the **L=4** planning audit rather than inheriting the L=2 figure. — *Done in
   section J and in the downstream documents (N≈150 at L=4, four-season calendar stop); the
   boundary is a recommendation until approved here.*
5. **Correct the two provenance cautions** in section V wherever they appear downstream. — *Done;
   both are carried in `LASSA_V1_2_FREEZE_READINESS.md` section 3, and the L=4 table adds a third
   (Platt is worse than raw in 2024 alone on both Brier and ECE).*
6. Only then freeze, generate the manifest, and build the v1.2 implementation (section X).

Items 1, 3, 4 and 5 are discharged. **Item 2 is not, and no amount of consistency work
substitutes for it** — the lead cannot be frozen on proxy timing evidence.

Nothing in this packet is frozen, no manifest exists, no v1.2 ledger exists, and no v1.2 forecast
has been issued.

**Decision:** `APPROVE / REVISE / REJECT` → _______________

Accountable human: ______________________  Date (UTC): ______________

Notes: ______________________________________________________________

---

## X. Implementation plan (build only after approval)

Separate objects, sharing nothing mutable with v1.1 and never reusing the v1.1 logger:

| Object | Proposed path (ID not final) |
|---|---|
| Study ID | `lassa-national-forecast-v1.2` — **not final until approved** |
| Forecast generator | `scripts/lassa/v12-forecast-now.py` |
| Forecast logger | `scripts/lassa/v12-forecast-logger.py` |
| Forecast ledger | `data/lassa/v12-prospective-log.jsonl` |
| Outcome recorder | `scripts/lassa/v12-outcome-recorder.py` |
| Outcome ledger | `data/lassa/v12-prospective-outcomes.jsonl` |
| Receipt builder | `scripts/lassa/v12-build-public-receipts.mjs` |
| Public receipts | `public/lassa-v12-prospective-receipts.json` |
| Readout | `scripts/lassa/v12-prospective-readout.py` |
| Freeze manifest | `data/lassa/v12-freeze.json` |
| Runbook | `docs/lassa/V12_PROSPECTIVE_OPERATIONS.md` |
| Eligibility guard | `scripts/lassa/lib/v12_eligibility.py` — **already built and tested** |

Each ledger record must independently permit full reconstruction: `issued_at` (UTC), data-through
week, information-source URL, source hash, target start, target end, lead offset, eligibility
result and reason, raw probability, calibrated probability, all four comparator probabilities,
model hash, calibration hash, dataset hash, protocol hash, code commit, environment versions,
previous record hash and current record hash.

Ineligible opportunities are recorded in the ledger as ineligible, with their machine-readable
reason, rather than omitted — so the denominator of missed opportunities is auditable.
