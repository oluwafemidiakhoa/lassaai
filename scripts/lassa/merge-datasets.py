"""
LassaAI — Dataset Merger & Validator
=====================================
Merges ncdc-cases.csv with weather-by-state.csv on (state, year, epi_week).
Reports coverage, missing weeks, and basic statistics.

Output: data/lassa/lassa-merged.csv

Usage:
  python scripts/lassa/merge-datasets.py
  python scripts/lassa/merge-datasets.py --report-only   # print report without writing output
"""

import csv
import sys
import logging
import argparse
from pathlib import Path
from collections import defaultdict

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
CASES_CSV   = Path("data/lassa/ncdc-cases.csv")
WEATHER_CSV = Path("data/lassa/weather-by-state.csv")
MERGED_CSV  = Path("data/lassa/lassa-merged.csv")
REPORT_TXT  = Path("data/lassa/merge-report.txt")

MERGED_FIELDS = [
    "state", "year", "epi_week",
    # cases
    "confirmed_cases", "suspected_cases", "deaths", "healthcare_worker_cases",
    "source_type", "source_url",
    # weather
    "temp_max", "temp_min", "rainfall", "humidity", "wind_max", "obs_days",
    # merge quality
    "has_weather", "has_cases", "notes",
]

# Expected epi weeks per year
EXPECTED_WEEKS = 52  # 53 in some years; use 52 as minimum expected


def load_cases(path: Path) -> dict:
    """Load cases CSV into dict keyed by (state, year, epi_week)."""
    data = {}
    if not path.exists():
        log.error(f"Cases file not found: {path}")
        return data
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                key = (row["state"], int(row["year"]), int(row["epi_week"]))
                data[key] = row
            except (KeyError, ValueError):
                continue
    log.info(f"Loaded {len(data)} case rows from {path}")
    return data


def load_weather(path: Path) -> dict:
    """Load weather CSV into dict keyed by (state, year, epi_week)."""
    data = {}
    if not path.exists():
        log.warning(f"Weather file not found: {path} — merging without weather data")
        return data
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                key = (row["state"], int(row["year"]), int(row["epi_week"]))
                data[key] = row
            except (KeyError, ValueError):
                continue
    log.info(f"Loaded {len(data)} weather rows from {path}")
    return data


def merge(cases: dict, weather: dict) -> list[dict]:
    """Full outer join on (state, year, epi_week)."""
    all_keys = set(cases.keys()) | set(weather.keys())
    rows = []

    for key in sorted(all_keys):
        state, year, epi_week = key
        c = cases.get(key, {})
        w = weather.get(key, {})

        row = {
            "state":     state,
            "year":      year,
            "epi_week":  epi_week,
            # cases
            "confirmed_cases":          c.get("confirmed_cases", ""),
            "suspected_cases":          c.get("suspected_cases", ""),
            "deaths":                   c.get("deaths", ""),
            "healthcare_worker_cases":  c.get("healthcare_worker_cases", ""),
            "source_type":              c.get("source_type", ""),
            "source_url":               c.get("source_url", ""),
            # weather
            "temp_max":   w.get("temp_max", ""),
            "temp_min":   w.get("temp_min", ""),
            "rainfall":   w.get("rainfall", ""),
            "humidity":   w.get("humidity", ""),
            "wind_max":   w.get("wind_max", ""),
            "obs_days":   w.get("obs_days", ""),
            # merge quality flags
            "has_weather": "1" if w else "0",
            "has_cases":   "1" if c else "0",
            "notes":       c.get("notes", ""),
        }
        rows.append(row)

    return rows


