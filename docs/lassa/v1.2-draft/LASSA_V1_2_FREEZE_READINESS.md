# LassaAI v1.2 — Freeze Readiness Gate

**Status:** NOT READY TO FREEZE

**Revision 2026-10-08:** this memo previously advanced **L=2** as the primary development
candidate on the strength of a six-day NCDC reporting-lag sample and an AUROC sweep. Both inputs
were wrong. The six-day lag was a week-boundary subtraction artifact, and the AUROC sweep is not
the primary endpoint. **L=2 is withdrawn** (0 of 36 observed 2026 weeks would have been eligible)
and **L=4 is the current proposed lead, pending accountable-human approval and a defensible
first-publication timing source.** The withdrawn L=2 evidence is retained below as development
history because the way it failed is itself a finding. The authoritative packet is
`LASSA_V1_2_PRE_FREEZE_REVIEW.md`; this memo is its decision-gate summary and must not disagree
with it.

This memo summarizes the current evidence on the reporting-lag-aware national Lassa forecasting design. It is a decision gate, not a frozen protocol and not a prospective result.

## 1. Current preferred design

Primary development candidate:

- **lead offset:** L=4 *(proposed; not frozen. L=2 withdrawn — see section 2)*;
- **target:** four-week national confirmed-case burden over weeks t+4 through t+7;
- **development endpoint threshold:** >32 confirmed cases over the target window — confirmed
  unchanged at every lead tested (L=2, 3, 4, 5), so the move to L=4 needs no threshold re-approval;
- **base model family:** XGBoost with the existing v1.1 feature family, hyperparameters identical
  across all leads (no per-lead tuning);
- **calibration candidate:** Platt scaling using a temporally separate calibration period;
- **primary probability-quality metrics:** Brier score and log loss;
- **secondary discrimination metric:** AUROC;
- **comparators:** recent-4-week persistence, lag-1 persistence, harmonic seasonality, seasonal+persistence logistic;
- **dependence-aware uncertainty:** paired moving-block bootstrap;
- **prospective structure:** multi-season program with the first active season predeclared as interim.

None of these items are frozen by this memo.

## 2. Evidence on the lead offset — L=2 withdrawn, L=4 proposed

**The lead is chosen by the eligibility constraint, not by held-out scores.** 2024 is the
untouched set and 2025 the reserved set; picking L by their scores would convert them into a
selection set. The sweeps were widened only to confirm the lag-forced lead is usable.

Eligibility under the measured publication-lag distribution (upload-time proxy, n=36, median 17
days, min 9, p90 25, max 44):

| Lead | Max tolerated lag | Observed week coverage (n=36) | Eligible information boundaries | Est. forecasts / 25-week season |
|---|---:|---:|---:|---:|
| L=2 *(withdrawn)* | < 8 days | **0 / 36 (0%)** | **0 / 19** | **~0** |
| L=3 | < 15 days | 13 / 36 (36%) | 13 / 19 | ~9.0 |
| **L=4 (proposed)** | **< 22 days** | 27 / 36 (75%) | **19 / 19** | **~13.2** |
| L=5 | < 29 days | 33 / 36 (92%) | 19 / 19 | ~13.2 |

L=4 is the smallest lead reaching full eligibility across every observed 2026 information
boundary. It does **not** cover the measured tail (21-day tolerance against a p90 of 25 and a
maximum of 44), so some releases will be refused as ineligible opportunities — recorded, never
backfilled. L=5 is the robustness alternative if a primary timing source shows a heavier tail.

**Withdrawn L=2 rationale, retained as history.** The earlier version of this section read: "L=1
is not compatible with a strict fully-future target under the directly verified recent NCDC
six-day reporting-lag sample; L=2 retains positive AUROC gain in 2024, reserved 2025, and pooled
evaluation; L=3 has more lag tolerance but greater year-to-year instability; L=4 has weaker pooled
discrimination," with L=2 pooled AUROC ≈0.812 against a strongest-comparator ≈0.791 for a point
gain of ≈+0.021. Two defects: the six-day lag was a measurement artifact, and ranking leads by
AUROC gave the wrong answer because **AUROC is not the primary endpoint**.

