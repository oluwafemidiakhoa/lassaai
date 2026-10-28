# LassaAI National Early-Warning — Prospective Validation Protocol v1.2 (DRAFT)

**Status: DRAFT — NOT FROZEN — NOT ACTIVE.**
**Purpose:** redesign the forecast-timing contract so every scored target window is genuinely future at issuance under real NCDC reporting latency.
**Relationship to v1.1:** this document does not amend, reinterpret, or repair `lassa-national-forecast-2026-27-v1.1`. v1.1 remains frozen and must be scored only under its original contract.

## 1. Why v1.2 is needed

The frozen v1.1 protocol says a scored week is excluded if it could not be logged **before its outcome window began**. The current v1.1 implementation only checks that the four-week outcome window has **not completely ended** (`window_end > today`). Those are different conditions.

Therefore v1.2 must explicitly bind:
1. the information cutoff available to the model;
2. the issuance timestamp;
3. the first target week;
4. a target window that has not begun at issuance.

No v1.2 forecast may be backfilled.

## 2. Current reporting-lag evidence

> **SUPERSEDED 2026-10-08.** The six-day figure below is a **measurement artifact** and must not be
> used to choose a lead. The "archive label" is the label of the epidemiological week the report
> covers, not the date the report was published, so subtracting the week end from the label
> measures the week-boundary offset and nothing else — which is why all seven observations show
> exactly 6 days with zero variance. The current figure is in
> `docs/lassa/NCDC_REPORTING_LAG_AUDIT_2026-10-08_CORRECTION.md`: under an upload-time proxy,
> n=36, **median 17 days**, min 9, p90 25, max 44. The table is retained as withdrawn evidence
> because a lead chosen from it (L=2) would have produced **0 eligible forecasts in 36 weeks**.

The original (withdrawn) sample for 2026 W30-W35 read archive labels dated six days after each epidemiological week ended:

| Data-through week | Week end | Archive label | Observed lag |
|---|---:|---:|---:|
| W30 | 2026-07-26 | 2026-08-01 | 6 days |
| W31 | 2026-08-02 | 2026-08-08 | 6 days |
| W32 | 2026-08-09 | 2026-08-15 | 6 days |
| W33 | 2026-08-16 | 2026-08-22 | 6 days |
| W34 | 2026-08-23 | 2026-08-29 | 6 days |
| W35 | 2026-08-30 | 2026-09-05 | 6 days |

The instruction this section already carried — "extend the measurement across all 2026 reports
whose publication/upload dates can be verified from a primary NCDC surface, record unknown dates
as unknown" — is what exposed the artifact, and it remains **unsatisfied**. The replacement
measurement uses an HTTP `Last-Modified` upload-time proxy. A proxy is adequate to disqualify L=2
and to rank leads; it is **not** a defensible first-publication source and must not be promoted
into one. Freezing a lead still requires a primary publication-time source, and that is the
outstanding blocker to freeze (section 4, section 21).

## 3. Candidate timing designs

### A. Information-set-relative target

Issue at official report publication time and forecast a target not yet known in the official NCDC information set.

**Advantage:** matches what an operational forecaster actually knows.
**Weakness:** some calendar weeks in the nominal target may already have elapsed. This is weaker for claims framed as predicting future real-world incidence.
**Recommendation:** do not use as the primary v1.2 design unless the scientific claim is explicitly narrowed to "future-to-the-information-system" rather than future-in-calendar-time.

### B. Next four full ISO weeks after issuance

Issue after an official report arrives, but define the target as the next four complete ISO weeks that have not begun at issuance.

**Advantage:** strongest intuitive prospective claim; every target week is physically future.
**Weakness:** the prediction horizon relative to the last observed data week varies with publication delay, requiring a matching model-training target and careful historical simulation.

### C. Fixed lead-offset target from the last observed week

For data-through week t, forecast four-week burden over weeks t+L through t+L+3, where L is frozen before use and selected from measured publication-lag evidence so the entire target is still future at normal issuance.

An earlier draft of this section used a six-day lag as its worked example and concluded that L=2 would suffice. That six-day figure was later found to be a week-boundary subtraction artifact and has been withdrawn (see `NCDC_REPORTING_LAG_AUDIT_2026-10-08_CORRECTION.md`). Under the upload-time proxy the measured lag distribution is n=36, median 17 days, min 9, p90 25, max 44 — so L=2 tolerates no observed release at all and L=4 is the smallest lead that does. The example is retained only to show how the example was wrong: a lead chosen from an under-measured lag silently produces a target window that has already begun.

