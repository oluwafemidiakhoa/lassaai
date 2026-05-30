# LassaAI

**AI-powered Lassa fever outbreak prediction and clinical decision support for Nigeria.**

Built by Oluwafemi Idiakhoa · Houston, TX  
Open source · MIT License · 2026

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![Data: NCDC](https://img.shields.io/badge/data-NCDC%20Nigeria-orange.svg)](https://ncdc.gov.ng)

---

## What LassaAI Does

Lassa fever kills thousands of Nigerians every year. Current response is reactive —
outbreaks are detected after they have already grown. LassaAI is an open-source
platform that combines:

- **Outbreak prediction** — forecast which Nigerian states are at risk 4–8 weeks
  before an outbreak occurs
- **Clinical decision support** — help healthcare workers in Nigeria assess
  Lassa fever probability at point of care
- **Drug discovery** — track antiviral candidates and their evidence tier

---

## Live Platform

| Feature | URL |
|---------|-----|
| Outbreak forecast board | gailabai.com/boards |
| Clinical copilot | gailabai.com/lassa-copilot |
| Drug discovery pipeline | gailabai.com/boards (Lassa board) |

---

## Outbreak Prediction Model

### Data
- **Source:** NCDC weekly epidemiological reports
- **Weather:** Open-Meteo historical API
- **Coverage:** All 37 Nigerian states plus FCT
- **Period:** 2011–2026
- **Observations:** 27,861 state-week records
- **Total confirmed cases in dataset:** 8,138
- **Total deaths in dataset:** 910

### Method
- **Model:** XGBoost classifier
- **Target:** Will this state report more than 5 confirmed cases in the next 4 weeks?
- **Validation:** Temporal holdout — no random splits (prevents data leakage)

| Split | Period |
|-------|--------|
| Train | 2011–2021 |
| Validate | 2022–2023 |
| Test | 2024–2025 |

### Performance

| Metric | Test set (2024–25) |
|--------|--------------------|
| AUROC | **0.9994** |
| Precision | 0.9100 |
| Recall | 1.0000 |
| F1 Score | 0.9529 |

Baseline (random classifier): AUROC 0.50

**Confusion matrix (test set):**

|  | Predicted negative | Predicted positive |
|--|--------------------|--------------------|
| **Actual negative** | 3,648 (TN) | 18 (FP) |
| **Actual positive** | 0 (FN) | 182 (TP) |

Zero false negatives on the test set — no outbreak weeks were missed.

### Important note on model performance

Test AUROC of 0.9994 reflects the strong seasonal and geographic predictability
of Lassa fever in Nigeria. Edo, Ondo, Bauchi, Taraba, and Ebonyi account for the
majority of cases and peak consistently during the dry season (November through April).

This predictability is clinically useful — it means the model can reliably identify
when and where to pre-position resources — but AUROC alone does not capture
performance on rare high-outbreak weeks where prediction is hardest.

Prospective validation against 2026 NCDC data is ongoing. Results will be published
when sufficient data is available.

### Class balance

Of 27,417 modelling rows, **6.1% are outbreak weeks** (outbreak = 1) and **93.9% are
non-outbreak weeks** (outbreak = 0). This imbalance is expected and ecologically
accurate: Nigeria has 37 states and 52 weeks per year, but Lassa fever outbreaks
are geographically concentrated (5 states account for >90% of cases) and
seasonally concentrated (dry season, November–April). A model that predicts "no
outbreak" every week would achieve 93.9% accuracy but near-zero recall — which is
why AUROC and recall are the primary evaluation metrics.

### Top Predictive Features

| Feature | Importance |
|---------|-----------|
| 8-week rolling case average | 49.6% |
| Cases 1 week prior | 26.1% |
| 4-week rolling case average | 13.6% |
| Cases 2 weeks prior | 2.2% |
| Weeks into dry season | 1.8% |
| Month of year | 1.7% |
| Cases 8 weeks prior | 1.3% |
| High-risk state (Ondo) | 0.6% |
| High-risk state (Edo) | 0.6% |

Epidemiological signals dominate (93%+). Weather and seasonality provide
the remaining signal — consistent with known Lassa ecology.

### Current Forecast
All 37 Nigerian states: **LOW risk** (Week 22, 2026)

This is expected — it is wet season (May through October). Lassa fever
peaks during the dry season (November through April).

Historically highest risk states: **Edo · Ondo · Bauchi · Taraba · Ebonyi**

---

## Clinical Copilot

A symptom-based probability calculator for healthcare workers in Nigeria.

**IMPORTANT: This tool does not diagnose Lassa fever.** It provides probability
estimates to support clinical judgment. All results require laboratory confirmation
by a qualified healthcare professional.

### How it works
A healthcare worker enters:
- Patient symptoms (fever, sore throat, chest pain, mucosal bleeding, etc.)
- Exposure history (contact with cases, rodents, high-risk areas)
- State of residence

The tool returns:
- Lassa fever probability score (0–95%)
- Risk category (LOW / MODERATE / HIGH / VERY HIGH)
- Differential diagnosis
- Recommended clinical actions
- NCDC reporting instructions

### Report suspected cases immediately
**NCDC Emergency Line:** 0800-970000-10  
Available: 24 hours, 7 days, toll-free  
Online: ncdc.gov.ng/report  
Email: info@ncdc.gov.ng

---

## Drug Discovery Pipeline

Antiviral candidates ranked by evidence tier:

| Drug | Tier | Status |
|------|------|--------|
| Ribavirin | I | FDA approved (orphan drug) — current standard of care |
| Favipiravir | I | Investigational — superior in animal models |
| Molnupiravir (MK-4482) | II | Investigational broad-spectrum antiviral |
| Galidesivir | II | Investigational — RNA polymerase inhibitor |

Full evidence pipeline integrated with GaiaLab biological evidence platform.

---

## How to Run Locally

### Requirements
Python 3.9 or higher

### Install dependencies
```bash
git clone https://github.com/oluwafemidiakhoa/lassaai.git
cd lassaai
pip install -r requirements.txt
```

### Collect data
```bash
python scripts/collect-ncdc-data.py
python scripts/collect-weather-data.py
python scripts/merge-datasets.py
```

### Train the model
```bash
python scripts/train-model.py
```

### Generate current forecast
```bash
python scripts/forecast-now.py
```

---

## Repository Structure

```
lassaai/
├── README.md
├── LICENSE
├── requirements.txt
├── scripts/
│   ├── collect-ncdc-data.py
│   ├── collect-weather-data.py
│   ├── build-features.py
│   ├── train-model.py
│   └── forecast-now.py
├── data/
│   └── lassa/
│       ├── ncdc-cases.csv
│       ├── weather-by-state.csv
│       ├── lassa-merged.csv         (27,861 state-week observations)
│       ├── features.csv
│       ├── feature-importance.csv
│       ├── calibration-curve.png
│       └── current-forecast.json
├── models/
│   └── lassa/
│       └── outbreak-model-v1.pkl    (trained XGBoost model)
├── docs/
│   └── lassa/
│       ├── paper-draft.md
│       ├── data-sources.md
│       └── grant-outline.md
└── public/
    └── lassa-copilot.html
```

---

## Data Sources

All data used in this project is publicly available. No patient data is used or stored.

| Source | Description | License |
|--------|-------------|---------|
| NCDC Nigeria | Weekly Lassa fever situation reports | Public domain |
| Open-Meteo | Historical weather data by state capital | CC BY 4.0 |
| ClinicalTrials.gov | Antiviral drug trial records | Public domain |
| WHO | Outbreak reports and clinical guidance | Public domain |

---

## Scientific Context

Lassa fever is endemic to West Africa and causes significant mortality in Nigeria,
with an estimated 300,000 infections and 5,000 deaths annually (WHO estimate).

The multimammate rat (*Mastomys natalensis*) is the primary reservoir. Transmission
to humans occurs through contact with infected rodent urine or droppings, or
person-to-person contact with infected blood or body fluids.

Current antiviral therapy (ribavirin) has limited efficacy and significant toxicity.
No approved vaccine exists. Early prediction and clinical recognition are the most
actionable current interventions.

---

## Citation

If you use LassaAI in your research please cite:

> Idiakhoa, O. (2026). LassaAI: Machine learning prediction of Lassa fever outbreaks
> in Nigerian states using epidemiological surveillance and environmental data.
> GitHub: github.com/oluwafemidiakhoa/lassaai

A peer-reviewed paper is in preparation for submission to PLOS Neglected Tropical Diseases.

---

## Contributing

Contributions are welcome from:
- Nigerian epidemiologists and clinicians
- Public health researchers
- African academic institutions
- WHO and NCDC technical staff
- Open source developers

Please open an issue before submitting a pull request. Clinical suggestions
should include references to published literature.

---

## Roadmap

- [ ] Prospective validation (model predictions vs actual NCDC data)
- [ ] Local government area (LGA) resolution (currently state-level only)
- [ ] Clinical validation study at Irrua Specialist Teaching Hospital
- [ ] NCDC partnership for real-time data feed
- [ ] Mobile-optimised copilot for rural healthcare workers
- [ ] Hausa language support
- [ ] WHO situation report automation

---

## Contact

**Oluwafemi Idiakhoa**  
partnerships@gailabai.com  
gailabai.com  
Houston, TX

For partnership inquiries from NCDC, WHO, or academic institutions
please email partnerships@gailabai.com

---

## License

MIT License — free to use, modify, and distribute with attribution.

See [LICENSE](LICENSE) for full text.

For clinical deployment in Nigerian health facilities please contact
partnerships@gailabai.com for implementation guidance.

---

## Disclaimer

LassaAI outputs are computational research tools requiring expert validation
before clinical or public health application.

The clinical copilot is for decision support only — not for independent
diagnosis of Lassa fever.

Outbreak predictions require confirmation by qualified epidemiologists
before informing public health response.

This platform is not affiliated with NCDC, WHO, or any government health authority.