**On the primary endpoint L=4 is stronger than L=2.** AUROC gain does fall with lead (L=2 +0.0214,
L=3 +0.0247, L=4 +0.0089; lead-offset audit, train ≤2023), but the primary endpoint is the paired
Brier difference for the calibrated candidate, and there L=4 is better against **every**
comparator and is the only lead tested at which the lag-1 interval clears zero (section 4).

This is development evidence only.

## 3. Evidence supporting Platt calibration

Temporal calibration audit:
- endpoint threshold defined from <=2023 development data;
- base model fit <=2022;
- calibrator fit on 2023 only;
- 2024 and reserved 2025 untouched for evaluation.

Calibrated Brier is nearly flat across leads — L=2 0.1587, L=3 0.1618, **L=4 0.1602**, L=5 0.1617
— so the longer lead costs little in probability quality while degrading the baselines
substantially. Platt leaves AUROC unchanged (the mapping is monotonic).

At the proposed **L=4**, pooled 2024+2025 (frozen environment, CI run 37796979614): raw Brier
0.2490 → Platt **0.1602**; raw ECE-5 0.2796 → Platt **0.1463**; raw log loss 0.9381 → Platt
**0.4832**; AUROC 0.8097 either way. The full per-cohort table is in
`LASSA_V1_2_PRE_FREEZE_REVIEW.md` section V. The L=2 equivalents (Platt Brier 0.1587, ECE 0.1439,
log loss 0.4860) are retained there for comparison only.

Two provenance cautions that must not be dropped downstream:

1. **Do not mix the two training designs.** The lead-offset audit trains on ≤2023; the calibration
   and proper-score audits train on ≤2022 with a 2023 calibrator — a different model. The frozen
   candidate is the ≤2022 + Platt specification, so quoting the ≤2023 audit's AUROC alongside
   Platt's Brier describes a model that does not exist.
2. **Report the raw model too.** The *uncalibrated* model at L=4 is worse than all four
   comparators on Brier (lag-1 +0.0495), whereas at L=2 it at least beat the seasonal pair. The
   favourable proper-score result at L=4 depends **entirely** on the frozen calibrator, which
   makes the calibration-freezing rule (blocker D) load-bearing rather than procedural.

Isotonic calibration is not advanced because of instability and poor reserved-year log loss
(L=2 pooled log loss 2.7198 versus Platt 0.4860).

## 4. Proper-score uncertainty

Paired moving-block bootstrap, calibrated candidate, pooled 2024 + reserved 2025, 4-week blocks
(model − comparator; negative favours GaiaLab):

| Comparator | L=2 Brier 95% CI *(withdrawn)* | L=4 Brier 95% CI *(proposed)* |
|---|---|---|
| lag-1 | [−0.0829, **+0.0074**] crosses zero | [−0.1040, **−0.0013**] below zero |
| recent-4 | [−0.0962, +0.0013] crosses zero | [−0.1164, −0.0108] below zero |
| seasonal | [−0.1519, −0.0238] below zero | [−0.1580, −0.0186] below zero |
| seasonal+persistence | [−0.1465, −0.0161] below zero | [−0.1584, −0.0173] below zero |

Log loss behaves the same way (L=4 vs lag-1 [−0.2303, −0.0040], below zero; L=2 crossed). 8-week
blocks agree in sign and conclusion. The mechanism is unsurprising: over a four-week-further
horizon, naive persistence loses skill faster than a model carrying seasonality and trend.

Three cautions that keep this honest:
- the lag-1 upper bound at L=4 is **−0.0013**, only marginally below zero — a thin historical
  margin, not a robust result;
- it leans harder on the frozen calibrator (section 3, caution 2);
- it is retrospective evidence on 2024+2025 and establishes **no** prospective skill.

Therefore the historical evidence supports further development but does not establish robust superiority over every prespecified comparator.

## 5. Why a one-season definitive claim is not appropriate

The expected prospective cohort is **~13.2 eligible forecasts per 25-week dry season** at L=4 —
about four times slower than the 104 held-out weekly observations used in the historical
uncertainty analysis, because releases are batched rather than weekly.

Measured planning audit (not a power calculation), paired Brier vs lag-1, the hardest comparator:

| N | L=2 Brier | L=2 log loss | L=4 Brier | L=4 log loss |
|---:|---|---|---|---|
| 50 | crosses 0 | crosses 0 | crosses 0 | crosses 0 |
| 100 | crosses 0 | crosses 0 | crosses 0 (upper +0.0013) | **below 0** |
| 150 | crosses 0 (upper +0.0001) | crosses 0 | **below 0** (upper −0.0092) | **below 0** |
| 200 | **below 0** | crosses 0 | below 0 | below 0 |
| 300 | below 0 | **still crosses 0** | below 0 | below 0 |