**Advantage:** fixed target mapping, easy to reproduce and backtest without variable horizons.
**Weakness:** the chosen L must cover real publication-lag tails, not only the median; large delayed batches may still be ineligible.

## 4. Preferred design for development

**Preferred for further evaluation: Candidate C, fixed lead-offset**, because it preserves a fixed machine-learning target while making the future boundary explicit.

Do not freeze L yet.

Freeze L only after:
- measuring the primary-source publication-lag distribution;
- selecting a pre-declared coverage target (for example >=90% of historical releases);
- simulating historical scoreable-week counts;
- confirming adequate expected power.

Status of those four conditions as of 2026-10-08: the lag distribution and the scoreable-week
simulation have been measured, and the expected-cohort question has been re-planned at the
lag-feasible lead (section 21). The first condition is satisfied only by an **HTTP
`Last-Modified` upload-time proxy**, which is not a defensible first-publication source and must
not be promoted into one. L therefore remains unfrozen, and the lead cannot be frozen on proxy
timing evidence alone no matter how favourable the rest of the package looks.

If no practical fixed L yields adequate coverage and useful lead time, Candidate B becomes the fallback.

## 5. Proposed scientific question

Can a frozen national model predict whether confirmed Lassa burden will be elevated over a **fully future four-week target window**, at a fixed lead offset from the latest officially published data week, with added skill over pre-specified persistence and seasonal comparators constructed at the same information boundary?

## 6. Information boundary

For every forecast:
- information cutoff = exact official NCDC report used, identified by data-through epi week, URL, and retrieval/issuance timestamp;
- no later report, revision, outcome, or secondary-source data may enter model fitting;
- issuance timestamp must precede the start of the target window;
- if issuance occurs after target-window start, the forecast is ineligible and no scored record is logged.

## 7. Target definition

**DRAFT:** four-week national confirmed-case burden over weeks `t+L ... t+L+3`, where `t` is the last officially published data-through week at issuance and `L` is the frozen lead offset selected before activation.

The elevated threshold and target transformation must be developed and frozen using pre-v1.2 development data only. Do not automatically reuse v1.1's >32 threshold unless a scientific review explicitly establishes that the same threshold remains appropriate for the shifted target.

## 8. Model development rule

A v1.2 model must be evaluated retrospectively using the same lead-offset target intended prospectively.

Options:
- reuse the v1.1 feature family but refit labels for the shifted target;
- retain the v1.1 XGBoost hyperparameters unless a pre-freeze development comparison justifies a different fixed specification.

No tuning is permitted after v1.2 is frozen.

## 9. Comparators

At minimum:
1. recent four-week persistence;
2. previous-week persistence;
3. harmonic seasonal climatology;
4. seasonal + persistence logistic regression.

Every comparator must obey the same information cutoff and predict the same shifted target.

## 10. Calibration and uncertainty

Before freeze, specify:
- model probability calibration rule;
- Brier score;
- reliability curve;
- ECE bins;
- dependence-aware paired uncertainty for overlapping four-week outcomes;
- bootstrap block length(s), replicate count, and seed.

Do not inherit these values from v1.1 by implication; explicitly review and freeze them.

## 11. Inclusion / exclusion

Include a forecast only when:
- official primary NCDC data are verified;
- required history exists;
- no gap/negative-difference anomaly is present;
- frozen code/data bindings pass;
- issuance timestamp is strictly before target-window start;
- no record for the same information week already exists.

Exclude and disclose:
- delayed reports that arrive after target-window start for the frozen lead offset;
- missing/gappy source weeks;
- source-integrity anomalies;
- runtime/freeze drift.

Never backfill an excluded opportunity.

## 12. Publication-lag analysis required before freeze

Measure verified NCDC lag as:
`official publication/upload date - epi_week_end_date`.

Report:
- n with verifiable dates;
- median;
- mean;
- min;
- max;
- p75;
- p90;
- empirical proportion covered by each candidate L.

Unknown publication dates remain unknown.

## 13. Power/readiness analysis required before freeze

For each candidate L:
- simulate how many historical release opportunities would have been eligible;
- estimate expected scoreable forecasts in the proposed primary season;
- account for irregular batching and overlapping outcome windows;
- identify the probability of ending with <10 scoreable weeks.

Do not activate a design whose expected sample size makes the claimed readout implausible without explicitly accepting an underpowered study.

## 14. Evaluation window and readout

**Not yet frozen.**

Choose only after the reporting-lag and power analyses. If activation occurs after the original v1.1 W45 boundary, do not pretend the full W45-W17 window was prospectively available to v1.2.

## 15. Decision criteria

**Not yet frozen.**

Predeclare success, neutral/inconclusive, failure, calibration, comparator, and uncertainty rules before the first v1.2 scored forecast.

