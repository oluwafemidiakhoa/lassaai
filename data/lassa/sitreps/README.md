# LassaAI — NCDC Sitrep Data Directory

This directory stores weekly NCDC Lassa fever situation report data in CSV format,
used by `scripts/lassa/outcome-recorder.py` to record ground-truth outcomes against
prospective forecasts.

## File naming convention

```
YYYY-WNN.csv
```

Examples: `2026-W23.csv`, `2026-W24.csv`, `2027-W01.csv`

Use ISO 8601 week numbering (same as Python `date.isocalendar()`).

## CSV format

One row per Nigerian state (37 rows expected). Required columns:

| Column | Type | Description |
|---|---|---|
| `state` | string | State name exactly as in `data/lassa/lassa-merged.csv` (e.g. `Edo`, `Ondo`, `FCT`) |
| `confirmed_cases` | integer | Lab-confirmed Lassa fever cases reported that week |
| `deaths` | integer | Deaths reported that week |

Example `2026-W23.csv`:
```csv
state,confirmed_cases,deaths
Abia,0,0
Adamawa,0,0
Akwa Ibom,0,0
Anambra,0,0
Bauchi,1,0
Bayelsa,0,0
Benue,0,0
Borno,0,0
Cross River,0,0
Delta,0,0
Ebonyi,0,0
Edo,2,1
Ekiti,0,0
Enugu,0,0
FCT,0,0
Gombe,0,0
Imo,0,0
Jigawa,0,0
Kaduna,0,0
Kano,0,0
Katsina,0,0
Kebbi,0,0
Kogi,0,0
Kwara,0,0
Lagos,0,0
Nasarawa,1,0
Niger,0,0
Ogun,0,0
Ondo,1,0
Osun,0,0
Oyo,0,0
Plateau,0,0
Rivers,0,0
Sokoto,0,0
Taraba,0,0
Yobe,0,0
Zamfara,0,0
```

## Data source

Extract from NCDC Weekly Lassa Fever Situation Reports:
https://ncdc.gov.ng/diseases/sitreps

Each sitrep is published as a PDF. Extract state-level confirmed case and death
counts from the tabular summary on pages 2–3 of each report.

## Workflow

```bash
# 1. Monday morning — log forecast BEFORE sitrep is published
python scripts/lassa/forecast-logger.py

# 2. When NCDC publishes the sitrep (~Wednesday) — create the CSV from the PDF
# e.g. data/lassa/sitreps/2026-W22.csv

# 3. Record outcomes against the Week 22 forecast
python scripts/lassa/outcome-recorder.py \
  --week 2026-W22 \
  --sitrep data/lassa/sitreps/2026-W22.csv \
  --notes "NCDC sitrep published 2026-06-03"
```

## State name mapping

Use these exact state names (matching `lassa-merged.csv`):

Abia, Adamawa, Akwa Ibom, Anambra, Bauchi, Bayelsa, Benue, Borno,
Cross River, Delta, Ebonyi, Edo, Ekiti, Enugu, FCT, Gombe, Imo,
Jigawa, Kaduna, Kano, Katsina, Kebbi, Kogi, Kwara, Lagos, Nasarawa,
Niger, Ogun, Ondo, Osun, Oyo, Plateau, Rivers, Sokoto, Taraba,
Yobe, Zamfara