def build_report(merged: list[dict], cases: dict, weather: dict) -> str:
    """Build a human-readable coverage report."""
    lines = []
    sep = "=" * 64

    lines.append(sep)
    lines.append("LassaAI — Merge Report")
    lines.append(sep)

    # Global stats
    total_confirmed = sum(
        int(r["confirmed_cases"]) for r in merged
        if r["confirmed_cases"] not in ("", None)
        and str(r["confirmed_cases"]).isdigit()
    )
    total_deaths = sum(
        int(r["deaths"]) for r in merged
        if r["deaths"] not in ("", None)
        and str(r["deaths"]).isdigit()
    )
    years = sorted({r["year"] for r in merged})
    states = sorted({r["state"] for r in merged})
    both = sum(1 for r in merged if r["has_cases"] == "1" and r["has_weather"] == "1")
    cases_only = sum(1 for r in merged if r["has_cases"] == "1" and r["has_weather"] == "0")
    weather_only = sum(1 for r in merged if r["has_cases"] == "0" and r["has_weather"] == "1")

    lines.append(f"\nTotal rows in merged file : {len(merged):,}")
    lines.append(f"Rows with both data types : {both:,}")
    lines.append(f"Rows with cases only      : {cases_only:,}")
    lines.append(f"Rows with weather only    : {weather_only:,}")
    lines.append(f"\nDate range covered        : {min(years)}–{max(years)}")
    lines.append(f"States in dataset         : {len(states)}")
    lines.append(f"Total confirmed cases     : {total_confirmed:,}")
    lines.append(f"Total deaths              : {total_deaths:,}")

    # Per-state coverage
    lines.append(f"\n{sep}")
    lines.append("Per-state coverage")
    lines.append(sep)
    lines.append(f"{'State':<18} {'Weeks':>6} {'Expected':>9} {'Gap%':>6} {'Confirmed':>10} {'Deaths':>7}")
    lines.append("-" * 64)

    state_stats = defaultdict(lambda: {"weeks": 0, "confirmed": 0, "deaths": 0, "missing": []})

    for r in merged:
        s = r["state"]
        if r["has_cases"] == "1":
            state_stats[s]["weeks"] += 1
            conf = r["confirmed_cases"]
            dead = r["deaths"]
            if conf and str(conf).isdigit():
                state_stats[s]["confirmed"] += int(conf)
            if dead and str(dead).isdigit():
                state_stats[s]["deaths"] += int(dead)

    total_expected = len(years) * EXPECTED_WEEKS

    for state in sorted(state_stats):
        st = state_stats[state]
        gap_pct = round(100 * (1 - st["weeks"] / total_expected), 1)
        lines.append(
            f"{state:<18} {st['weeks']:>6,} {total_expected:>9,} {gap_pct:>5.1f}% "
            f"{st['confirmed']:>10,} {st['deaths']:>7,}"
        )

    # Missing weeks (states with > 20% gap)
    missing_states = [s for s, st in state_stats.items()
                      if st["weeks"] < total_expected * 0.8]
    if missing_states:
        lines.append(f"\n{sep}")
        lines.append("States with >20% missing weeks (flagged for manual review)")
        lines.append(sep)
        for s in sorted(missing_states):
            st = state_stats[s]
            lines.append(f"  {s}: {st['weeks']:,}/{total_expected:,} weeks present")

    # Top endemic states
    top_states = sorted(state_stats.items(), key=lambda x: x[1]["confirmed"], reverse=True)[:10]
    lines.append(f"\n{sep}")
    lines.append("Top 10 states by confirmed cases")
    lines.append(sep)
    for state, st in top_states:
        lines.append(f"  {state:<18} {st['confirmed']:>8,} confirmed  {st['deaths']:>6,} deaths")

    lines.append(f"\n{sep}")
    lines.append("Data source breakdown")
    lines.append(sep)
    source_counts = defaultdict(int)
    for r in merged:
        if r["source_type"]:
            source_counts[r["source_type"]] += 1
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        lines.append(f"  {src:<35} {count:>8,} rows")

    lines.append(f"\n{sep}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Merge NCDC and weather datasets")
    parser.add_argument("--report-only", action="store_true", help="Print report without writing CSV")
    args = parser.parse_args()

    cases = load_cases(CASES_CSV)
    weather = load_weather(WEATHER_CSV)

    if not cases and not weather:
        log.error("Both input files missing. Run collect-ncdc-data.py and collect-weather-data.py first.")
        sys.exit(1)

    merged = merge(cases, weather)
    report = build_report(merged, cases, weather)

    print(report)

    REPORT_TXT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_TXT.write_text(report, encoding="utf-8")
    log.info(f"Report saved to {REPORT_TXT}")

    if not args.report_only:
        MERGED_CSV.parent.mkdir(parents=True, exist_ok=True)
        with open(MERGED_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=MERGED_FIELDS)
            writer.writeheader()
            writer.writerows(merged)
        log.info(f"Merged CSV written: {MERGED_CSV} ({len(merged):,} rows)")


if __name__ == "__main__":
    main()