## 16. Revised data

Primary analysis should use as-published/as-logged values bound to the forecast's information set. A separately labelled sensitivity analysis may use later revised values.

## 17. Publication commitment

Publish positive, neutral, negative, and underpowered results. Never delete a miss.

## 18. Anti-gaming safeguards

Before first scored v1.2 forecast:
- human scientific sign-off;
- clean-tree freeze;
- code SHA-256;
- protocol SHA-256;
- data snapshot/hash;
- exact runtime lock;
- readout implementation hash;
- source-review hash;
- explicit study ID distinct from v1.1.

After first scored forecast:
- no silent change to target, lead offset, threshold, model, comparators, calibration, uncertainty, or decision rules.

## 19. Relationship to v1.1

v1.1 remains historically intact. A v1.2 forecast:
- cannot be counted in v1.1;
- cannot modify v1.1 receipts;
- cannot repair v1.1 missed opportunities;
- cannot change the interpretation of a v1.1 result.

## 20. Human gate

Before activation, the accountable human researcher must choose:

- [ ] APPROVE design for final pre-freeze audit
- [ ] REVISE
- [ ] REJECT

No AI system has authority to sign or freeze the scientific protocol.


## 21. Current development evidence (not frozen)

The current research package has narrowed the design but has not activated it.

### Lead-offset candidate

**L=2 is withdrawn. L=4 is the current proposed lead, pending accountable-human approval.**

| Lead | Max tolerated publication lag | Observed week coverage (n=36) | Eligible information boundaries | Est. forecasts / 25-week season |
|---|---|---|---|---|
| L=2 | < 8 days | 0 / 36 (0%) | 0 / 19 | ~0 |
| L=3 | < 15 days | 13 / 36 (36%) | 13 / 19 | ~9.0 |
| **L=4** | **< 22 days** | 27 / 36 (75%) | **19 / 19** | **~13.2** |
| L=5 | < 29 days | 33 / 36 (92%) | 19 / 19 | ~13.2 |

L=4 is the smallest lead reaching full eligibility across every observed information boundary, and
the primary endpoint agrees with that constraint rather than fighting it — see the uncertainty
subsection below.

- L=1 and L=2 are operationally infeasible: under the upload-time proxy a study frozen at L=2
  could not have logged a single eligible forecast in 36 observed weeks.
- L=3 covers only 13 of 19 information boundaries and is not proposed.
- L=5 adds lag tolerance at no measured cohort cost and is the robustness alternative if the
  eventual first-publication source shows a heavier tail than the proxy.

Stated against L=4 rather than hidden: L=4 tolerates lag up to 21 days, while the observed p90 is
25 days and the maximum 44. L=4 does **not** cover the measured tail, so some releases will be
refused as ineligible opportunities. That is the designed behaviour — a refusal is recorded, never
backfilled — but it means the ~13.2/season yield is an estimate from proxy timing, not a guarantee.

### Calibration candidate
Platt scaling, trained on a temporally separate calibration year, is the only calibration method currently advanced:
- it preserves AUROC;
- it materially improves pooled/reserved-year Brier score, ECE, and log loss;
- isotonic calibration is rejected as the primary candidate on current evidence because of instability and poor reserved-year log loss.

### Uncertainty
Paired moving-block bootstrap on 2024 + reserved 2025, calibrated candidate, against the hardest
comparator (lag-1 persistence):

| Comparator | L=2 Brier 95% interval (withdrawn) | L=4 Brier 95% interval (proposed) |
|---|---|---|
| lag-1 | [−0.0829, **+0.0074**] crosses zero | [−0.1040, **−0.0013**] below zero |
| seasonal | [−0.1519, −0.0238] below zero | [−0.1580, −0.0186] below zero |
| seasonal+persistence | [−0.1465, −0.0161] below zero | [−0.1584, −0.0173] below zero |

- On the primary endpoint L=4 is **stronger** than the withdrawn L=2: it is the only lead tested at
  which the lag-1 Brier interval lies entirely below zero. Log loss agrees (L=4 vs lag-1
  [−0.2303, −0.0040] below zero; L=2 crossed).
- AUROC gain over the strongest comparator moves the other way (L=2 +0.0214, L=3 +0.0247, L=4
  +0.0089), but AUROC is a ranking measure and is **not** the primary endpoint (section 23).
- The L=4 lag-1 result is thin: the upper bound is −0.0013. It also leans harder on the frozen
  calibrator, since the *uncalibrated* model at L=4 is worse than all four comparators on Brier.
- The endpoint threshold (median development-era 4-week burden = 32 confirmed cases) is unchanged
  at every lead tested (L=2, 3, 4, 5), so moving to L=4 requires no threshold re-approval.

