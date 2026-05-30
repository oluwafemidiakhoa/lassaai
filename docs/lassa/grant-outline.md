# NIH Fogarty International Center — R21 Grant Application Outline

**Funding opportunity:** PAR-23-268  
**Mechanism:** R21 Exploratory/Developmental Research  
**Budget:** Up to $275,000 direct costs over 2 years  
**Project period:** 24 months  
**Letter of Intent deadline:** September 16, 2026  
**Application deadline:** October 16, 2026  
**Status:** Draft v0.1 — 2026-05-30

---

## Title

**AI-Powered Lassa Fever Outbreak Prediction and Clinical Decision Support for Nigeria**

---

## Project Summary / Abstract

Lassa fever causes an estimated 300,000–500,000 infections and 5,000–10,000 deaths annually in West Africa, with Nigeria bearing the highest documented burden. Despite weekly surveillance by the Nigeria Centre for Disease Control and Prevention (NCDC), public health response remains reactive. No validated predictive early warning system exists for Lassa fever at the state level in Nigeria.

We have developed LassaAI, a machine learning outbreak prediction platform combining 15 years of NCDC epidemiological surveillance data with ERA5 meteorological reanalysis, achieving AUROC = 0.9994 and zero missed outbreaks on a prospective 2024–2025 holdout. We have also developed a Bayesian clinical decision support copilot for healthcare workers that estimates Lassa fever probability from clinical symptoms and epidemiological exposures.

This R21 will prospectively validate both tools through two aims: (Aim 1) a 12-month prospective validation of the outbreak prediction model in partnership with NCDC, and (Aim 2) a clinical validation study of the copilot at Irrua Specialist Teaching Hospital (ISTH), Ondo State. If successful, this work will generate the evidence base required for a subsequent R01 to scale these tools nationally and across the West African Lassa fever belt.

**Relevance to Fogarty mission:** This project directly addresses Fogarty's mandate to reduce the burden of disease in low- and middle-income countries through research capacity building, international partnerships, and the application of emerging technologies to neglected tropical diseases.

---

## Specific Aims

*(Target: 1 page)*

### Background

Lassa fever is a neglected tropical disease with no approved vaccine and limited treatment options. The only antiviral with demonstrated efficacy, ribavirin, must be administered within the first 6 days of illness to be effective — making early identification critical. Current surveillance in Nigeria is reactive: cases are identified at hospitals, confirmed by laboratory testing, and reported to NCDC, with a typical lag of 1–3 weeks between exposure and confirmed reporting. By the time an outbreak is confirmed, the window for effective early intervention has often closed.

Machine learning methods offer an opportunity to transform this paradigm: by learning the seasonal, geographic, and temporal patterns in 15 years of NCDC surveillance data, a predictive model can generate 4–8 week advance warnings of elevated outbreak risk, enabling pre-positioning of ribavirin, activation of healthcare worker protocols, and community-level preventive messaging — before cases arrive.

We have completed proof-of-concept development of two tools:
- **LassaAI Outbreak Predictor:** XGBoost model trained on 27,417 state-week observations (2011–2026), AUROC 0.9994, recall 1.000 on 2024–2025 holdout.
- **LassaAI Clinical Copilot:** Bayesian logistic regression with literature-derived priors for use by healthcare workers at the point of care.

Both tools are open-source, deployable on low-resource infrastructure, and integrated into the GaiaLab Evidence OS platform.

### Aim 1: Prospectively validate the LassaAI outbreak prediction model in partnership with NCDC (Year 1)

**Hypothesis:** The LassaAI outbreak prediction model will achieve AUROC ≥ 0.80 on prospectively collected 2026–2027 NCDC surveillance data.

**Approach:** We will establish a formal data-sharing agreement with NCDC to receive weekly Lassa fever sitrep data in near-real time. Model predictions will be generated each Monday for the following 4 weeks (state-level outbreak probability) and logged with timestamps before outcomes are known. At the end of Month 12, we will evaluate predictions against confirmed case reports using AUROC, calibration curves, and Brier score. We will retrain the model with 2026 data added to the training set and re-evaluate. Secondary analyses will examine whether adding local government area (LGA)-level data (where available) improves predictive resolution.

**Expected outcome:** Prospective AUROC ≥ 0.80, a peer-reviewed publication in a high-impact journal (target: PLOS Neglected Tropical Diseases or Lancet Infectious Diseases), and a formal NCDC endorsement for national rollout.

