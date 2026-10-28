# LassaAI v1.2 — Human Decision Package (blockers B, C, D)

**Status: PROPOSED — NOTHING FROZEN, NOTHING ACTIVE, NO FORECAST ISSUED.**

This document converts the three open contract blockers into decisions an accountable human can
sign or refuse. It does not freeze them. It is the companion to
[`LASSA_V1_2_PRE_FREEZE_REVIEW.md`](LASSA_V1_2_PRE_FREEZE_REVIEW.md) (the evidence packet) and
[`LASSA_V1_2_FREEZE_READINESS.md`](LASSA_V1_2_FREEZE_READINESS.md) (the gate memo), and must not
disagree with either.

Proposed contract under discussion throughout: **L=4**, target weeks t+4..t+7, eligibility
`issued_at < start_of_week(t+4)`, endpoint `> 32` confirmed cases over the four-week window, base
XGBoost fitted on epi-years ≤2022, Platt calibrator fitted on 2023 only.

---

## A. The headline finding, and it changes the recommendation

**The four-season calendar stop recommended by the earlier drafts was justified by a claim that
is now measured false.** Those drafts said a four-season study would "report NEUTRAL against
lag-1 while plausibly being decisive against the seasonal baselines." The second clause had never
been measured — the planning audit only ever compared against lag-1 persistence — so it was an
assumption carried forward as if it were evidence.

It has now been measured against all four pre-specified comparators (CI run on commit `b7186795`,
frozen environment, paired moving-block bootstrap, 4-week blocks, 5000 replicates, seed 20260923,
with the same resampled index series applied to every comparator so the comparators are paired
with each other as well as with the model):

| N | ≈ seasons | lag-1 | recent-4 | seasonal | seasonal+persistence |
|---:|---:|---|---|---|---|
| 13 | 1.0 | crosses | crosses | crosses | crosses |
| 26 | 2.0 | crosses | crosses | crosses | crosses |
| 40 | 3.0 | crosses | crosses | crosses | crosses |
| **53** | **4.0** | **crosses** | **crosses** | **crosses** | **crosses** |
| 80 | 6.1 | crosses | **below 0** | **below 0** | **below 0** |
| 106 | 8.0 | **below 0** | below 0 | below 0 | below 0 |
| 150 | 11.4 | below 0 | below 0 | below 0 | below 0 |
| 200 | 15.2 | below 0 | below 0 | below 0 | below 0 |

Brier 95% intervals at the decision-relevant sizes:

| N | lag-1 | seasonal |
|---:|---|---|
| 53 | [−0.1244, **+0.0191**] | [−0.1887, **+0.0066**] |
| 80 | [−0.1127, **+0.0060**] | [−0.1686, −0.0093] |
| 106 | [−0.1064, −0.0007] | [−0.1584, −0.0166] |

**At four seasons nothing clears zero — not even the climatological baselines.** A four-season
study framed as a superiority test would be expected to return NEUTRAL against every comparator,
including the ones it was assumed to beat. The seasonal interval at N=53 misses by +0.0066, which
is close, but "close" is not a result.

### The consequence almost nobody notices until it is too late

The primary comparator rule is **the strongest pre-specified comparator on the same scoreable
forecasts**. Look at which comparator that is. By median Brier difference the model's advantage is
*smallest* against lag-1 (−0.0506) and largest against seasonal (−0.0834). **Lag-1 persistence is
the strongest comparator**, so under the declared rule the primary endpoint is effectively the
lag-1 comparison and nothing else.

Therefore **clearing the seasonal baselines at N=80 would not produce SUCCESS.** It would produce
NEUTRAL, because the primary endpoint is measured against lag-1, which has not cleared. The study
is powered by the lag-1 requirement alone: **N ≈ 106–150, i.e. roughly 8–11 seasons.**

This is not an argument for dropping lag-1. §7 of the task is right that lag-1 must stay precisely
because it is difficult, and swapping to a weaker comparator after seeing these numbers would be
comparator-shopping. It is an argument for being honest about what a bounded study can deliver.

### How precisely can the crossing point be stated?

Not as precisely as earlier drafts implied. The original lag-1-only sweep put the Brier crossing
at N=150 with N=100 still crossing (upper +0.0013). The new pass puts it at N=106 (upper
−0.0007), with N=80 still crossing (upper +0.0060). These are different resampling streams, and
near the boundary the answer moves. **The honest statement is "somewhere around N≈100–150, call it
8–11 seasons," and the figure should never be quoted to three significant figures.** The earlier
"N=150" was stated with more precision than the method supports; it is better read as the
conservative end of that range.

---

## B. Information boundary — **RECOMMENDATION: reject the single four-season superiority study; declare two phases**

A single bounded study cannot both be short enough to commit to and long enough to answer the
primary question. Declaring one thing and hoping is how goalposts move. So declare both, before
activation, with different purposes and different permissible verdicts.

### Phase 1 — Prospective integrity cohort (bounded: 4 completed dry seasons, ≈53 forecasts)

**Purpose: prove the instrument, not the skill.** Pre-declared as **underpowered for superiority**
and *incapable of returning SUCCESS or FAILURE on the primary endpoint.*