An earlier draft of this document recorded the opposite conclusion — that L=4 was "not preferred
on current evidence" — from the AUROC sweep alone, before the primary endpoint was evaluated at
L=4. That conclusion was wrong and is withdrawn. The lag constraint and the primary endpoint point
the same way, which removes the temptation the opposite result would have created.

Therefore the current evidence still does not support a one-season "definitive superiority" design.

## 22. Multi-season development direction

The preferred structure to take to human review is now:

1. freeze one v1.2 contract before its first forecast;
2. use L=4 as the primary lead candidate, subject to a defensible first-publication timing source
   replacing the `Last-Modified` proxy (L=2 is withdrawn: 0/36 observed eligibility);
3. use a predeclared Platt calibration rule if the final calibration audit is accepted;
4. treat the first active season as a predeclared interim prospective cohort;
5. continue accumulating immutable forecasts across multiple seasons under the same frozen contract;
6. make no superiority claim at interim unless the predeclared final criterion is already met;
7. publish interim results regardless of direction;
8. define the final information boundary / minimum scoreable observation count before activation, not after observing prospective outcomes.

This section is research guidance only. It does not freeze L=4, Platt scaling, the study duration, or the final success rule.


## 23. Candidate final evaluation structure

The current development evidence supports the following **candidate** evaluation structure for accountable-human review. It is not yet frozen.

### Primary probability-quality endpoint candidate
Paired **Brier-score difference** between GaiaLab and the strongest prespecified comparator on the same scoreable forecasts.

Reason, restated at the proposed L=4 (the figures below replace the L=2 figures an earlier draft
cited, which were derived at a lead now withdrawn):
- calibrated historical proper-score improvement at L=4 is robust versus the seasonal and
  seasonal+persistence baselines, and is the only lead tested that also clears zero versus lag-1;
- empirical information-horizon analysis reaches a two-sided 95% interval below zero versus lag-1
  persistence at about **150** scoreable forecasts under the 4-week block planning model at L=4
  (the ~200 figure was measured at L=2 and must not be inherited);
- log loss at L=4 clears zero by about 100 forecasts, whereas at L=2 it never cleared even at 300 —
  at L=4 the two proper scores agree, which is part of why L=4 is proposed;
- AUROC measures ranking rather than probability quality and is less aligned with the intended calibrated risk output.

### Primary comparator rule candidate
Retain all prespecified comparators and define the final primary comparator rule **before activation**. Do not switch comparators after observing prospective results.

A conservative choice is the strongest comparator on the same scoreable forecasts under the frozen evaluation contract.

### Candidate final information boundary
Minimum **150 scoreable forecasts** before a definitive superiority decision against lag-1
persistence, re-derived at L=4. The previously stated 200 was measured at the withdrawn L=2 and is
not the right requirement for the proposed lead.

This is a planning recommendation, not a guaranteed powered sample size.

At the measured ~13.2 eligible forecasts per 25-week dry season, N=150 is roughly **11 seasons**.
That is stated here rather than buried: beating naive lag-1 persistence decisively is a long
commitment at any feasible lead. The seasonal and seasonal+persistence comparisons are different —
their historical intervals sat entirely below zero at n=104 — so those are plausibly answerable
within a few seasons. The recommended structure is therefore a minimum N with a **hard calendar
stop of four completed dry seasons** (~53 forecasts). **Corrected 2026-10-08:** an earlier version
of this sentence said such a study would be "plausibly decisive against the climatological
baselines." Measured against all four comparators, it is not — at N=53 no interval excludes zero.
A four-season cohort is therefore proposed as a pre-declared **integrity** cohort that cannot
return a superiority verdict, with superiority deferred to a continuing cohort at N=150. See
`LASSA_V1_2_DECISION_PACKAGE.md` section B.

The final protocol must also predeclare:
- whether a maximum calendar duration/seasons applies;
- how to handle failure to reach the minimum eligible-forecast count;
- whether the study is then classified as underpowered/inconclusive;
- whether any early-stopping rule exists (preferred default: none for superiority claims).

### Interim reporting
At the end of each active season:
- publish all forecasts and outcomes;
- report descriptive Brier, AUROC, log loss, calibration and comparator differences;
- label the result as interim unless the final information boundary has been reached;
- do not refit the model, target, lead offset, comparator set, calibration map or decision thresholds mid-study.

### Secondary endpoints
- AUROC;
- log loss;
- ECE/reliability;
- sensitivity to 8-week dependence blocks;
- per-season descriptive results.

Nothing in this section authorizes activation or freeze.
