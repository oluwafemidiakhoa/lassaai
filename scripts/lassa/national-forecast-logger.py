"""
national-forecast-logger.py — append the registered national forecast to the
prospective log (append-only, hashed, idempotent per data epi-week).

This is the honest prospective-validation record for the national model
(out-of-time AUROC 0.880 vs 0.849 naive). Each forecast is an append-only,
hash-chained JSONL record. Outcomes are written to a separate immutable outcome
ledger once NCDC publishes the full target window.

HONESTY GUARD: refuses to log a forecast whose outcome window is already in the
past (window_is_future = false). The prospective log must contain ONLY genuine
forward forecasts — never a stale window relabelled as "prospective".

Usage (run weekly, AFTER national-forecast-now.py, BEFORE the window's NCDC sitreps):
  python scripts/lassa/national-forecast-now.py
  python scripts/lassa/national-forecast-logger.py
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FORECAST = Path("data/lassa/national-forecast.json")
LOG      = Path("data/lassa/national-prospective-log.jsonl")
SERIES   = Path("data/lassa/lassa_fever_timeseries_full.csv")
PROTOCOL = Path("docs/lassa/PROSPECTIVE_PROTOCOL_LASSA.md")
FREEZE_MANIFEST = Path("data/lassa/lassa-national-2026-27-freeze.json")
FORECAST_CODE = Path("scripts/lassa/national-forecast-now.py")
LOGGER_CODE = Path("scripts/lassa/national-forecast-logger.py")
OUTCOME_CODE = Path("scripts/lassa/national-outcome-recorder.py")
READOUT_CODE = Path("scripts/lassa/prospective-readout.py")
ENV_LOCK = Path("scripts/lassa/prospective-requirements.txt")
SOURCE_REVIEW = Path("docs/lassa/PRE_FREEZE_SOURCE_REVIEW_2026-09-22.md")

STUDY_ID = "lassa-national-forecast-2026-27-v1.1"
FROZEN_MODEL_VERSION = "national-elevated-transmission-v1"
FROZEN_ELEVATED_THRESHOLD = 32.0
FROZEN_HORIZON_WEEKS = 4
PRIMARY_BASELINE = "recent_4_week_case_average"
SECONDARY_BASELINE = "previous_week_case_count"
SEASONAL_BASELINE = "seasonal_climatology_harmonic"
SEASONAL_PERSISTENCE_BASELINE = "seasonal_plus_persistence"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_record_bytes(record: dict) -> bytes:
    return json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def record_hash(record: dict) -> str:
    unsigned = dict(record)
    unsigned.pop("record_sha256", None)
    return sha256_bytes(canonical_record_bytes(unsigned))


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def load_verified_log() -> list[dict]:
    if not LOG.exists():
        return []

    records = []
    previous = None
    for line_no, line in enumerate(LOG.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"prospective log line {line_no} is invalid JSON: {exc}") from exc

        stored_hash = record.get("record_sha256")
        if not stored_hash:
            raise RuntimeError(f"prospective log line {line_no} has no record_sha256")
        if record_hash(record) != stored_hash:
            raise RuntimeError(f"prospective log line {line_no} failed its SHA-256 integrity check")
        if record.get("previous_record_sha256") != previous:
            raise RuntimeError(f"prospective log line {line_no} broke the hash chain")

        records.append(record)
        previous = stored_hash
    return records


def load_and_verify_freeze_manifest() -> dict:
    if not FREEZE_MANIFEST.exists():
        raise RuntimeError(
            "pre-season freeze manifest is missing; refusing to create a scored prospective record"
        )
    try:
        manifest = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"freeze manifest is invalid JSON: {exc}") from exc

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
    drift = [
        name for name, current in expected.items()
        if hashes.get(name) != current
    ]
    if drift:
        raise RuntimeError(
            "frozen study implementation drift detected in: " + ", ".join(drift)
        )

    env_contract = manifest.get("environment_contract") or {}
    frozen_packages = env_contract.get("packages") or {}
    if not frozen_packages:
        raise RuntimeError("freeze manifest has no frozen package environment")

    endpoint = manifest.get("endpoint_contract") or {}
    if float(endpoint.get("frozen_threshold_4wk_burden", -1)) != FROZEN_ELEVATED_THRESHOLD:
        raise RuntimeError("freeze manifest endpoint threshold does not equal 32")
    if int(endpoint.get("forecast_horizon_weeks", -1)) != FROZEN_HORIZON_WEEKS:
        raise RuntimeError("freeze manifest horizon does not equal 4 weeks")
    return manifest


def assert_frozen_contract(fc: dict) -> None:
    if fc.get("model_version") != FROZEN_MODEL_VERSION:
        raise RuntimeError(
            f"model version drift: {fc.get('model_version')!r} != {FROZEN_MODEL_VERSION!r}"
        )
    if float(fc.get("elevated_threshold_4wk_burden", -1)) != FROZEN_ELEVATED_THRESHOLD:
        raise RuntimeError("prospective endpoint threshold drifted from the frozen value 32")
    if int(fc.get("forecast_window", {}).get("horizon_weeks", -1)) != FROZEN_HORIZON_WEEKS:
        raise RuntimeError("forecast horizon drifted from the frozen 4-week contract")

    baseline = fc.get("baseline") or {}
    if baseline.get("primary", {}).get("name") != PRIMARY_BASELINE:
        raise RuntimeError("primary baseline is missing or differs from the frozen protocol")
    if baseline.get("secondary", {}).get("name") != SECONDARY_BASELINE:
        raise RuntimeError("secondary baseline is missing or differs from the frozen protocol")
    if baseline.get("seasonal_climatology", {}).get("name") != SEASONAL_BASELINE:
        raise RuntimeError("seasonal climatology comparator is missing or differs from protocol v1.1")
    if baseline.get("seasonal_plus_persistence", {}).get("name") != SEASONAL_PERSISTENCE_BASELINE:
        raise RuntimeError("seasonal+persistence comparator is missing or differs from protocol v1.1")
    for name in ("primary", "secondary", "seasonal_climatology", "seasonal_plus_persistence"):
        if baseline.get(name, {}).get("probability") is None:
            raise RuntimeError(f"{name} baseline probability is missing; Brier/ECE would be unscorable")

    forecast_env = fc.get("environment") or {}
    freeze_env = load_and_verify_freeze_manifest().get("environment_contract") or {}
    expected = {
        "python": freeze_env.get("python"),
        "numpy": (freeze_env.get("packages") or {}).get("numpy"),
        "scikit_learn": (freeze_env.get("packages") or {}).get("scikit-learn"),
        "xgboost": (freeze_env.get("packages") or {}).get("xgboost"),
    }
    drift = [name for name, value in expected.items() if forecast_env.get(name) != value]
    if drift:
        raise RuntimeError("forecast runtime environment drift detected in: " + ", ".join(drift))


def main():
    if not FORECAST.exists():
        print("ERROR: national-forecast.json not found — run national-forecast-now.py first.")
        sys.exit(1)

    fc = json.loads(FORECAST.read_text(encoding="utf-8"))
    assert_frozen_contract(fc)

    if not SERIES.exists() or not PROTOCOL.exists():
        print("ERROR: frozen dataset/protocol source missing; refusing to log.")
        sys.exit(1)

    try:
        freeze = load_and_verify_freeze_manifest()
    except RuntimeError as exc:
        print(f"ERROR: freeze contract failure: {exc}")
        sys.exit(5)

    try:
        existing_records = load_verified_log()
    except RuntimeError as exc:
        print(f"ERROR: prospective log integrity failure: {exc}")
        sys.exit(3)

    # ── Honesty guard: never log a stale (already-resolved) window as prospective ──
    if not fc.get("window_is_future"):
        print("REFUSING to log: the forecast window is not in the future (data is stale).")
        print(f"  {fc.get('note')}")
        print(f"  data_through = {fc.get('data_through')}  window = {fc.get('forecast_window')}")
        sys.exit(2)

    dt = fc.get("data_through", {})
    yr, wk = dt.get("epi_year"), dt.get("epi_week")

    # ── Idempotency: one immutable record per (data epi-year, epi-week) ────────────
    forecast_sha = sha256_file(FORECAST)
    for r in existing_records:
        rdt = r.get("data_through", {})
        if rdt.get("epi_year") == yr and rdt.get("epi_week") == wk:
            if r.get("forecast_sha256") != forecast_sha:
                print(
                    f"ERROR: a different forecast is already locked for {yr}-W{wk:02d}; "
                    "refusing to overwrite or append a competing record."
                )
                sys.exit(4)
            print(f"Already locked for data-through {yr}-W{wk:02d}. Integrity verified; skipping.")
            return

    record = dict(fc)
    record["schema_version"] = "gaialab.lassa-national-prospective.v1"
    record["study_id"] = STUDY_ID
    record["logged_at_utc"] = datetime.now(tz=timezone.utc).isoformat()
    record["forecast_sha256"] = forecast_sha
    record["dataset_sha256"] = sha256_file(SERIES)
    record["protocol_sha256"] = sha256_file(PROTOCOL)
    record["freeze_manifest_sha256"] = sha256_file(FREEZE_MANIFEST)
    record["freeze_commit_sha"] = (freeze.get("git") or {}).get("commit_sha")
    record["code_commit_sha"] = git_head()
    record["previous_record_sha256"] = (
        existing_records[-1]["record_sha256"] if existing_records else None
    )
    # Outcomes are NEVER written back into this forecast record. A separate append-only
    # outcome ledger references record_sha256, preserving the original locked bytes.
    record["record_sha256"] = record_hash(record)

    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    w = fc["forecast_window"]
    print(f"Logged national prospective forecast (append-only).")
    print(f"  data through : {yr}-W{wk:02d} ({dt.get('week_end_date')})")
    print(f"  window       : {w['start']} .. {w['end']} ({w['horizon_weeks']} wks)")
    print(f"  P(elevated)  : {fc['national_probability_elevated']}  → {fc['risk']}")
    print(f"  forecast sha : {record['forecast_sha256'][:16]}…")
    print(f"  record sha   : {record['record_sha256'][:16]}…")
    print(f"  dataset sha  : {record['dataset_sha256'][:16]}…")
    print(f"  code commit  : {record['code_commit_sha']}")
    print(f"  log          : {LOG}")


if __name__ == "__main__":
    main()
