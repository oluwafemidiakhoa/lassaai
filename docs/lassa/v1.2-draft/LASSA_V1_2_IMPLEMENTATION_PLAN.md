# LassaAI v1.2 — Inert Implementation Plan

**Status: PLAN ONLY — NOT BUILT, NOT ACTIVE, NO FORECAST POSSIBLE.**

What exists today is exactly two things: the side-effect-free eligibility guard
(`scripts/lassa/lib/v12_eligibility.py`, wired into nothing) and the first-observation ledger
(`scripts/lassa/lib/first-observation-ledger.mjs` plus its recorder and parallel workflow, which
records observations and cannot issue a forecast). Everything else below is a plan for an
accountable human to approve or refuse.

**Hard rule throughout: no v1.2 object may reuse a v1.1 path.** The frozen v1.1 study keeps its
own series, ledger, receipts and manifest. A v1.2 component that wrote to a v1.1 path would
corrupt a frozen scientific record, and no convenience justifies it.

---

## 1. Object inventory

| Object | Proposed path | Status |
|---|---|---|
| Study ID | `lassa-national-forecast-v1.2` (+ activation date suffix at freeze) | not assigned |
| Eligibility guard | `scripts/lassa/lib/v12_eligibility.py` | **exists, inert, lead required** |
| First-observation ledger | `data/lassa/ncdc-first-observation-ledger.jsonl` | **exists, append-only, dispatch-only workflow** |
| Forecast generator | `scripts/lassa/v12/forecast-now.py` | not built |
| Forecast logger | `scripts/lassa/v12/forecast-logger.py` | not built |
| Forecast ledger | `data/lassa/v12-forecast-log.jsonl` | **does not exist** |
| Outcome recorder | `scripts/lassa/v12/outcome-recorder.py` | not built |
| Outcome ledger | `data/lassa/v12-outcome-log.jsonl` | **does not exist** |
| Public receipt builder | `scripts/lassa/v12/build-receipts.mjs` | not built |
| Public receipts | `public/lassa-v12-receipts.json` | does not exist |
| Readout | `scripts/lassa/v12/readout.py` | not built |
| Freeze manifest generator | `scripts/lassa/v12/freeze-study.py` | not built |
| Freeze manifest | `data/lassa/lassa-v12-freeze.json` | **does not exist** |
| Verification vector | `data/lassa/v12-calibration-verification-candidate.json` | **exists, CANDIDATE** |
| Operations runbook | `docs/lassa/V12_PROSPECTIVE_OPERATIONS.md` | not written |
| Manual workflow | `.github/workflows/lassa-v12-forecast.yml` | **not created — and must not be scheduled** |

Any code written before approval must operate only on fixtures or in an explicit dry-run mode, and
must be incapable of producing a record in a real ledger path.

---

## 2. Forecast ledger record schema (blocker §11)

One JSON object per line, append-only, hash-chained. The record must contain enough to reconstruct
exactly what GaiaLab knew and predicted, without consulting anything mutable.

```jsonc
{
  "schema_version": "gaialab.lassa-v12-forecast.v1",
  "study_id": "lassa-national-forecast-v1.2",
  "sequence": 1,                          // 1-based, strictly incrementing, no gaps
  "issued_at_utc": "2026-10-05T07:14:22.000Z",

  // What the model was allowed to know.
  "data_through": { "epi_year": 2026, "epi_week": 36 },
  "first_observed_at_utc": "2026-09-19T07:02:11.000Z",   // from the observation ledger
  "first_observation_record_sha256": "…",                 // binds THAT ledger line
  "information_source_url": "https://ncdc.gov.ng/…/….pdf",
  "source_sha256": "…",                                   // the report bytes
  "input_series_sha256": "…",                             // canonical series as used

  // The committed prediction.
  "lead": 4,
  "target_span_weeks": 4,
  "target_start": "2026-09-28",
  "target_end": "2026-10-25",
  "threshold_confirmed_cases": 32,
  "raw_model_probability": 0.6123,
  "calibrated_probability": 0.7044,
  "comparator_probabilities": {
    "recent4": 0.55, "lag1": 0.58, "seasonal": 0.49, "seasonal_persistence": 0.52
  },

  // What produced it.
  "booster_sha256": "…",
  "calibrator": { "coef": [2.6934365595797853], "intercept": [-0.7160969922000109],
                  "sha256": "…", "tolerance_contract": "relative 1e-12" },
  "feature_contract_sha256": "…",
  "protocol_sha256": "…",
  "freeze_manifest_sha256": "…",
  "code_commit_sha": "…",
  "environment": { "python": "3.11.16", "numpy": "1.26.4",
                   "scikit_learn": "1.4.2", "xgboost": "2.0.3" },

  "eligibility": { "rule": "issued_at < 00:00:00Z Monday of ISO week (t + 4)",
                   "lead_time_seconds": 812138, "guard_sha256": "…" },

  "previous_record_sha256": "…",
  "record_sha256": "…"
}
```