This is a real scientific contribution, not a consolation prize. The two things that have actually
gone wrong in this program were both instrument failures, not skill failures: the v1.1 guard
admitted forecasts whose target had already begun (`window_end > today`), and the six-day lag
figure was a measurement artifact that would have produced a study with zero eligible forecasts.
Phase 1 tests, prospectively and in public, that:

- every logged forecast was issued strictly before its target window opened;
- every ineligible opportunity was recorded as a refusal rather than quietly dropped;
- the hash chain is unbroken and no record was ever rewritten;
- first-observation evidence exists for every week used;
- the frozen calibrator was applied unchanged for four seasons;
- the realised eligible-forecast yield matches the ~13.2/season planning estimate — which is
  currently an estimate from an upload-time proxy and may be wrong.

**Permitted Phase 1 verdicts:** `INSTRUMENT VALIDATED` / `DATA-INTEGRITY FAILURE` /
`MATERIAL CALIBRATION FAILURE` / `YIELD ASSUMPTION REFUTED`. Descriptive Brier, log loss, ECE,
AUROC and all four comparator differences are **published with intervals** and labelled interim
and underpowered. No superiority claim is permitted at Phase 1 whatever the numbers show.

### Phase 2 — Superiority cohort (continuing, same frozen contract)

Begins automatically at the end of Phase 1 unless Phase 1 returned a failure verdict. Same frozen
model, calibrator, lead, threshold, comparators and eligibility rule — a methodology change starts
v1.3 and resets the cohort.

- **Information boundary:** minimum **N = 150** scoreable forecasts against the strongest
  comparator, chosen as the conservative end of the measured N≈106–150 range.
- **Calendar backstop:** report at every season end regardless; if N=150 is not reached by the end
  of season 12, the study closes as `UNDERPOWERED / INCONCLUSIVE` and says so.
- **No early stopping for superiority.** Interim reports are descriptive only.

### Why not simply run one 11-season study?

It is the same total commitment either way, so the question is only whether anything gets reported
before roughly 2037. Phase 1 makes a four-season reporting point *meaningful* rather than
disappointing: it answers a question it can actually answer. The alternative — declaring an
11-season superiority study and publishing "still crossing zero" eight times — invites exactly the
pressure to redefine success that this structure exists to prevent.

**Both boundaries must be declared before activation.** Phase 2's N is not permitted to move after
any prospective outcome is observed, and Phase 1's inability to claim superiority is not permitted
to be revisited because its point estimate looked good.

---

## C. Success contract — **RECOMMENDATION: adopt as written below**

Applies to **Phase 2 only**. Phase 1 can return none of SUCCESS, FAILURE or NEUTRAL on the
primary endpoint.

**Primary endpoint:** paired **Brier-score difference** (calibrated model − strongest
pre-specified comparator) on the same scoreable forecasts, with a dependence-aware paired
moving-block bootstrap (4-week blocks primary, 8-week sensitivity).

**Comparator set, all four retained, none removable:** recent-4-week persistence; lag-1
persistence; harmonic seasonal climatology; seasonal + persistence logistic regression. The
*strongest* comparator on the same scoreable forecasts is the primary one, determined by the
frozen rule and never re-chosen after seeing results. On current evidence that will be lag-1.

### SUCCESS — all five required

1. the study reached its pre-declared information boundary (N ≥ 150 scoreable forecasts);
2. calibrated model Brier is lower than the strongest pre-specified comparator's;
3. the paired dependence-aware 95% interval for that difference lies **entirely below zero**;
4. no data-integrity failure occurred at any point in the study;
5. no material calibration failure (see below).

### FAILURE — any one sufficient

1. the paired 95% interval lies **entirely above zero** (significantly worse than the strongest
   comparator);
2. the model is beaten by the strongest comparator on **both** Brier and log loss with intervals
   excluding zero;
3. a material calibration failure occurs: **accumulated-cohort** ECE (5 bins) > 0.25.

### NEUTRAL

Point estimate favourable (or unfavourable) but the paired 95% interval crosses zero; or secondary
metrics disagree without changing the primary outcome. **NEUTRAL is a legitimate published result,
not a deferral.**

### UNDERPOWERED / INCONCLUSIVE

Fewer than 150 scoreable forecasts at the calendar backstop; or insufficient outcome-class
variation to compute the endpoint (e.g. a cohort with almost no elevated windows); or the primary
metric cannot be computed from the available records.

### DATA-INTEGRITY FAILURE — overrides every other verdict

Any one of: a forecast issued at or after its target window opened; forecast bytes changed after
commitment; model, calibrator, lead, threshold or feature contract changed during the study;
provenance became unverifiable; the hash chain broke; a retrospective or backfilled forecast
entered the prospective ledger; an outcome was written into the forecast ledger; a week was used
without first-observation evidence.

A data-integrity failure **voids the superiority claim for the affected cohort** and is published
as such. There is no partial credit and **no rescue rule** — no "excluding the affected weeks"
re-analysis may be presented as the primary result.

### On the ECE criterion — why it is accumulated-cohort only

