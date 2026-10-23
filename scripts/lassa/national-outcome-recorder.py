"""
national-outcome-recorder.py — append-only outcome ledger for the frozen
2026-2027 LassaAI national prospective validation.

This script NEVER edits the prospective forecast log. It records a separate
outcome object keyed to the immutable forecast record_sha256 after all four
target weeks are present in the national NCDC series.

Primary-analysis rule:
- use the first-published/as-logged rows already appended to
  data/lassa/lassa_fever_timeseries_full.csv;
- preserve the exact four source-row payloads + source URLs + dataset hash;
- later NCDC revisions belong in a separate sensitivity analysis, never a
  rewrite of the primary outcome.

Usage:
  python scripts/lassa/national-outcome-recorder.py --forecast-record <sha256>
"""

import argparse
import csv
import hashlib
import json
import sys
from datetime import date, timedelta, datetime, timezone
from pathlib import Path

FORECAST_LOG = Path("data/lassa/national-prospective-log.jsonl")
OUTCOME_LOG = Path("data/lassa/national-prospective-outcomes.jsonl")
SERIES = Path("data/lassa/lassa_fever_timeseries_full.csv")
FREEZE_MANIFEST = Path("data/lassa/lassa-national-2026-27-freeze.json")
OUTCOME_CODE = Path("scripts/lassa/national-outcome-recorder.py")
PROTOCOL = Path("docs/lassa/PROSPECTIVE_PROTOCOL_LASSA.md")
FORECAST_CODE = Path("scripts/lassa/national-forecast-now.py")
LOGGER_CODE = Path("scripts/lassa/national-forecast-logger.py")
READOUT_CODE = Path("scripts/lassa/prospective-readout.py")
ENV_LOCK = Path("scripts/lassa/prospective-requirements.txt")
SOURCE_REVIEW = Path("docs/lassa/PRE_FREEZE_SOURCE_REVIEW_2026-09-22.md")

FROZEN_THRESHOLD = 32.0
STUDY_ID = "lassa-national-forecast-2026-27-v1.1"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bytes(obj: dict) -> bytes:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def record_hash(record: dict) -> str:
    unsigned = dict(record)
    unsigned.pop("outcome_record_sha256", None)
    return sha256_bytes(canonical_bytes(unsigned))


def verify_freeze_manifest() -> dict:
    if not FREEZE_MANIFEST.exists():
        raise RuntimeError("pre-season freeze manifest is missing")
    manifest = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "gaialab.lassa-national-freeze.v1":
        raise RuntimeError("freeze manifest schema/version mismatch")
    if manifest.get("study_id") != STUDY_ID:
        raise RuntimeError("freeze manifest belongs to a different study")
    hashes = manifest.get("hashes") or {}
    expected = {
        "protocol_sha256": sha256_file(PROTOCOL),
        "forecast_code_sha256": sha256_file(FORECAST_CODE),
        "logger_code_sha256": sha256_file(LOGGER_CODE),
        "outcome_recorder_sha256": sha256_file(OUTCOME_CODE),
        "readout_code_sha256": sha256_file(READOUT_CODE),
        "environment_lock_sha256": sha256_file(ENV_LOCK),
        "source_review_sha256": sha256_file(SOURCE_REVIEW),
    }
    drift = [name for name, current in expected.items() if hashes.get(name) != current]
    if drift:
        raise RuntimeError("frozen study implementation drift detected in: " + ", ".join(drift))
    if float((manifest.get("endpoint_contract") or {}).get("frozen_threshold_4wk_burden", -1)) != FROZEN_THRESHOLD:
        raise RuntimeError("freeze manifest endpoint threshold does not equal 32")
    return manifest