The requirement against lag-1 falls from roughly **N=200 at L=2 to N=150 at L=4**, and log loss —
which never cleared zero at L=2 even at N=300 — clears at N=100 at L=4. At ~13.2 forecasts per
season, N=150 is roughly **11 seasons**. Beating naive lag-1 persistence decisively is a long
commitment at any feasible lead; the seasonal and seasonal+persistence comparisons sat entirely
below zero at n=104 historically and are plausibly answerable within a few seasons.

Therefore the proposed v1.2 structure is:
1. first active season = prospectively frozen interim cohort;
2. publish the interim result regardless of sign;
3. continue collecting forecasts under the unchanged frozen contract;
4. final inference only at a predeclared multi-season information boundary or minimum
   scoreable-observation count, with the minimum N taken from the **L=4** planning audit and not
   inherited from the L=2 figure;
5. any methodological change starts a new protocol version.

## 6. Remaining blockers before freeze

### BLOCKER A — No defensible first-publication timestamp source *(unresolved; now the binding blocker)*

The original form of this blocker — "the directly verified recent sample is only W30-W35, all with
six-day lag" — has been partly discharged and partly inverted. The audit was expanded to all 36
observed 2026 weeks, which is what **exposed** the six-day figure as an artifact. But the
replacement measurement rests on an HTTP `Last-Modified` upload-time proxy.

A proxy is adequate to **disqualify** L=2 and to rank leads. It is **not** a defensible
first-publication source and must **not** be promoted into one. Before freezing any L:
- establish a first-publication timestamp source independent of `Last-Modified`. The cheapest and
  cleanest is to begin recording, from now on, the first date the detector observes each new week —
  it costs nothing and should start immediately, before any freeze decision;
- re-estimate the lag distribution against that source and confirm the lead;
- keep the existing rule: do not infer publication dates from ambiguous week-number archive rows
  (that rule is exactly what the six-day artifact violated);
- keep the explicit definition of how delayed/batched releases become ineligible opportunities.

If the source-based lag distribution shows a materially heavier tail than the proxy, move to L=5
rather than relaxing the eligibility rule.

### BLOCKER A2 — Per-cohort calibration table at L=4 — **RESOLVED 2026-10-08**

Discharged by CI run 37796979614 on commit `ba02e4ce`: the calibration audit was run at L=4 in the
frozen environment and the per-cohort raw/Platt/isotonic table is published in
`LASSA_V1_2_PRE_FREEZE_REVIEW.md` section V. The frozen median rule yields threshold **32.0** at
L=4, as it does at L=2, 3 and 5. The freeze-candidate generator and the calibration audit agree in
the same run on threshold (32.0), base fit n (149) and calibrator n (52), so the two scripts have
not drifted apart.

Two findings from that table that the final protocol must carry forward:
- in **2024 alone** Platt is worse than raw on Brier *and* ECE; the pooled gain comes entirely
  from 2025, where raw calibration collapses. Platt is a robustness measure, not a uniform
  improvement;
- **reserved-2025 Platt ECE is 0.3064 at L=4**, which is what makes a per-season ECE auto-fail at
  0.25 unsound (blocker C).

### BLOCKER B — Final prospective information boundary is not defined

Predeclare one of:
- a fixed final date/season count;
- a minimum scoreable forecast count;
- or both.

**Recommendation revised 2026-10-08** — see
[`LASSA_V1_2_DECISION_PACKAGE.md`](LASSA_V1_2_DECISION_PACKAGE.md) section B. A four-season
superiority study was measured and found to be decisive against **nothing**: at N=53 no
comparator's interval excludes zero, including the climatological baselines the earlier
recommendation assumed it would beat (seasonal [−0.1887, +0.0066]). And because the model's
advantage is smallest against lag-1, lag-1 **is** the strongest comparator, so the primary
endpoint is the lag-1 comparison alone and the study's power is the lag-1 requirement: N≈106–150,
roughly 8–11 seasons.

The recommendation is therefore **two separately declared phases**, both fixed before activation:
a bounded four-season **integrity cohort** that is pre-declared underpowered and *cannot* return a
superiority verdict, followed by a **superiority cohort** at N=150 with a season-12 calendar
backstop.

