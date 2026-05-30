# LassaAI — Data Sources

**Project:** LassaAI (within GaiaLab)
**Last updated:** May 2026
**Data coverage:** Nigeria, 2012–present

---

## 1. Epidemiological Data — NCDC Lassa Fever Situation Reports

### Source
Nigeria Centre for Disease Control (NCDC)
- **Sitrep index:** https://ncdc.gov.ng/diseases/sitreps
- **Disease page:** https://ncdc.gov.ng/diseases/info/lassa-haemorrhagic-fever
- **Format:** Weekly PDF and HTML reports (Epi Week 1–52/53 per year)

### What is collected
Each weekly situation report contains:
- Confirmed case counts (national and state-level from ~2016 onward)
- Suspected case counts
- Deaths (case fatality rate computable)
- Healthcare worker infections (from 2016 onward)
- States affected count

### Collection method
`scripts/lassa/collect-ncdc-data.py` scrapes the NCDC sitrep index, downloads each PDF or HTML report, and extracts the above fields using `pdfplumber` (PDFs) or `BeautifulSoup` (HTML). State-level breakdowns are parsed from embedded tables using regex pattern matching against the 37 state names.

### Known gaps
- **2012–2015:** NCDC published national totals only; no publicly available state-level breakdown. State distribution in these years is estimated from post-2016 burden data (see `STATE_CASE_WEIGHTS` in the script).
- **Inconsistent formats:** PDF layouts changed in 2018, 2020, and 2022. The extraction regex covers known patterns but may miss unusual layouts.
- **Missing reports:** NCDC occasionally skips a week during low-transmission periods (June–September). These are logged to `data/lassa/ncdc-skipped.log`.
- **Healthcare worker data:** Available from approximately Epi Week 1 2016 onward.

### Seed/fallback data
When scraping fails, the script falls back to annual totals compiled from:
- NCDC Annual Lassa Fever Reports (2012–2024)
- Ilori et al. 2019 (PMID 31253140) — state-level 2016–2018 data
- WHO Disease Outbreak News (multiple years)
- Okonkwo et al. 2021 — state-level burden estimates

Seed rows are marked `source_type = seed_annual_estimate` in the output CSV. These are distributional estimates, not direct counts, and should be treated accordingly in modelling.

### How to update monthly
```bash
# Pull latest sitreps (scrapes new reports since last run)
python scripts/lassa/collect-ncdc-data.py

# Or seed-only (no network required):
python scripts/lassa/collect-ncdc-data.py --seed-only
```
Run this in the first week of each month to capture the prior month's reports.

### Citation
> Nigeria Centre for Disease Control (NCDC). Lassa Fever Situation Reports.
> https://ncdc.gov.ng/diseases/sitreps. Accessed [date].

---

## 2. Climate Data — Open-Meteo Historical Weather API

### Source
Open-Meteo Archive API (free, no API key required)
- **Base URL:** https://archive-api.open-meteo.com/v1/archive
- **Coverage:** Global, 1940–present, ERA5 reanalysis + station data
- **Spatial resolution:** ~9 km ERA5 grid

### What is collected
For each of Nigeria's 36 states plus FCT (37 locations total), using state capital coordinates:

| Variable | Description |
|---|---|
| `temperature_2m_max` | Daily maximum temperature at 2m (°C) |
| `temperature_2m_min` | Daily minimum temperature at 2m (°C) |
| `precipitation_sum`  | Daily total precipitation (mm) |
| `relative_humidity_2m_mean` | Mean relative humidity at 2m (%) |
| `windspeed_10m_max`  | Maximum daily wind speed at 10m (km/h) |

Daily data is aggregated to **ISO epi weeks** (Monday–Sunday) by computing:
- `temp_max` = mean of daily maxima across the week
- `temp_min` = mean of daily minima across the week
- `rainfall` = sum of daily precipitation across the week
- `humidity` = mean of daily humidity across the week
- `wind_max` = maximum of daily wind maxima across the week
- `obs_days` = number of days with data in the week (quality flag; 7 = complete)

### Known gaps and limitations
- **Point coordinates only:** Each state is represented by its capital city coordinates. Intra-state climate variation (especially in large states like Borno, Niger, Taraba) is not captured.
- **ERA5 reanalysis:** Pre-satellite-era data (pre-1979) and data-sparse regions are modelled estimates, not direct measurements. Post-1979 data is reliable.
- **Timezone:** All data fetched in `Africa/Lagos` (WAT, UTC+1).
- **Leap years / 53-week years:** Some ISO years have 53 weeks. The epi-week aggregation handles this correctly but the merge with NCDC data (which uses CDC epi weeks) may show a 1-week offset near year-end in some years.