def load_forecasts() -> list[dict]:
    if not FORECAST_LOG.exists():
        raise RuntimeError(f"forecast log does not exist: {FORECAST_LOG}")

    records = []
    previous = None
    for line_no, line in enumerate(FORECAST_LOG.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        rec = json.loads(line)
        stored = rec.get("record_sha256")
        if not stored:
            raise RuntimeError(f"forecast line {line_no} missing record_sha256")
        unsigned = dict(rec)
        unsigned.pop("record_sha256", None)
        computed = sha256_bytes(canonical_bytes(unsigned))
        if computed != stored:
            raise RuntimeError(f"forecast line {line_no} failed SHA-256 integrity")
        if rec.get("previous_record_sha256") != previous:
            raise RuntimeError(f"forecast line {line_no} broke the hash chain")
        records.append(rec)
        previous = stored
    return records


def load_outcomes() -> list[dict]:
    if not OUTCOME_LOG.exists():
        return []
    records = []
    previous = None
    for line_no, line in enumerate(OUTCOME_LOG.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        rec = json.loads(line)
        stored = rec.get("outcome_record_sha256")
        if not stored or record_hash(rec) != stored:
            raise RuntimeError(f"outcome line {line_no} failed SHA-256 integrity")
        if rec.get("previous_outcome_sha256") != previous:
            raise RuntimeError(f"outcome line {line_no} broke the hash chain")
        records.append(rec)
        previous = stored
    return records


def load_series() -> list[dict]:
    if not SERIES.exists():
        raise RuntimeError(f"national series missing: {SERIES}")
    rows = list(csv.DictReader(SERIES.open(encoding="utf-8")))
    rows.sort(key=lambda r: (int(r["epi_year"]), int(r["epi_week"])))
    return rows


def iso_week_key(day: date) -> tuple[int, int]:
    iso = day.isocalendar()
    return int(iso.year), int(iso.week)


def target_week_keys(forecast: dict) -> list[tuple[int, int]]:
    window = forecast.get("forecast_window") or {}
    start_raw = window.get("start")
    if not start_raw:
        raise RuntimeError("forecast has no forecast_window.start")
    start = date.fromisoformat(start_raw)
    return [iso_week_key(start + timedelta(days=7 * i)) for i in range(4)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--forecast-record",
        required=True,
        help="record_sha256 of the immutable prospective forecast to score",
    )
    args = parser.parse_args()

    try:
        freeze = verify_freeze_manifest()
        forecasts = load_forecasts()
        outcomes = load_outcomes()
        rows = load_series()
    except (RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    forecast = next(
        (r for r in forecasts if r.get("record_sha256") == args.forecast_record),
        None,
    )
    if forecast is None:
        print("ERROR: forecast record SHA not found")
        sys.exit(2)

    if forecast.get("study_id") != STUDY_ID:
        print("ERROR: forecast belongs to a different study")
        sys.exit(2)

    if any(o.get("forecast_record_sha256") == args.forecast_record for o in outcomes):
        print("Outcome already recorded for this forecast. Refusing duplicate.")
        return

    expected = target_week_keys(forecast)
    by_week = {
        (int(r["epi_year"]), int(r["epi_week"])): r
        for r in rows
    }
    missing = [key for key in expected if key not in by_week]
    if missing:
        print(
            "REFUSING to score: not all four target weeks are present in the "
            f"first-published national series. Missing: {missing}"
        )
        sys.exit(3)

    target_rows = [by_week[key] for key in expected]
    confirmed = [int(r.get("confirmed_cases") or 0) for r in target_rows]
    burden = sum(confirmed)
    was_elevated = burden > FROZEN_THRESHOLD
    predicted_probability = float(forecast["national_probability_elevated"])
    predicted_class = predicted_probability >= 0.50

    row_snapshots = []
    for r in target_rows:
        row_snapshots.append({
            "epi_year": int(r["epi_year"]),
            "epi_week": int(r["epi_week"]),
            "week_start_date": r.get("week_start_date"),
            "week_end_date": r.get("week_end_date"),
            "confirmed_cases": int(r.get("confirmed_cases") or 0),
            "deaths": int(r.get("deaths") or 0),
            "extraction_method": r.get("extraction_method"),
            "extraction_timestamp": r.get("extraction_timestamp"),
            "report_pdf_url": r.get("report_pdf_url"),
        })

    baseline = forecast.get("baseline", {})
    primary = baseline.get("primary", {})
    secondary = baseline.get("secondary", {})
    seasonal = baseline.get("seasonal_climatology", {})
    seasonal_persistence = baseline.get("seasonal_plus_persistence", {})

    outcome = {
        "schema_version": "gaialab.lassa-national-outcome.v1",
        "study_id": STUDY_ID,
        "forecast_record_sha256": forecast["record_sha256"],
        "forecast_sha256": forecast.get("forecast_sha256"),
        "forecast_logged_at_utc": forecast.get("logged_at_utc"),
        "freeze_manifest_sha256": sha256_file(FREEZE_MANIFEST),
        "freeze_commit_sha": (freeze.get("git") or {}).get("commit_sha"),
        "outcome_recorded_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "target_weeks": [
            {"epi_year": year, "epi_week": week}
            for year, week in expected
        ],
        "source_rows": row_snapshots,
        "series_sha256_at_outcome_capture": sha256_file(SERIES),
        "confirmed_4wk_burden": burden,
        "elevated_threshold_4wk_burden": FROZEN_THRESHOLD,
        "was_elevated": was_elevated,
        "model_probability": predicted_probability,
        "model_predicted_class_at_0_50": predicted_class,
        "model_class_correct_at_0_50": predicted_class == was_elevated,
        "primary_baseline": {
            "name": primary.get("name"),
            "raw_score": primary.get("raw_score"),
            "probability": primary.get("probability"),
        },
        "secondary_baseline": {
            "name": secondary.get("name"),
            "raw_score": secondary.get("raw_score"),
            "probability": secondary.get("probability"),
        },
        "seasonal_climatology_baseline": {
            "name": seasonal.get("name"),
            "probability": seasonal.get("probability"),
        },
        "seasonal_plus_persistence_baseline": {
            "name": seasonal_persistence.get("name"),
            "probability": seasonal_persistence.get("probability"),
        },
        "previous_outcome_sha256": (
            outcomes[-1]["outcome_record_sha256"] if outcomes else None
        ),
        "scientific_boundary": (
            "Prospective national surveillance-model outcome only; does not establish "
            "clinical utility, causality, prevention of cases, or treatment efficacy."
        ),
    }
    outcome["outcome_record_sha256"] = record_hash(outcome)

    OUTCOME_LOG.parent.mkdir(parents=True, exist_ok=True)
    with OUTCOME_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(outcome, ensure_ascii=False, sort_keys=True) + "\n")

    print("Recorded hash-chained national prospective outcome.")
    print(f"  forecast record : {forecast['record_sha256']}")
    print(f"  target weeks    : {expected}")
    print(f"  4-week burden   : {burden}")
    print(f"  elevated (>32)  : {was_elevated}")
    print(f"  outcome sha     : {outcome['outcome_record_sha256']}")
    print(f"  ledger          : {OUTCOME_LOG}")


if __name__ == "__main__":
    main()