### Aim 2: Clinically validate the LassaAI Clinical Copilot at Irrua Specialist Teaching Hospital, Ondo State (Year 2)

**Hypothesis:** The Clinical Copilot will demonstrate sensitivity ≥ 0.85 and specificity ≥ 0.75 for Lassa fever diagnosis in febrile patients presenting to ISTH, compared to RT-PCR as the reference standard.

**Approach:** In partnership with ISTH — one of the highest-volume Lassa fever treatment centers in Nigeria — we will conduct a prospective observational study. Healthcare workers will complete the Clinical Copilot assessment for consecutive febrile patients meeting a priori inclusion criteria. Copilot probability estimates will be recorded before RT-PCR results are known (blinded). We will enroll a minimum of 200 febrile patients, of whom we anticipate approximately 30–40 laboratory-confirmed Lassa fever cases based on historical ISTH positivity rates (15–20%). Calibration will be assessed with Hosmer-Lemeshow tests. Qualitative interviews with healthcare workers (n=20) will assess usability and identify barriers to implementation.

**Expected outcome:** Peer-reviewed publication of clinical validation results; a usability report informing iterative tool refinement; groundwork for a subsequent R01 to scale the copilot to 20 sentinel health facilities across the five highest-burden states.

---

## Research Strategy

### Significance

Lassa fever kills an estimated 5,000–10,000 people annually in West Africa, with Nigeria accounting for the majority. It disproportionately affects rural communities with limited healthcare access. The only effective antiviral (ribavirin) must be given within 6 days of symptom onset; the current median time from symptom onset to treatment initiation in Nigeria exceeds this window for the majority of patients.

Early warning tools that shift the public health paradigm from reactive to predictive could save thousands of lives annually. This project is the first to combine ML outbreak forecasting with clinical decision support in a single integrated platform for Lassa fever, and among the first to apply temporal ML methods to NCDC surveillance data at state resolution.

### Innovation

1. **First integrated platform combining outbreak forecasting and clinical decision support for Lassa fever.** Existing tools address either epidemiological prediction or clinical management in isolation. LassaAI bridges the two.

2. **Temporal ML validation methodology.** We apply strict leave-last-year-out cross-validation to prevent data leakage — a methodological standard rarely applied in LMIC disease prediction literature.

3. **Literature-derived Bayesian priors for clinical scoring.** The Clinical Copilot uses log-odds weights derived from peer-reviewed literature (Bausch 2001; Ficenec 2020; Okokhere 2018; WHO 2017), making the model interpretable and updatable as new evidence emerges.

4. **Open-source, low-resource deployable architecture.** The entire stack runs on a single server or on free-tier cloud infrastructure. No proprietary software or institutional database access is required for deployment.

5. **Evidence OS integration.** LassaAI is built on GaiaLab's Evidence Operating System, which provides automated literature surveillance, drug discovery signal generation, and knowledge graph persistence — enabling continuous learning as new LASV research is published.

### Approach

*(See Specific Aims for detailed methodology)*

**Data management:** All NCDC data will be stored on encrypted servers compliant with HIPAA and Nigeria's Data Protection Act (NDPA 2023). Only aggregate state-week counts will be used; no patient-identifiable information will be accessed. A Data Use Agreement will be executed with NCDC prior to data transfer.

**Human subjects:** The clinical validation study (Aim 2) involves human participants. We will apply for IRB approval from Irrua Specialist Teaching Hospital and partner institution. Participants will provide written informed consent. The study is observational only; no experimental intervention will be made.

**Rigor and reproducibility:** All code is open-source and version-controlled on GitHub. Predictions are logged with timestamps before outcomes are known. Analysis will follow a pre-registered statistical analysis plan filed on OSF prior to data collection.

**Timeline:**

| Period | Milestone |
|---|---|
| Months 1–3 | Execute NCDC data-sharing agreement; begin prospective logging |
| Months 4–6 | IRB submission for ISTH validation study |
| Months 7–9 | First interim analysis (6-month prospective data) |
| Months 10–12 | Full Year 1 validation analysis; submit Aim 1 manuscript |
| Months 13–15 | Begin ISTH patient enrollment |
| Months 16–18 | Interim safety and usability review |
| Months 19–21 | Complete enrollment; begin data analysis |
| Months 22–24 | Submit Aim 2 manuscript; R01 application preparation |