**The forecast ledger never contains a realised outcome.** No `observed_cases`, no `correct`, no
`brier`. A record that could hold an outcome could be completed after the fact, and the
append-only chain would not detect it because the line would be written once, late. Outcomes live
in their own ledger (§3) and are joined by `record_sha256`.

**Refusals are recorded too**, in a sibling stream `data/lassa/v12-refusal-log.jsonl`, with the
guard's reason code (`target_already_started`, `duplicate_data_through_week`,
`malformed_source_week`, `naive_timestamp_rejected`). A refused opportunity that leaves no trace is
indistinguishable from an opportunity that never existed, and the difference is exactly what an
honest denominator depends on.

---

## 3. Outcome adjudication (blocker §12)

1. **Wait for all four target weeks** to have official NCDC outcomes. A partially observed window
   is never scored.
2. **Primary analysis uses as-first-published values.** For each target week, the confirmed-case
   count as it first appeared in an official report, with that report's URL and SHA-256 preserved.
   This is the only rule that cannot be influenced by a later revision.
3. **Append an outcome record** to `data/lassa/v12-outcome-log.jsonl`, hash-chained in its own
   chain, carrying `forecast_record_sha256` as the join key, the four weekly values with their
   source hashes, the summed target burden, the binary outcome against the threshold, and the
   scores for the model and every comparator.
4. **Never modify the forecast record.** Not to add the outcome, not to correct anything.
5. **Later NCDC revisions** are recorded in a clearly labelled sensitivity stream and may be
   reported only as a secondary sensitivity analysis. The primary result stays on the
   as-first-published rule, whichever direction the revision moves it.

The asymmetry is deliberate: revisions become available only after the outcome is known, so
allowing them into the primary analysis would permit a choice made with knowledge of the result.

---

## 4. Negative scientific-integrity tests (blocker §13)

These are part of the instrument. Each asserts that the system **refuses** something, because the
failure mode for a prospective study is not a crash — it is quietly producing a record it should
have refused. Status reflects what is testable today versus what needs the unbuilt components.

| # | Must refuse | Status |
|---:|---|---|
| 1 | missing explicit lead | **covered** — `lassa-v12-eligibility.test.js`, 3 TypeError proofs + no `DEFAULT_LEAD` |
| 2 | lead mismatch against the frozen manifest | planned (needs manifest) |
| 3 | forecast issued after target start | **covered** — self-test boundary cases |
| 4 | forecast issued exactly at target start | **covered** — strict `<` is pinned |
| 5 | duplicate data-through week | **covered** — guard + self-test |
| 6 | backfill attempt (stale week) | **covered** — guard refuses; v1.1's weaker rule documented |
| 7 | earlier week of a batch after a later week is known | planned — guard supports it via `logged_weeks`; needs the logger |
| 8 | altered model (booster) hash | planned (needs manifest) |
| 9 | altered calibrator beyond tolerance | **partly covered** — negative control in `lassa-v12-calibration-verification.test.js` detects a 1e-6 change |
| 10 | altered threshold | planned (needs manifest) |
| 11 | altered feature contract | planned (needs manifest) |
| 12 | broken ledger hash chain | **covered** — `lassa-first-observation-ledger.test.js` (sever, delete, tamper, duplicate, non-monotonic) |
| 13 | outcome written into the forecast ledger | planned — schema assertion, needs the logger |
| 14 | ambiguous NCDC report year | **covered** — observation ledger refuses boundary and bare-week rows |
| 15 | non-official source as incidence truth | **covered** — official-origin test incl. lookalike host |
| 16 | missing first-observation evidence | planned — the join key makes it enforceable |
| 17 | missing provenance hash | **covered** for observations; planned for forecasts |
| 18 | Platt refit during an active study | planned — manifest binding + tolerance check |

**Covered today: 9 of 18.** The nine planned items all depend on objects that do not exist yet,
and building them now would mean building the forecast chain before the contract is approved —
which is what §10 and §20 of the task forbid.

---

## 5. Build sequence, if approved

1. Assign the study ID and write the operations runbook.
2. Generate the freeze manifest from the approved contract, binding every hash exactly and the
   calibrator under the declared tolerance.
3. Build the forecast generator and logger against **fixtures only**, with negative tests 2, 7, 8,
   10, 11, 13, 16, 18 written **before** the first real run.
4. Build the outcome recorder and its separate ledger.
5. Build receipts and readout.
6. Create the manual workflow — `workflow_dispatch` only, no schedule.
7. Dry-run the full cycle end to end on fixtures and confirm zero writes to any real ledger path.
8. **Only then**, with explicit human authorisation, freeze and issue the first forecast — which
   must be for a target window that has not begun.

Steps 1–7 produce no scientific record. Step 8 is the activation boundary and is not part of this
plan.
