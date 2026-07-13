# Nigerian Academic Partner Outreach Email

## Background: Institute of Lassa Fever Research and Control

The **Institute of Lassa Fever Research and Control (ILFRC)** is located at the **Federal Medical Centre (FMC) Owo**, Owo, Ondo State, Nigeria. Ondo State is the second highest-burden state for Lassa fever in Nigeria (1,638 confirmed cases in our dataset). FMC Owo and the nearby **Irrua Specialist Teaching Hospital (ISTH)** in Edo State are the two principal tertiary referral centres for Lassa fever in Nigeria and have been the sites of landmark clinical research including the Okokhere et al. (2018) Lancet Infectious Diseases study on clinical predictors of Lassa fever outcomes.

**Key contacts (verify before sending):**
- Director, Institute of Lassa Fever Research and Control, FMC Owo: director@fmcowo.gov.ng or ilfrc@fmcowo.gov.ng
- General FMC Owo: info@fmcowo.gov.ng
- **Prof. David Asogun** — FMC Owo, Lassa fever clinical research; formerly CMO; most cited LASV researcher at the institution
- **Prof. George Akpede** — ISTH Irrua; longstanding Lassa fever clinical lead; try cmddirector@isth.gov.ng
- If email bounces, contact via West African Health Organisation (WAHO) or through Nigerian colleagues for warm introduction
- The Viral Hemorrhagic Fever Consortium (VHFC) may have current direct contacts for both institutions

---

## Outreach Email — FMC Owo / ILFRC

**To:** director@fmcowo.gov.ng *(or ilfrc@fmcowo.gov.ng — verify current address)*  
**CC:** info@fmcowo.gov.ng  
**Subject:** Collaboration Request — LassaAI Grant Application (NIH Fogarty R21)

---

Dear Director,

My name is Oluwafemi Idiakhoa, and I am the founder of GaiaLab, an AI-powered biological intelligence platform based in Houston, Texas, USA. I am writing to request a research partnership between GaiaLab and the Institute of Lassa Fever Research and Control at FMC Owo on a NIH Fogarty International Center R21 grant application for Lassa fever outbreak prediction and clinical decision support.

**About LassaAI**

We have developed two open-source tools for Lassa fever:

**1. Outbreak Prediction Model**  
An XGBoost machine learning model trained on NCDC Weekly Epidemiological Reports (national weekly series, 2020–2025; 313 weeks, 6,456 confirmed cases). On a strict out-of-time 2024 hold-out (a retrospective test, not a prospective evaluation), the model reached AUROC = 0.880 versus 0.849 for a naive four-week-average baseline — a modest ~0.03 gain, driven chiefly by dry-season timing. We present it as an honest, baseline-benchmarked proof of concept; prospective validation is the real test and has not yet been done. The model generates a weekly national elevated-transmission forecast about four weeks ahead (per-state forecasting is future work). A live dashboard is at https://www.gailabai.com/lassa

**2. Clinical Copilot**  
A Bayesian probability calculator for healthcare workers that estimates the likelihood of Lassa fever in febrile patients based on symptoms, vital signs, and epidemiological exposures. Weights are derived from published Lassa fever clinical literature including studies conducted at ISTH Irrua (Okokhere et al. 2018 Lancet Infect Dis) and FMC Owo. The copilot is freely accessible at https://www.gailabai.com/lassa-copilot

**The Grant Application**

We are preparing a NIH Fogarty International Center R21 application (Exploratory/Developmental Research, up to $275,000 over 2 years) with two aims:

- **Aim 1 (Year 1):** Prospective validation of the outbreak prediction model in partnership with NCDC
- **Aim 2 (Year 2):** Clinical validation of the LassaAI Clinical Copilot in febrile patients presenting to a Nigerian Lassa fever treatment centre

For Aim 2, we are seeking a partner institution with:
- Active Lassa fever clinical services
- Laboratory capacity for RT-PCR confirmation
- Institutional ethics review board
- Willingness to co-author peer-reviewed publications