A per-season ECE auto-fail at 0.25 would be wrong, and the number says so: at the proposed L=4 the
**reserved 2025 season alone has Platt ECE 0.3064** (0.2887 at the withdrawn L=2). A single season
near 0.30 is within this model's observed behaviour, so a per-season trigger would fail the study
on behaviour already known before activation. Per-season ECE is published as a secondary
diagnostic.

**Secondary endpoints (never promoted to primary):** AUROC; log loss; ECE (5 bins) and reliability
curve; 8-week block sensitivity; per-season descriptive results; eligible-vs-refused opportunity
counts.

AUROC is **secondary, not co-primary.** Treating it as co-primary is precisely what produced the
withdrawn L=2 recommendation: ranked by AUROC gain, L=2 (+0.0214) beat L=4 (+0.0089), and that
ranking was both operationally impossible and wrong on the primary endpoint.

---

## D. Calibration freeze rule — **RECOMMENDATION: adopt as written below**

**Freeze the pre-prospective calibrator and never refit it during the study.** No expanding-window
recalibration, no refit after any prospective outcome is observed, no per-season adjustment. A
refit mid-study starts v1.3 and resets the cohort.

### Why this blocker is load-bearing rather than procedural

The favourable L=4 result depends **entirely** on the frozen calibrator. The *uncalibrated* model
at L=4 is worse than all four comparators on Brier (lag-1 +0.0495). And Platt is not uniformly
better: in **2024 alone it is worse than raw on both Brier (0.1232 vs 0.1153) and ECE (0.1430 vs
0.1311)**, and better only on log loss. The entire pooled gain comes from 2025, where raw
calibration collapses (Brier 0.3826 → 0.1971).

So Platt is a **robustness measure against bad years**, not a general improvement. That must be
stated in any publication: a reader shown only the pooled row would conclude something false about
what calibration does here.

### Verification rule — tolerance where non-determinism was measured, exact everywhere else

Exact string or hash equality on the calibrator is **not** a valid reproduction check. Two CI runs
of the same commit in the same pinned environment produced coefficients one float64 ULP apart
(`2.6934365595797853` vs `2.693436559579785`, 1.6×10⁻¹⁶ relative), from L-BFGS summation order.
A freeze manifest demanding exact equality would reject a correct reproduction.

| Bound value | Rule |
|---|---|
| Platt coefficient, intercept | relative tolerance **1×10⁻¹²** |
| Calibrated probabilities on the verification vector | absolute tolerance **1×10⁻¹²** |
| Booster SHA-256 | **exact** (measured bit-reproducible across runners) |
| Input series SHA-256 | **exact** |
| Protocol, code, environment-lock hashes | **exact** |

Tolerance is applied **only** where floating-point non-determinism was actually observed, so it
cannot be used to wave through a different model. Headroom is explicit: the largest observed
cross-runner probability drift is 2.2×10⁻¹⁶ against a declared tolerance of 1×10⁻¹², a factor of
~4,500 — and a negative control confirms that a merely 1×10⁻⁶ relative coefficient change is
detected.

**Binding fixture:** [`data/lassa/v12-calibration-verification-candidate.json`](../../data/lassa/v12-calibration-verification-candidate.json)
— eleven raw probabilities spanning very low to very high plus both boundaries, with expected
calibrated outputs. CANDIDATE, not frozen. `lassa-v12-research-eval` validates it against the
calibrator freshly fitted on that runner, which is a genuinely different machine from the one that
produced the fixture, so agreement is cross-machine evidence rather than self-consistency.

### Known limitation

The in-job reproducibility gate generates the candidate twice on one runner and finds bit-identical
calibrators — the drift is **cross-runner**, not within-machine. So a green in-job gate does not by
itself establish the cross-machine tolerance; the fixture validation above is what does. A
reference calibrator value is deliberately **not** committed as a frozen constant, because a stored
expected value could be mistaken for a freeze. It belongs in the freeze manifest, after approval.

---

## E. What this package does *not* decide

- **The lead is not frozen.** L=4 remains proposed, blocked on a defensible first-publication
  timestamp source (blocker A). The upload-time proxy is adequate to disqualify L=2 and rank
  leads; it is not publication truth and must not be promoted into it.
- **No study ID, manifest, ledger or forecast exists.**
- **No schedule is active.**

## F. Decision

| Blocker | Recommendation | Decision |
|---|---|---|
| B — information boundary | Two phases: 4-season integrity cohort (no superiority verdict), then N=150 superiority cohort with a season-12 backstop | `APPROVE / REVISE / REJECT` → ________ |
| C — success contract | Adopt section C as written; lag-1 retained; AUROC secondary; ECE accumulated-cohort only; no rescue rule | `APPROVE / REVISE / REJECT` → ________ |
| D — calibration freeze rule | Freeze and never refit; tolerance 1×10⁻¹² on calibrator values, exact on all hashes | `APPROVE / REVISE / REJECT` → ________ |

Approving these three authorises **final protocol drafting only**. It does not authorise a
scientific freeze, a prospective forecast, a schedule, a merge to production, or any public
performance claim.

Accountable human: ______________________  Date (UTC): ______________

**No AI system has authority to sign or freeze the scientific protocol.**
