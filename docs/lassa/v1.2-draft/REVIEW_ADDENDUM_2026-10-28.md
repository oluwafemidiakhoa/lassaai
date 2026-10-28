# v1.2 draft: review addendum, 2026-10-28

> **DRAFT. NOT FROZEN. NOT APPROVED. Decisions B, C, D unsigned.**

## 1. Status

| Item | State |
|---|---|
| v1.1 (frozen 2026-09-23) | All freeze hashes verified 2026-10-28. **Zero valid prospective forecasts; none can be issued this season; operationally blocked.** Interim readout 2027-W05 and final readout after 2027-W21 will run as written; the expected verdict is inconclusive-underpowered (not yet run). |
| v1.2 | Draft. Lead L=4 *proposed*, not frozen. |
| Publication-time evidence | Hash-chained first-observation ledger since 2026-10-10: two records. Automated collection has been blocked on GitHub-hosted runners (HTTP 403) since 2026-10-23; NCDC is checked manually from an operator network meanwhile. |

## 2. Reporting-lag evidence since the 8 October packet

Lag = days from the ISO week's end (Sunday, UTC) to the observation. NCDC's own publication time
is not observable; only bounds are held.

| Week | Week ends | Not visible at | First observed | Lag bound (days) | Source |
|---|---|---|---|---|---|
| 2026-W39 | 09-27 | 10-10 13:52Z | 10-12 16:50Z | 13–15 | ledger |
| 2026-W40 | 10-04 | 10-10 13:52Z | 10-12 16:50Z | 6–8 | ledger |
| 2026-W41 | 10-11 | 10-28 14:47Z (operator check) | not yet | **≥ 17, open** | operator monitoring log (not a ledger record) |
| 2026 W1–W36 | — | — | — | median 17, min 9, p90 25, max 44 (n = 36) | HTTP `Last-Modified` upload-time **proxy**; not publication truth |

**Does v1.2 avoid v1.1's failure? Not yet shown.**

- L=4 tolerates lags under 22 days. W41 has already reached 17 days. If it appears on or after
  2 November, it would be ineligible under v1.2 as well.
- The proxy implies roughly 75% week coverage at L=4 (27 of 36), with a tail beyond 3 weeks.
- What would show it: an eligibility-yield calculation for v1.2 (L=4, L=5, and Candidate B),
  equivalent to `data/lassa/v1-1-eligibility-yield.json`, using directly observed lag bounds from
  several more release events rather than the proxy.

## 3. Additional reviewer questions

These add to the ten in the review packet.

- **Q11.** With batched releases and a tail at or beyond 3 weeks, is a fixed lead (L=4 or L=5)
  still preferable to Candidate B, the next four full ISO weeks after issue? B is eligible by
  construction but has a variable horizon. How should training and comparators handle that?
- **Q12.** Should the lead be frozen only after a minimum number of directly observed release
  events? How many?
- **Q13.** Is a "Phase 1 integrity cohort" with no skill verdict worth running?
- **Q14.** Ineligible weeks are recorded as refusals, not scored. Could refusals concentrate in
  high-incidence periods, and bias the scored cohort?
- **Q15.** Should a hash-chained log of "not visible at time T" checks be a precondition for freezing?
- **Q16.** NCDC reports two different weekly confirmed counts.
  - The **cumulative difference** (the series method) gives 2026-W39 = 19 and W40 = 4.
  - The **narrative "new confirmed this week"** gives W39 = 13 and W40 = 3.

  With an endpoint of more than 32 over 4 weeks, which definition should be primary, and what
  sensitivity analysis should be pre-specified?

## 4. Source integrity

The W39 and W40 report PDFs re-downloaded on 2026-10-28 are byte-identical to the SHA-256 values
recorded at first observation (`de97cbeb…`, `ca2b2f33…`).