The Institute of Lassa Fever Research and Control at FMC Owo, and/or ISTH Irrua, are the most appropriate partners in the world for this work, given the volume of Lassa fever cases you manage annually and the clinical research infrastructure you have already built.

**What partnership would involve**

If your institution agrees to serve as the Nigerian partner on this grant:

1. **Letter of support** for the R21 application (required by NIH Fogarty; typically one to two pages confirming institutional commitment and describing the partnership)
2. **Aim 2 study coordination:** A locally-based study coordinator (funded by the grant at approximately $15,000/year) would lead patient enrollment, administer the Clinical Copilot assessment, and coordinate RT-PCR confirmation
3. **Co-authorship** on all peer-reviewed publications arising from Aim 2
4. **Subaward:** Approximately $35,000 in Year 2 to support study operations at your institution
5. **Technology transfer:** Full open-source access to the LassaAI platform, which your institution could deploy and maintain independently

**What I am requesting**

A 30-minute virtual meeting in June or July 2026 to:
1. Demonstrate the LassaAI platform
2. Discuss the feasibility of the Aim 2 study design at your institution
3. Agree in principle on partnership terms before I submit the Letter of Intent to NIH

The R21 application deadline I am targeting is **October 16, 2026** (PAR-23-268 standard cycle; Letter of Intent due September 16, 2026).

Your institution's contributions to the global understanding of Lassa fever — particularly the clinical and epidemiological work published over the past two decades — are the scientific foundation on which LassaAI is built. I would be honoured to work with you to translate that knowledge into tools that can be deployed at the point of care across Nigeria.

Thank you for considering this request. I am happy to provide any additional information.

Warm regards,

**Oluwafemi Idiakhoa**  
Founder, GaiaLab  
Houston, TX, USA  
partnerships@gailabai.com  
https://www.gailabai.com

---

## Outreach Email — Irrua Specialist Teaching Hospital (ISTH)

*(Alternative or additional partner — send separately or CC)*

**To:** cmddirector@isth.gov.ng *(verify current address)*  
**Subject:** Research Partnership Request — LassaAI Clinical Validation Study

---

Dear Prof. Akpede / Dear CMD,

*(Use same body as FMC Owo email above, adjusted to reference ISTH's specific role — ISTH Irrua is referenced by name in our Clinical Copilot as a reporting centre, and is the site of the Okokhere et al. 2018 landmark study)*

Key adjustment for ISTH version:
- Reference that the Clinical Copilot cites ISTH as a reporting centre (NCDC 0800-970000-10)
- Reference the Okokhere et al. 2018 paper specifically: "The feature weights in our Clinical Copilot for chest pain (OR = 4.0), sore throat (OR = 3.5), and hearing loss (OR = 7.1) are derived directly from the clinical predictors identified in the ISTH-based cohort published by Okokhere et al. in the Lancet Infectious Diseases (2018)"
- Note that ISTH manages approximately 100–200 confirmed Lassa fever cases annually, providing the sample size needed for Aim 2

---

## Attachments to Include with Both Emails

1. **One-page LassaAI summary PDF** — print from https://www.gailabai.com/lassa-summary (A4, File → Print → Save as PDF)
2. **Live dashboard screenshot** — gailabai.com/lassa
3. **Clinical Copilot screenshot** — gailabai.com/lassa-copilot (relevant for FMC Owo / ISTH given Aim 2)
4. **GitHub link** — https://github.com/oluwafemidiakhoa/lassaai

---

*Note: Verify current contact details before sending. Both institutions have had leadership changes. Consider also contacting through the West African Health Organisation (WAHO), the Viral Hemorrhagic Fever Consortium (VHFC), or through Nigerian colleagues in your network for a warm introduction. Do not send the same email simultaneously to both FMC Owo and ISTH — send FMC Owo first, wait 2 weeks, then send ISTH if no response.*
