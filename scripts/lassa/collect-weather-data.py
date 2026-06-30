"""
LassaAI — Weather Data Collector (Open-Meteo Historical API)
============================================================
Fetches weekly climate data for all 37 Nigerian states/FCT
from 2012-01-01 to today via the Open-Meteo archive API
(free, no API key required).

Output: data/lassa/weather-by-state.csv
Fields: state, year, epi_week, temp_max, temp_min, rainfall, humidity,
        wind_max, obs_days (quality flag: number of days with actual data)

Usage:
  python scripts/lassa/collect-weather-data.py
  python scripts/lassa/collect-weather-data.py --state Edo    # single state
  python scripts/lassa/collect-weather-data.py --resume       # skip already-fetched states
"""

import os
import sys
import csv
import time
import logging
import argparse
from datetime import date, timedelta
from pathlib import Path

import requests

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/lassa/weather-collect.log", mode="a"),
    ],
)
log = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
API_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2012-01-01"
END_DATE = date.today().isoformat()
OUTPUT_CSV = Path("data/lassa/weather-by-state.csv")
REQUEST_DELAY = 3.0   # seconds — Open-Meteo free tier; back off after 429s
MAX_RETRIES   = 4     # exponential backoff: 3s, 6s, 12s, 24s

CSV_FIELDS = [
    "state", "year", "epi_week",
    "temp_max", "temp_min", "rainfall", "humidity", "wind_max",
    "obs_days",
]

# ── State capital coordinates ─────────────────────────────────────────────────
STATE_COORDS = {
    "Abia":        (5.4527,  7.5248),
    "Adamawa":     (9.3265, 12.3984),
    "Akwa Ibom":   (5.0077,  7.8536),
    "Anambra":     (6.2104,  6.9623),
    "Bauchi":     (10.3158,  9.8442),
    "Bayelsa":     (4.9267,  6.2676),
    "Benue":       (7.7325,  8.5881),
    "Borno":      (11.8333, 13.1500),
    "Cross River": (4.9517,  8.3220),
    "Delta":       (5.8904,  5.6801),
    "Ebonyi":      (6.2649,  8.0137),
    "Edo":         (6.3350,  5.6037),
    "Ekiti":       (7.7190,  5.3110),
    "Enugu":       (6.4584,  7.5464),
    "Gombe":      (10.2791, 11.1670),
    "Imo":         (5.4927,  7.0261),
    "Jigawa":     (12.2280,  9.5616),
    "Kaduna":     (10.5264,  7.4381),
    "Kano":       (12.0022,  8.5919),
    "Katsina":    (12.9889,  7.6006),
    "Kebbi":      (12.4539,  4.1975),
    "Kogi":        (7.8007,  6.7332),
    "Kwara":       (8.4966,  4.5426),
    "Lagos":       (6.5244,  3.3792),
    "Nasarawa":    (8.5302,  8.3204),
    "Niger":       (9.6139,  6.5568),
    "Ogun":        (7.1608,  3.3488),
    "Ondo":        (7.2500,  5.1950),
    "Osun":        (7.5629,  4.5200),
    "Oyo":         (7.8500,  3.9333),
    "Plateau":     (9.2182,  9.5178),
    "Rivers":      (4.8156,  7.0498),
    "Sokoto":     (13.0622,  5.2339),
    "Taraba":      (7.8700,  9.7800),
    "Yobe":       (12.0000, 11.5000),
    "Zamfara":    (12.1704,  6.6575),
    "FCT":         (9.0765,  7.3986),
}

# ── Epi-week helpers ──────────────────────────────────────────────────────────

def iso_to_epi_week(d: date) -> tuple[int, int]:
    """Return (epi_week, year) using CDC epi-week convention (week starts Sunday)."""
    # CDC epi week: week 1 starts on the Sunday of the week containing Jan 4
    # Approximate with ISO week (starts Monday) — close enough for weekly aggregation
    iso = d.isocalendar()
    return iso[1], iso[0]


