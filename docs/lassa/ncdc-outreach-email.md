# NCDC Director General Outreach Email

**To:** director@ncdc.gov.ng  
**CC:** info@ncdc.gov.ng  
**Subject:** Partnership Request — AI-Powered Lassa Fever Outbreak Prediction System (LassaAI)

---

Dear Dr. Idris,

My name is Oluwafemi Idiakhoa, and I am the founder of GaiaLab, an AI-powered biological intelligence platform based in Houston, Texas. I am writing to request a brief meeting to discuss a potential research partnership between LassaAI and the NCDC around Lassa fever outbreak prediction.

**What we have built**

Over the past year, we have developed LassaAI — an open-source machine learning system that anticipates weeks of elevated **national** Lassa fever transmission in Nigeria about four weeks ahead. The model was trained on NCDC Weekly Epidemiological Reports (national weekly series, 2020–2025; 313 weeks, 6,456 confirmed cases cross-validated against NCDC annual totals).

On a strict out-of-time 2024 hold-out (a retrospective test, **not** a prospective evaluation), the model reached AUROC = 0.880 (precision 0.93, recall 0.78) for a non-degenerate target (56% of weeks positive). A naive four-week-average baseline reached AUROC = 0.849 — so the model's *added* skill over a trivial baseline is only ~0.03, with dry-season timing as the dominant signal. We want to be candid: this is a modest, honestly benchmarked proof of concept, not a claim of exceptional accuracy. The genuine test is prospective — predictions locked before outcomes are known — which we have not yet done.

We have also developed a Clinical Copilot — a Bayesian probability calculator for healthcare workers at the point of care, which estimates the likelihood of Lassa fever in a febrile patient based on clinical symptoms and epidemiological exposures. Both tools are freely available, open-source, and designed to operate in low-resource settings without proprietary software.

A live demonstration is available at: https://www.gailabai.com/lassa  
All code, training data, and model weights are publicly available at: https://github.com/oluwafemidiakhoa/lassaai

**Why we are reaching out to NCDC**

The model currently uses NCDC situation report data that we have manually compiled from your publicly available publications. To move from retrospective validation to prospective early warning, we need two things that only NCDC can provide:

1. **Near-real-time data access:** A structured data feed or weekly data sharing arrangement to receive confirmed case counts by state as soon as sitreps are published, enabling the model to generate predictions before each dry season begins.

2. **Prospective validation partnership:** A formal acknowledgment from NCDC that model predictions are being compared against ground-truth case data as part of a scientific validation study. This is required for publication in peer-reviewed journals and for NIH grant applications.

In exchange, NCDC would receive weekly automated outbreak risk forecasts for all 37 states, full access to the open-source codebase, co-authorship on all peer-reviewed publications arising from the validation study, and a deployable version of the platform that NCDC could operate independently.

**What we are requesting**

A 30-minute virtual meeting at your convenience to:
1. Demonstrate the LassaAI platform
2. Discuss the terms of a data-sharing agreement
3. Explore whether NCDC would be willing to serve as a partner institution on a NIH Fogarty International Center R21 grant application (up to $275,000 over 2 years) targeting prospective model validation

I am available any time in June or July 2026 and can accommodate Nigerian time (WAT, UTC+1). I would be grateful for the opportunity to show you what the system can do.

Thank you for your leadership in strengthening Nigeria's disease surveillance infrastructure. The work of NCDC — particularly the weekly Lassa fever situation reports — made this research possible.

Warm regards,

**Oluwafemi Idiakhoa**  
Founder, GaiaLab  
Houston, TX, USA  
partnerships@gailabai.com  
https://www.gailabai.com  
LassaAI: https://www.gailabai.com/lassa

---

---

## Verified Contact Notes (checked May 30, 2026)

- **Dr. Jide Idris** is the current NCDC Director-General as of 2026. Verify at ncdc.gov.ng before sending.
- Primary email: director@ncdc.gov.ng — also try dg@ncdc.gov.ng if no reply within 10 days.
- CC: info@ncdc.gov.ng (general inbox, copied on all official correspondence).
- Consider also contacting through WHO Nigeria Country Office (who.int/nigeria) for a warm introduction if no response within 3 weeks.

## Attachments to Include

1. **One-page LassaAI summary PDF** — print from https://www.gailabai.com/lassa-summary (File → Print → Save as PDF, A4 paper)
2. **Screenshot of forecast dashboard** — gailabai.com/lassa showing the 37-state map/table
3. **GitHub repository link** — https://github.com/oluwafemidiakhoa/lassaai
4. **Clinical Copilot link** — https://www.gailabai.com/lassa-copilot
