# LassaAI

**An open, honestly-benchmarked national early-warning model and clinical decision-support aid for Lassa fever in Nigeria.**

Built by Oluwafemi Idiakhoa · Houston, TX
Open source · MIT License · 2026

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![Data: NCDC + SORMAS](https://img.shields.io/badge/data-NCDC%20%2B%20SORMAS-orange.svg)](https://ncdc.gov.ng)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21122486.svg)](https://doi.org/10.5281/zenodo.21122486)

---

## What LassaAI is (and what it isn't)

Lassa fever is endemic in Nigeria and the national response is largely reactive. LassaAI is an **open, reproducible pipeline** that asks a modest, honest question: can we anticipate weeks of *elevated* national transmission a month ahead — and does a model actually beat a trivial baseline?

**It is:** a national weekly early-warning proof of concept on **real, cross-validated NCDC data**, benchmarked against naive baselines, plus a point-of-care clinical-probability aid and an antiviral-evidence tracker.

**It is not:** a validated clinical or operational forecasting system. The model beats a naive persistence baseline only slightly; genuine skill can only be shown prospectively. We make **no claim of exceptional accuracy.**

> **Preprint (open access):** [doi.org/10.5281/zenodo.21122486](https://doi.org/10.5281/zenodo.21122486). Manuscript source: `docs/lassa/paper-draft.md`.

---

## Live platform

| Feature | URL |
|---|---|
| Outbreak dashboard | https://www.gailabai.com/lassa |
| Clinical copilot | https://www.gailabai.com/lassa-copilot |
| One-page summary | https://www.gailabai.com/lassa-summary |

---

## National early-warning model

### Data (real, triple-cross-validated)
- **National weekly incidence, 2020–2025** — NCDC Weekly Epidemiological Reports, via a provenance-tracked public compilation *and* our own independent re-extraction (`scripts/lassa/rebuild-ncdc-real.py`). The two extractions and NCDC's published annual totals agree within **~1%** (e.g. 2020: 1,190 vs 1,189; 2024: 1,311 vs 1,309).
- **Annual confirmed cases:** 2020 = 1,190 · 2021 = 511 · 2022 = 1,042 · 2023 = 1,271 · 2024 = 1,311 · 2025 = 1,131 (total 6,456).
- **Individual-level cross-check (2018–2021):** the de-identified SORMAS dataset (20,062 records, CC-BY-4.0) — its February peak and Edo/Ondo/Ebonyi/Bauchi ranking independently corroborate the national series.
- Seasonality is correct: incidence peaks in the **dry season (Nov–Apr)**, troughs May–Sep.

### Method
- **Target:** will the next 4 weeks carry an *above-median* confirmed-case burden (an "elevated-transmission week")? Chosen because national weekly incidence is never zero, so a ">0/>5" target is trivially always-true. Balanced target: 56% positive.
- **Model:** XGBoost, 9 features (lagged/rolling confirmed counts, trend, epi-week, dry-season flag). No weather (national-average weather is not epidemiologically meaningful).
- **Split:** strictly temporal — train ≤2023, test 2024, 2025 reserved.
- **Benchmarked against naive persistence baselines** (recent 4-week average; previous-week count).

### Performance — read the model *and* the baseline together

| Model | AUROC (2024 hold-out) | Precision | Recall |
|---|---|---|---|
| **XGBoost (9 features)** | **0.880** | 0.93 | 0.78 |
| Naive: recent 4-week average | 0.849 | — | — |
| Naive: previous-week count | 0.848 | — | — |

The model beats the best naive baseline by only **~0.03 AUROC**. Most of the discrimination is **seasonality and recent incidence** — which the baselines also capture. The top predictor is the **dry-season flag (≈53% gain importance)**, i.e. the model is learning the real Nov–Apr season, not a data artefact. This is a modest, believable result, **not a breakthrough.**

### Honest limitations
- Modest gain over a naive baseline; retrospective metrics overstate operational value.
- **National, not per-state.** Per-state weekly counts are published by NCDC as image tables (not text-extractable); the per-state view on the dashboard is an **illustrative prototype**, not validated. Per-state weekly forecasting is future work (SORMAS gives a 2018–2021 per-state view).
- Confirmed counts under-report true incidence.
- **No prospective validation yet** — the genuine test. Append-only forecast logging (`data/lassa/prospective-log.jsonl`) is in place to support it.

---

## Clinical Copilot

A symptom-based probability aid for healthcare workers. **It does not diagnose Lassa fever** and is **not independently validated** — it provides probability estimates to support clinical judgment; all results require RT-PCR confirmation. Symptom weights are literature-derived (McCormick 1987; Okokhere 2018; WHO 2017) and consistent with the SORMAS clinical fields (fever, sore throat, facial/neck oedema).

**Report suspected cases:** NCDC Emergency Line **0800-970000-10** (24/7, toll-free) · ncdc.gov.ng/report

---

## Antiviral evidence tracker

| Drug | Tier | Status |
|---|---|---|
| Ribavirin | I | FDA-approved (orphan) — current standard of care |
| Favipiravir | I | Investigational — superior in animal models |
| Molnupiravir (MK-4482) | II | Investigational broad-spectrum antiviral |

Computational evidence tiers only — not clinical efficacy.

---

## Reproduce it

```bash
git clone https://github.com/oluwafemidiakhoa/lassaai.git
cd lassaai
pip install -r requirements.txt

# 1) Real NCDC national weekly data (re-extract from sitreps, or use the committed CSV)
python scripts/lassa/rebuild-ncdc-real.py          # -> data/lassa/ncdc-real.csv

# 2) Train the national model + print honest metrics vs naive baselines
python scripts/lassa/build-real-national.py

# 3) Regenerate the figures
python scripts/lassa/generate-figures-real.py
```

The validated national series used for the paper is `data/lassa/lassa_fever_timeseries_full.csv` (NCDC WER compilation, 2020–2025).

> **Note on a retracted synthetic version.** An earlier iteration used a **synthetic** per-state series (annual national totals distributed across weeks/states by a fixed formula, with *inverted* seasonality) and reported a misleading near-perfect AUROC. Those data files and the scripts that generated them (`collect-ncdc-data.py`, `build-features.py`, `train-model.py`, `merge-datasets.py`, and the synthetic `lassa-merged.csv` / `features.csv` / `ncdc-cases.csv`) have been **removed** from the repository. They remain in the git history for full transparency about the correction. Do not resurrect them — use the real pipeline above.

---

## Data sources

All data are public, aggregate or de-identified. No identifiable patient data are used.

| Source | Description | License |
|---|---|---|
| NCDC Nigeria | Weekly Lassa fever situation reports (primary) | Public |
| NCDC WER compilation (Kaggle) | Provenance-tracked weekly series 2020–2025 | Public |
| SORMAS (Zenodo 10.5281/zenodo.7309567) | Individual-level Lassa data 2018–2021 | CC-BY-4.0 |
| ClinicalTrials.gov / WHO | Antiviral trials, clinical guidance | Public |

---

## Citation

> Idiakhoa, O. (2026). *Forecasting Elevated Lassa Fever Transmission Weeks in Nigeria from National Surveillance Data: A Baseline-Benchmarked Proof of Concept.* Zenodo. https://doi.org/10.5281/zenodo.21122486

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21122486.svg)](https://doi.org/10.5281/zenodo.21122486)

---

## Contact

**Oluwafemi Idiakhoa** · partnerships@gailabai.com · gailabai.com · Houston, TX

Partnership inquiries from NCDC, WHO, or academic institutions welcome.

---

## License

MIT — see [LICENSE](LICENSE).