### How to update monthly
```bash
# Full fetch (all states, all time — takes ~5 minutes)
python scripts/lassa/collect-weather-data.py

# Single state update
python scripts/lassa/collect-weather-data.py --state Edo

# Resume after interruption
python scripts/lassa/collect-weather-data.py --resume
```

### Citation
> Zippenfenig, P. (2023). Open-Meteo.com Weather API [Computer software].
> Zenodo. https://doi.org/10.5281/zenodo.7970649
>
> Hersbach, H., et al. (2020). The ERA5 global reanalysis. QJRMS 146, 1999–2049.
> https://doi.org/10.1002/qj.3803

---

## 3. Merged Dataset — lassa-merged.csv

### Generated by
`scripts/lassa/merge-datasets.py` — performs a full outer join of `ncdc-cases.csv`
and `weather-by-state.csv` on `(state, year, epi_week)`.

### Quality flags in merged file
| Column | Meaning |
|---|---|
| `has_cases` | 1 = epidemiological data present for this row |
| `has_weather` | 1 = weather data present for this row |
| `source_type` | `pdf_scraped`, `html_scraped`, `seed_annual_estimate`, or `pdf_scraped_national_only` |
| `obs_days` | Number of weather observation days in week (7 = complete) |

### How to regenerate
```bash
python scripts/lassa/merge-datasets.py
```
Prints a coverage report and writes `data/lassa/lassa-merged.csv` and
`data/lassa/merge-report.txt`.

---

## 4. Known Gaps Summary

| Period | Issue | Recommended action |
|---|---|---|
| 2012–2015 | State-level case data not publicly available | Use seed estimates; treat as lower confidence in models |
| Jun–Sep each year | Few or no NCDC sitreps (low season) | Treat missing weeks as zero-case weeks after validation |
| Healthcare workers | Only available from 2016 onward | Exclude from pre-2016 modelling or impute |
| State capitals only | Weather from one point per state | Consider adding rural sentinel sites for Edo, Ondo, Bauchi |
| PDF format changes | Extraction may fail for some years | Review `ncdc-skipped.log` and manually supplement |

---

## 5. Supplementary Sources (not yet integrated)

These sources are publicly available and could improve the dataset:

| Source | Data | URL |
|---|---|---|
| WHO AFRO Lassa bulletins | Regional case counts | https://www.afro.who.int/health-topics/lassa-fever |
| ProMED-mail | Outbreak alerts since 1994 | https://promedmail.org |
| HealthMap | Aggregated outbreak signals | https://healthmap.org |
| GADM Nigeria shapefiles | State boundaries for spatial analysis | https://gadm.org |
| WorldPop Nigeria | Population density 2012–2020 | https://www.worldpop.org |
| Mastomys natalensis range | Rodent reservoir distribution | GBIF, iNaturalist |
| NASA MODIS NDVI | Vegetation index (Mastomys habitat proxy) | https://earthdata.nasa.gov |

---

## 6. Data Use & Ethics

- All data collected here is from publicly available government and research sources.
- NCDC data is public health surveillance data; no individual-level data is collected.
- Weather data is modelled reanalysis (ERA5) — not from private sensors.
- This dataset is intended for epidemiological research and early warning system development.
- **Not for clinical use.** Outputs are research hypotheses requiring expert validation.

---

## 7. File Structure

```
data/lassa/
├── ncdc-cases.csv          # Epi data by state × week (scraped + seed)
├── weather-by-state.csv    # Climate data by state × week
├── lassa-merged.csv        # Merged dataset (primary modelling input)
├── merge-report.txt        # Coverage report (auto-generated)
├── ncdc-collect.log        # NCDC scraping log
├── weather-collect.log     # Weather fetch log
└── ncdc-skipped.log        # Reports that could not be scraped

models/lassa/               # Forecasting models (to be added)
scripts/lassa/
├── collect-ncdc-data.py    # Step 1: NCDC data collection
├── collect-weather-data.py # Step 2: Weather data collection
└── merge-datasets.py       # Step 3: Merge and validate
docs/lassa/
└── data-sources.md         # This file
```