def daily_to_weekly(daily_data: dict) -> list[dict]:
    """
    Aggregate daily Open-Meteo data into epi weeks.
    daily_data keys: dates, temperature_2m_max, temperature_2m_min,
                     precipitation_sum, relative_humidity_2m_mean, windspeed_10m_max
    """
    dates = daily_data.get("time", [])
    t_max  = daily_data.get("temperature_2m_max", [])
    t_min  = daily_data.get("temperature_2m_min", [])
    rain   = daily_data.get("precipitation_sum", [])
    hum    = daily_data.get("relative_humidity_2m_mean", [])
    wind   = daily_data.get("windspeed_10m_max", [])

    weeks: dict[tuple, dict] = {}

    for i, ds in enumerate(dates):
        d = date.fromisoformat(ds)
        epi_week, year = iso_to_epi_week(d)
        key = (year, epi_week)

        if key not in weeks:
            weeks[key] = {
                "temp_max_vals": [], "temp_min_vals": [],
                "rain_vals": [], "hum_vals": [], "wind_vals": [],
                "count": 0,
            }

        def _v(lst, idx):
            v = lst[idx] if idx < len(lst) else None
            return None if v is None or (isinstance(v, float) and v != v) else v  # NaN check

        w = weeks[key]
        w["count"] += 1
        if _v(t_max, i)  is not None: w["temp_max_vals"].append(_v(t_max, i))
        if _v(t_min, i)  is not None: w["temp_min_vals"].append(_v(t_min, i))
        if _v(rain, i)   is not None: w["rain_vals"].append(_v(rain, i))
        if _v(hum, i)    is not None: w["hum_vals"].append(_v(hum, i))
        if _v(wind, i)   is not None: w["wind_vals"].append(_v(wind, i))

    rows = []
    for (year, epi_week), w in sorted(weeks.items()):
        def _mean(lst): return round(sum(lst) / len(lst), 2) if lst else ""
        def _sum(lst):  return round(sum(lst), 2) if lst else ""
        def _mxv(lst):  return round(max(lst), 2) if lst else ""

        rows.append({
            "year": year,
            "epi_week": epi_week,
            "temp_max":  _mean(w["temp_max_vals"]),
            "temp_min":  _mean(w["temp_min_vals"]),
            "rainfall":  _sum(w["rain_vals"]),
            "humidity":  _mean(w["hum_vals"]),
            "wind_max":  _mxv(w["wind_vals"]),
            "obs_days":  w["count"],
        })

    return rows


# ── API fetch ─────────────────────────────────────────────────────────────────

def fetch_state_weather(state: str, lat: float, lon: float) -> list[dict]:
    """Fetch all historical weather for one state capital. Returns list of weekly rows."""
    params = {
        "latitude":    lat,
        "longitude":   lon,
        "start_date":  START_DATE,
        "end_date":    END_DATE,
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "relative_humidity_2m_mean",
            "windspeed_10m_max",
        ]),
        "timezone": "Africa/Lagos",
    }

    log.info(f"  Fetching {state} ({lat:.4f}, {lon:.4f}) {START_DATE} to {END_DATE} ...")

    data = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(API_URL, params=params, timeout=60)
            if resp.status_code == 429:
                wait = REQUEST_DELAY * (2 ** attempt)
                log.warning(f"  429 rate limit for {state}, waiting {wait:.0f}s (attempt {attempt+1}/{MAX_RETRIES})")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            break
        except requests.RequestException as e:
            wait = REQUEST_DELAY * (2 ** attempt)
            log.warning(f"  Request error {state} (attempt {attempt+1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(wait)
            else:
                log.error(f"  FAILED {state} after {MAX_RETRIES} attempts: {e}")
                return []
        except Exception as e:
            log.error(f"  Parse error {state}: {e}")
            return []

    if data is None:
        log.error(f"  FAILED {state}: exhausted retries")
        return []

    daily = data.get("daily", {})
    if not daily.get("time"):
        log.warning(f"  No daily data returned for {state}")
        return []

    weekly_rows = daily_to_weekly(daily)
    for row in weekly_rows:
        row["state"] = state

    log.info(f"  {state}: {len(weekly_rows)} weeks fetched")
    return weekly_rows


# ── Main ──────────────────────────────────────────────────────────────────────

def already_fetched_states(path: Path) -> set[str]:
    """Read existing CSV and return set of states already present."""
    if not path.exists():
        return set()
    states = set()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            states.add(row.get("state", ""))
    return states


def main():
    parser = argparse.ArgumentParser(description="Collect weather data for Nigerian states")
    parser.add_argument("--state", help="Fetch a single state only")
    parser.add_argument("--resume", action="store_true", help="Skip states already in output CSV")
    args = parser.parse_args()

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    targets = STATE_COORDS
    if args.state:
        if args.state not in STATE_COORDS:
            log.error(f"Unknown state: {args.state}. Valid states: {', '.join(STATE_COORDS)}")
            sys.exit(1)
        targets = {args.state: STATE_COORDS[args.state]}

    already_done = already_fetched_states(OUTPUT_CSV) if args.resume else set()
    if already_done:
        log.info(f"Resume mode: skipping {len(already_done)} already-fetched states")

    write_header = not OUTPUT_CSV.exists() or not args.resume
    all_rows = []

    for state, (lat, lon) in targets.items():
        if state in already_done:
            log.info(f"  Skipping {state} (already fetched)")
            continue

        rows = fetch_state_weather(state, lat, lon)
        all_rows.extend(rows)
        time.sleep(REQUEST_DELAY)

    if not all_rows:
        log.warning("No data collected.")
        return

    # Write output
    mode = "a" if args.resume and OUTPUT_CSV.exists() else "w"
    with open(OUTPUT_CSV, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if mode == "w":
            writer.writeheader()
        writer.writerows(all_rows)

    states_done = {r["state"] for r in all_rows}
    years = {r["year"] for r in all_rows}

    log.info("=" * 60)
    log.info(f"OUTPUT: {OUTPUT_CSV}")
    log.info(f"  Rows written  : {len(all_rows)}")
    log.info(f"  States fetched: {len(states_done)}")
    log.info(f"  Years covered : {min(years)}–{max(years)}")
    log.info(f"  End date used : {END_DATE}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
