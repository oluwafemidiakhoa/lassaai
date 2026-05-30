# NIH Specific Aims — LassaAI Prospective Validation Study
**Fogarty International Center — PAR-23-268 (R21)**  
*LOI deadline: September 16, 2026 · Application deadline: October 16, 2026*  
*Format: 1 page · Font: Arial 11pt · Margins: 0.5 in*

---

## Specific Aims

Lassa fever kills an estimated 5,000–10,000 people annually in West Africa, with Nigeria bearing the highest documented burden. Despite weekly epidemiological surveillance by the Nigeria Centre for Disease Control and Prevention (NCDC), no validated early warning system exists. Reactive public health response — deploying ribavirin stockpiles, activating healthcare worker protocols, and alerting state epidemiologists only after confirmed cases accumulate — delays intervention at the most critical window.

We developed **LassaAI**, an XGBoost outbreak prediction model trained on 15 years of NCDC surveillance data (27,417 state-week observations, 37 administrative units). In retrospective temporal validation on a 2024–2025 holdout, LassaAI achieved AUROC = 0.9994 with perfect recall (zero missed outbreaks) and precision = 0.910, predicting outbreak risk 4–8 weeks in advance. The model is deployed as a free, open-source real-time dashboard (https://www.gailabai.com/lassa). All retrospective performance metrics, however, were computed on historical data. **The critical unresolved question is whether LassaAI's predictions — issued before outcomes are known — are accurate enough to guide public health action in prospective use.**

To address this gap, we propose a prospective validation and capacity-building study in partnership with NCDC. Our **central hypothesis** is that LassaAI will achieve AUROC ≥ 0.92 and Brier score ≤ 0.08 across a full prospective epidemiological year (52 prediction weeks including one complete dry season), with performance non-inferior to NCDC reactive surveillance as measured by mean alert lead time.

**Aim 1: Prospectively validate LassaAI's state-level outbreak predictions against NCDC-confirmed case data over 52 consecutive epidemiological weeks (October 2026 – September 2027).**

We will establish a real-time data-sharing protocol with NCDC under a formal data use agreement. Weekly state-level predictions will be locked in a tamper-evident append-only log before NCDC publishes case counts for that week. Primary endpoints are AUROC (discrimination) and Brier score (calibration). Secondary endpoints include alert lead time (weeks between first HIGH prediction and first confirmed case in that state-season) and false-alert burden (HIGH predictions with no subsequent case in the 4-week horizon). *This aim is purely observational and exempt from human subjects review under 45 CFR 46.104(b)(4) (publicly available aggregate surveillance data).*

**Aim 2: Conduct a prospective observational validation of the LassaAI Clinical Copilot at two sentinel healthcare facilities in Edo and Ondo States.**

Healthcare workers at Irrua Specialist Teaching Hospital (ISTH, Edo) and Federal Medical Centre Owo (FMC Owo, Ondo) will use the Copilot for febrile inpatients during the 2026–2027 dry season. We will compare Copilot clinical probability estimates to confirmed Lassa fever diagnoses (RT-PCR). Primary endpoints are AUROC for clinical triage and time-to-empiric-ribavirin-initiation. *This aim involves human subjects (minimal risk, observational) and will undergo IRB review by the ISTH Research Ethics Committee and the GaiaLab's affiliated U.S. institutional IRB.*

**Expected outcomes.** This study will (1) generate the first prospective performance data for an AI-driven Lassa fever early warning system; (2) build local capacity in Nigeria for AI-assisted disease surveillance; and (3) provide the evidence base for NCDC integration of LassaAI as an operational component of the national Lassa fever response. Results will be disseminated through open-access publication, the LassaAI public dashboard, and direct policy engagement with NCDC.

---

*Principal Investigator: Oluwafemi Idiakhoa, GaiaLab, Houston TX · partnerships@gailabai.com*  
*Key Personnel: [Nigerian co-investigator — FMC Owo / ISTH, TBC]*  
*Total budget requested: $275,000 (direct + indirect) over 24 months*