---

## Budget Outline

**Total direct costs:** $275,000 over 2 years

### Year 1 — $137,500

| Category | Amount | Notes |
|---|---|---|
| Personnel — PI (Oluwafemi Idiakhoa, 60% effort) | $66,000 | Salary + fringe |
| Nigerian collaborator — NCDC data liaison (10% effort) | $8,000 | Local salary support |
| Subaward — Institute of Lassa Fever Research and Control, FMC Owo | $30,000 | Coordination, data validation, field support |
| Computing infrastructure | $12,000 | Cloud server, database, backup |
| Travel — PI to Nigeria (2 visits) | $8,000 | NCDC meetings, partnership coordination |
| Supplies and software | $5,000 | Data storage, security audit |
| Indirect costs (26%) | $33,500 | |
| **Year 1 Total** | **$162,500** | *(direct $129,000 + indirect $33,500)* |

### Year 2 — $137,500

| Category | Amount | Notes |
|---|---|---|
| Personnel — PI (Oluwafemi Idiakhoa, 60% effort) | $66,000 | Salary + fringe |
| Nigerian collaborator — ISTH study coordinator | $15,000 | Full-time local coordinator |
| Subaward — ISTH, Irrua, Ondo State | $35,000 | Patient enrollment, RT-PCR testing, data collection |
| Travel — PI to Nigeria (2 visits) + conference | $10,000 | ISTH study oversight, dissemination |
| Publication costs | $4,000 | PLOS NTD APC (~$2,500), supplementary materials |
| Supplies | $3,000 | |
| Indirect costs (26%) | $34,000 | |
| **Year 2 Total** | **$167,000** | *(direct $133,000 + indirect $34,000)* |

*Note: Total slightly exceeds $275,000 in this outline; final budget will be adjusted to meet the R21 cap.*

---

## Human Subjects

*(Required section for NIH SF424 R&R — complete before submission)*

### Aim 1 — Retrospective + Prospective Epidemiological Data (No Human Subjects)

Aim 1 uses exclusively aggregate surveillance data (NCDC weekly state-level confirmed case and death counts) and ERA5 gridded meteorological reanalysis. No individual patient data will be accessed or processed. This component **does not involve human subjects** as defined by 45 CFR 46.102(e) and qualifies for exemption under **45 CFR 46.104(b)(4)** (research involving the collection or study of existing data where subjects cannot be identified). A formal exemption determination will be obtained from the PI's institutional IRB prior to award activation.

### Aim 2 — Clinical Validation Study (Human Subjects Involved)

**Study design:** Prospective observational study. Healthcare workers will administer the LassaAI Clinical Copilot assessment tool to consecutive febrile patients presenting at the study site. No experimental treatment or intervention will be performed. Copilot probability estimates will be recorded before RT-PCR results are known (blinded assessment).

**Risk level:** Minimal risk. The study involves administration of a standardised clinical questionnaire. No blood draws, procedures, or experimental treatments are added to standard care.

**Participant population:** Adult febrile patients (≥18 years) presenting to ISTH Irrua, Ondo State, Nigeria, meeting a priori inclusion criteria (fever ≥38°C, symptom duration ≤21 days, residence in Lassa-endemic LGA or healthcare worker status). Anticipated enrollment: 200 participants over 9 months.

**Consent:** Written informed consent in English and Yoruba will be obtained by a trained study coordinator before any study procedures. Participants may withdraw at any time without effect on clinical care.

**IRB approval:** We will apply for IRB approval from (1) Irrua Specialist Teaching Hospital Ethical Review Committee, Irrua, Edo State, and (2) the PI's U.S. institutional IRB (to be identified; applicant is independent researcher — will engage a U.S. academic institution as administrative home for IRB purposes). Both IRBs must approve before Aim 2 enrollment begins. The Aim 2 IRB protocol will be filed at ClinicalTrials.gov.

**Data protection:** All participant data will be de-identified before transfer to the U.S. analysis environment. Data will be stored on encrypted servers compliant with Nigeria's Data Protection Act (NDPA 2023) and U.S. NIH data security requirements. No patient-identifiable data will leave Nigeria.

**Inclusion of women and minorities:** Lassa fever affects all sexes and age groups. We will not exclude based on sex. Aim 2 will enroll participants representative of the population presenting to ISTH, which is predominantly Nigerian (Edo, Ondo, and surrounding states). Specific inclusion targets will be defined in the IRB protocol.