Do not choose the boundary after looking at prospective results.

### BLOCKER C — Final success/neutral/failure contract is not defined

The final v1.2 protocol must state:
- primary metric;
- strongest-comparator rule;
- effect-size requirement if any;
- confidence/uncertainty requirement;
- treatment of underpowered interim data;
- calibration acceptance criterion — noting that a per-season ECE auto-fail would be wrong: at the
  proposed L=4 the reserved 2025 season alone has Platt ECE **0.3064** (0.2887 at L=2), which is
  within observed behaviour for this model, so the criterion applies to the accumulated cohort and
  ECE is reported as a per-season diagnostic;
- whether AUROC is secondary rather than co-primary (it is secondary — treating it as co-primary
  is what produced the withdrawn L=2 recommendation).

### BLOCKER D — Prospective calibration fitting rule is not defined

The final protocol must state exactly how Platt scaling is frozen and applied:
- whether the calibration mapping is frozen from pre-2026 development data and never refit;
- or whether any expanding-window recalibration is allowed.

Preferred integrity-preserving default: freeze the pre-prospective calibrator and do not refit during the active study. This blocker is load-bearing at L=4, because the uncalibrated model at L=4 is worse than every comparator on Brier (section 3, caution 2).

**It must also state a numeric tolerance.** Two independent CI runs of the same commit in the same
pinned environment produce a bit-identical booster and threshold but a Platt coefficient differing
by one float64 ULP (2.6934365595797853 vs 2.693436559579785; L-BFGS summation order). The
probability effect is ≤1.1×10⁻¹⁶ and does not matter scientifically, but it means the freeze
manifest cannot verify the calibrator by exact hash or string equality — it needs a declared
tolerance or precision, and it must assume verification happens on a different machine from the
one that produced the frozen values, since the drift is cross-runner: generating the candidate
twice within a single CI job yields bit-identical calibrators. CI enforces 1×10⁻¹² relative
in-job, which catches genuine instability but does not by itself establish the cross-machine
tolerance the manifest needs.

### BLOCKER E — Operational v1.2 implementation does not yet exist

Do not repurpose the frozen v1.1 logger.

A future v1.2 implementation requires separate:
- study ID;
- forecast generator;
- logger/ledger;
- public receipts;
- outcome recorder binding;
- freeze manifest;
- tests;
- runbook.

These should be created only after the human approves the final protocol design. The one component
that exists is the inert eligibility guard (`scripts/lassa/lib/v12_eligibility.py`), which is
side-effect free, takes the lead as a required argument with no default, and is wired into nothing.

## 7. Proposed human decision

Current recommendation:

**REVISE — L=2 is withdrawn; L=4 is the current proposed lead, pending human approval and a
defensible publication-time source. Advance L=4 + frozen Platt calibration into final protocol
drafting, but do not freeze or activate until a first-publication timestamp source independent of
HTTP `Last-Modified` exists and the final multi-season decision contract is complete.**

The consistency corrections recorded in this revision do **not** move the verdict toward READY.
They remove a contradiction between documents; the scientific blocker (blocker A) is untouched.

Suggested decision gate:

- [ ] APPROVE current direction for final protocol drafting
- [ ] REVISE direction
- [ ] REJECT direction

Approval here would authorize final protocol drafting only. It would **not** authorize a scientific freeze, prospective forecast, merge to production, or public performance claim.

## 8. Scientific claim boundary

Allowed now:
- "L=4 + Platt is the leading development candidate, proposed and not frozen."
- "L=2 was withdrawn because it would have yielded no eligible forecasts."
- "Historical evaluation supports further prospective testing."
- "Proper-score improvement versus seasonal baselines is robust in the historical held-out analysis."

Not allowed now:
- "GaiaLab prospectively predicts Lassa better than baselines."
- "v1.2 is validated."
- "L=4 is proven superior." (Its lag-1 margin is thin, retrospective, and calibrator-dependent.)
- "The measured publication lag is the true first-publication lag." (It is an upload-time proxy.)
- "The study is frozen."
- "The 2026-27 season will be sufficient for definitive validation."

Prospective evidence begins only after the final v1.2 protocol is approved, frozen, timestamped, and the first eligible forecast is logged before its target window begins.
