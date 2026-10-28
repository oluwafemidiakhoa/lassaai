# NCDC reporting-lag audit — CORRECTION (2026-10-08)

**Status:** research input for LassaAI v1.2 design. Not a frozen scientific object. This document
**supersedes the lag statistic** in `docs/lassa/NCDC_REPORTING_LAG_AUDIT_2026-10-07.md`. That
document is deliberately left in place unedited: a withdrawn measurement is part of the record.

**Headline:** the previously reported six-day publication lag is a measurement artifact. Under a
genuine upload-time proxy, **no observed 2026 week would have been eligible under lead L=2**
(0 of 36). L=2 must therefore not be frozen, and every L-dependent result must be recomputed for
whichever lead is ultimately chosen.

## 1. Why the six-day figure is invalid

The 2026-10-07 audit computed `archive label − ISO week end` and reported n=7, mean = median =
min = max = p75 = p90 = **6 days, with zero variance**. Zero variance across seven real-world
public-health publication events is itself a warning sign; the cause is a date-field error.

Evidence that the archive label is a **week boundary, not a publication date**:

| Archive row | Label | Download filename date token | ISO week end (committed series) |
|---|---|---|---|
| Week 36 | 05 September 2026 | `..._050926_36.pdf` | 2026-09-06 |
| Week 35 | 29 August 2026 | `..._290826_35.pdf` | 2026-08-30 |
| Week 30 | 25 July 2026 | `..._250726_30.pdf` | 2026-07-26 |

For every row the label equals the **Saturday** of that week, i.e. the MMWR (Sunday–Saturday)
week end, exactly one day before the ISO (Monday–Sunday) week end the committed series uses.
`scripts/lassa/refresh-national-series.py` already warns about this MMWR/ISO convention
difference in its docstring.

The superseded table paired week *N*'s ISO week end with week *N+1*'s label. That subtraction is
structurally `7 − 1 = 6` for every row, which is why the variance was zero. It measured the
spacing between two week boundaries and told us nothing about when NCDC published anything.

## 2. Replacement measurement (upload-time proxy)

Script: `scripts/lassa/v12-publication-lag-probe.py` (reproducible, prints JSON).
Metric: HTTP `Last-Modified` of the official NCDC PDF **minus** the ISO week end taken from the
committed canonical series. Measured 2026-10-08.

Year binding: the report year is taken **only** from an explicit four-digit year in the archive
label. The archive lists same-numbered weeks from 2017–2026, and the filename date token is
ambiguous, so a week number or filename substring must never imply the year. The first run of
this probe did exactly that and admitted 19 prior-year rows with negative "lags" — that bug is
recorded here because it is the same failure mode the protocol's source-integrity rule exists to
prevent.

**n = 36 clean 2026 observations; 3 rows unresolved and marked unknown rather than guessed.**

| Statistic | Days |
|---|---:|
| minimum | 9 |
| median | 17 |
| mean | 17.67 |
| p75 | 19.75 |
| p90 | 25 |
| maximum | 44 |
| standard deviation | 7.7 |

Sorted observations (days): 9, 10, 10, 10, 10, 11, 11, 11, 11, 12, 12, 12, 12, 15, 15, 16, 17,
17, 17, 17, 18, 18, 18, 18, 19, 19, 19, 22, 22, 23, 24, 24, 26, 30, 37, 44.

**Batching:** 11 of 19 distinct upload timestamps cover more than one week (for example
2026-05-26 carries W15–W19; 2026-09-02 carries W32–W34). Batched release is the norm, not the
exception.

### Limitations (these matter and are not rhetorical)

- `Last-Modified` is an upload/re-upload timestamp, not a verified first-publication date.
- A batch timestamp shared by several weeks means the true first release of an individual week
  may have been earlier, so these values may **overstate** true lag.
- A site migration or CDN refresh would reset all timestamps at once.

Therefore this distribution does **not** establish the true lag either. What it establishes is
that the six-day figure cannot be relied on, and that the whole observed distribution sits far
from the ≤8-day ceiling L=2 requires.

## 3. Eligibility consequence

For data-through ISO week *t* and lead *L*, the target window opens on the Monday of week
*t+L*, which is `1 + 7(L−1)` days after *t*'s ISO week end. An opportunity is eligible only if
the report is published **before** that instant:

> eligible ⟺ publication lag < 1 + 7(L−1) days

| Lead | Max tolerated lag | Observed coverage (n=36) |
|---|---:|---:|
| L=2 | < 8 days | **0 / 36 (0%)** |
| L=3 | < 15 days | 13 / 36 (36%) |
| L=4 | < 22 days | 27 / 36 (75%) |
| L=5 | < 29 days | 33 / 36 (92%) |
| L=6 | < 36 days | 34 / 36 (94%) |

The minimum observed lag is 9 days. Even allowing that the proxy may overstate lag, **not one
observation falls under L=2's 8-day ceiling.** A v1.2 study frozen at L=2 would be structurally
incapable of logging a single eligible forecast.

## 4. What this invalidates

L is not a free parameter: it determines the target window, hence the development threshold
(median four-week burden at that lead) and therefore every metric. All of the following are
conditional on L=2 and must be recomputed for the chosen lead before freeze:

- `docs/lassa/LASSA_V1_2_LEAD_OFFSET_AUDIT_RESULTS.md`
- `docs/lassa/LASSA_V1_2_CALIBRATION_AUDIT_RESULTS.md`
- `docs/lassa/LASSA_V1_2_PROPER_SCORE_UNCERTAINTY_RESULTS.md`
- `docs/lassa/LASSA_V1_2_INFORMATION_HORIZON_RESULTS.md` (fixed at L=2)
- the `L=2` preference in `docs/lassa/LASSA_V1_2_FREEZE_READINESS.md`

The audit sweeps have been widened to L=2–5 (calibration, uncertainty) and L=1–6 (lead offset) so
that evidence exists for the leads the lag constraint actually permits.

## 5. Selection rule (integrity guard)

**L must be chosen by the eligibility constraint, which is an operational pre-outcome criterion,
and never by which lead scores best on 2024/2025.** Those years are the untouched and reserved
evaluation sets; picking L by their scores would convert them into a selection set and destroy
their value. The widened sweep exists to confirm that the lag-forced lead is *usable*, not to
choose a winner.

Recommended procedure before freeze:

1. Establish a defensible first-publication timestamp source (see §6) and re-estimate the lag
   distribution.
2. Choose the smallest L whose tolerated-lag ceiling exceeds a pre-declared coverage target (for
   example p90 lag) — declared before looking at any score for that L.
3. Only then read the audit results for that L, to confirm the design is worth running at all.

## 6. Open requirement before freeze

A first-publication timestamp source that does not depend on `Last-Modified`. Candidates:

- a date printed inside the PDF body (publication or approval date), parsed as primary evidence;
- an NCDC feed/API exposing publication timestamps, if one exists;
- independent dated archival snapshots (for example Internet Archive captures) as corroboration;
- prospective observation: record, from now on, the first date on which the detector observes
  each new week. This is the cleanest source, costs nothing, and begins accumulating immediately.

Until one exists, the lag distribution should be treated as **not reliably measured**, and no
lead offset should be frozen.

## 7. Scientific boundary

This is a measurement correction affecting study design only. It is not evidence about forecast
skill, and no v1.2 forecast has been issued. Frozen v1.1 objects are untouched; the v1.1 timing
mismatch remains disclosed as historical evidence.