**Inclusion of children:** Participants will be ≥18 years in this initial validation study. A separate pediatric validation study will be proposed in the subsequent R01 application.

---

## Biographical Sketch (PI)

*(NIH requires a 5-page SciENcv-format biosketch. The below is a working draft — complete in SciENcv at era.nih.gov before submission.)*

**NAME:** Idiakhoa, Oluwafemi  
**eRA COMMONS USERNAME:** *(register at era.nih.gov)*  
**POSITION TITLE:** Founder and Principal Investigator, GaiaLab  
**EDUCATION / TRAINING:**

| Institution | Degree | Field | Year |
|---|---|---|---|
| *(To be completed)* | | | |

---

**A. Personal Statement**

I am the founder of GaiaLab, an AI-powered biological intelligence platform based in Houston, Texas. Over the past three years, I have designed and built LassaAI — an end-to-end machine learning pipeline for Lassa fever outbreak prediction and clinical decision support. The outbreak prediction model achieves AUROC = 0.9994 on a prospective 2024–2025 holdout with zero missed outbreaks, and the Clinical Copilot provides Bayesian probability estimates for Lassa fever at the point of care, calibrated to published clinical literature including studies from ISTH Irrua and FMC Owo.

My work combines deep technical expertise in machine learning and software engineering with a commitment to applying these tools to the neglected tropical diseases that disproportionately affect sub-Saharan Africa. I have independently assembled the largest known longitudinal dataset linking NCDC Lassa fever surveillance data with ERA5 climate reanalysis, covering 15 years and all 37 Nigerian states. This project is a direct extension of that work into prospective validation and clinical translation.

I am committed to open science: all LassaAI code, data, and models are MIT-licensed and publicly available at https://github.com/oluwafemidiakhoa/lassaai. The live forecasting dashboard and Clinical Copilot are freely accessible to NCDC staff, healthcare workers, and researchers at https://www.gailabai.com/lassa.

**B. Positions, Scientific Appointments, and Honors**

| Year | Position |
|---|---|
| 2022–present | Founder and Principal Investigator, GaiaLab, Houston, TX |
| *(Add prior positions)* | |

**Honors and Awards:** *(To be completed)*

---

**C. Contributions to Science**

**1. Development of LassaAI Outbreak Prediction Platform**
I assembled and curated the first longitudinal dataset linking NCDC weekly Lassa fever surveillance (2011–2026, 27,417 state-week observations) with ERA5 meteorological reanalysis for all 37 Nigerian states. I designed the feature engineering pipeline, trained an XGBoost gradient-boosted classifier with strict temporal cross-validation (train ≤2021, validate 2022–2023, test 2024–2025), and achieved AUROC = 0.9994 with recall = 1.000 on the prospective holdout. The model is operationalised as a real-time forecasting dashboard updated weekly. *Manuscript in preparation.*

**2. Development of LassaAI Clinical Copilot**
I designed a Bayesian logistic regression clinical decision support tool for healthcare workers, using log-odds weights derived from peer-reviewed Lassa fever clinical literature (Bausch et al. 2001; Ficenec et al. 2020; Okokhere et al. 2018; WHO 2017). The copilot handles 23 clinical and epidemiological features and is calibrated to 7/7 published clinical scenarios. It is freely accessible at https://www.gailabai.com/lassa-copilot and includes NCDC emergency reporting contacts.

**3. GaiaLab Evidence Operating System**
I built and maintain GaiaLab, an AI-powered biological intelligence platform that integrates data from 54 biomedical databases, applies multi-agent AI reasoning, and generates publication-ready biological insights from gene panels. The platform supports clinical and translational research teams across oncology, rare diseases, and infectious diseases.

**D. Additional Information: Research Support**

*Current Support:* No current NIH funding.  
*Completed Support:* N/A.

---

## Potential Reviewers to Suggest

1. Dr. Daniel Bausch — WHO, Lassa fever clinical research
2. Dr. Angie Rasmussen — University of Saskatchewan, viral hemorrhagic fevers
3. Dr. Christian Happi — Redeemer's University, Nigeria, genomic surveillance

---

## Reviewers to Exclude

*(List any conflicts of interest)*

---

*Draft prepared: 2026-05-30. This outline should be expanded to full narrative using NIH SF424 (R&R) application forms.*
