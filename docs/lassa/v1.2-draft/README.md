# LassaAI v1.2: DRAFT protocol, published for comment

> **DRAFT. NOT FROZEN. NOT APPROVED. NOT ACTIVE.**
> Decisions B (information boundary), C (success contract) and D (calibration freeze) are
> **unsigned**. No v1.2 forecast, freeze manifest, ledger or schedule exists. Nothing here amends,
> reinterprets or rescues the frozen v1.1 study (`lassa-national-forecast-2026-27-v1.1`,
> `docs/lassa/PROSPECTIVE_PROTOCOL_LASSA.md`), which stays frozen and will be read out as written.

Published 2026-10-28, as committed publicly on 2026-10-27: *the draft will be published before
anything is frozen.* Any later freeze will be a new, separately versioned commit. This draft
will not be silently edited into the frozen version.

## Why v1.2 exists

The frozen v1.1 window starts the day after each data week ends, and a forecast must be logged
before its window starts. NCDC's weekly reports are published later than that. So v1.1 can issue
no eligible forecast in its 2026–27 primary window: **0 of 26 weeks**
(`data/lassa/v1-1-eligibility-yield.json`). v1.2 proposes a window that starts several weeks after
the data week (lead L=4 proposed) so that a report published within about three weeks can still be
used.

**Whether v1.2 actually avoids v1.1's failure is not yet demonstrated.** See
[REVIEW_ADDENDUM_2026-10-28.md](REVIEW_ADDENDUM_2026-10-28.md) §2: the proposed lead is checked
against an upload-time proxy, and the first directly observed lags include a week already beyond
16 days.

## Read in this order

1. [REVIEW_ADDENDUM_2026-10-28.md](REVIEW_ADDENDUM_2026-10-28.md): status and evidence since 8 October.
2. [LASSA_V1_2_EXTERNAL_REVIEW_PACKET.md](LASSA_V1_2_EXTERNAL_REVIEW_PACKET.md): the review request and its ten questions.
3. [PROSPECTIVE_PROTOCOL_LASSA_V1_2_DRAFT.md](PROSPECTIVE_PROTOCOL_LASSA_V1_2_DRAFT.md): the draft protocol (timing designs A, B, C in §3).
4. [LASSA_V1_2_DECISION_PACKAGE.md](LASSA_V1_2_DECISION_PACKAGE.md): the unsigned decisions B, C, D.
5. [LASSA_V1_2_FREEZE_READINESS.md](LASSA_V1_2_FREEZE_READINESS.md), [LASSA_V1_2_PRE_FREEZE_REVIEW.md](LASSA_V1_2_PRE_FREEZE_REVIEW.md), [LASSA_V1_2_IMPLEMENTATION_PLAN.md](LASSA_V1_2_IMPLEMENTATION_PLAN.md), [NCDC_REPORTING_LAG_AUDIT_2026-10-08_CORRECTION.md](NCDC_REPORTING_LAG_AUDIT_2026-10-08_CORRECTION.md): supporting evidence, including withdrawn figures kept as history.

These documents are copied unchanged from GaiaLab's research branch at commit `9daa9349`
(2026-10-08); only this README and the addendum are new. They refer to analysis scripts
(`scripts/lassa/v12-*.py`, `scripts/lassa/lib/v12_eligibility.py`) that are not in this
repository. They are available to reviewers on request, and every figure was produced by
committed scripts in a pinned environment in CI.

## How to comment

Open an issue in this repository. Critical reviews are the useful ones. Comments received before
any freeze will be answered publicly, and the decision on each will be recorded.

## What is not claimed

- No prospective forecasting skill, for v1.1 or v1.2.
- No approval by any external reviewer.
- No NCDC publication time: GaiaLab holds only first-observation upper bounds and not-visible
  lower bounds.

*Research use only. Prospective forecasting performance has not been established.*
