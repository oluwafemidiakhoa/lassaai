"""
LassaAI — Prospective Forecast Logger
======================================
Runs forecast-now.py and appends a timestamped, immutable record to
data/lassa/prospective-log.jsonl BEFORE any outcome is known.

This log is the scientific evidence base for prospective validation.
Each line is a single JSON object (newline-delimited JSON / JSONL).
Records must NEVER be edited after writing — only appended.

Usage (run every Monday before NCDC sitrep is published):
  python scripts/lassa/forecast-logger.py

Cron example (every Monday 06:00 WAT = 05:00 UTC):
  0 5 * * 1 cd /app && python scripts/lassa/forecast-logger.py >> logs/forecast-logger.log 2>&1
"""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FORECAST_JSON   = Path("data/lassa/current-forecast.json")
PROSPECTIVE_LOG = Path("data/lassa/prospective-log.jsonl")
FORECAST_SCRIPT = Path("scripts/lassa/forecast-now.py")


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def already_logged_this_week(log_path: Path, year: int, week: int) -> bool:
    """Return True if a record for (year, week) already exists in the log."""
    if not log_path.exists():
        return False
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("forecast_year") == year and rec.get("forecast_week") == week:
                    return True
            except json.JSONDecodeError:
                continue
    return False


def main():
    logged_at = datetime.now(tz=timezone.utc)
    iso_ts    = logged_at.isoformat()

    # ── Step 1: regenerate forecast ──────────────────────────────────────────
    print(f"[{iso_ts}] Running forecast-now.py ...")
    result = subprocess.run(
        [sys.executable, str(FORECAST_SCRIPT)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("ERROR: forecast-now.py failed:")
        print(result.stderr)
        sys.exit(1)
    print(result.stdout)

    # ── Step 2: load fresh forecast ──────────────────────────────────────────
    if not FORECAST_JSON.exists():
        print(f"ERROR: {FORECAST_JSON} not found after running forecast-now.py")
        sys.exit(1)

    forecast = json.loads(FORECAST_JSON.read_text(encoding="utf-8"))
    forecasts = forecast.get("forecasts", [])
    if not forecasts:
        print("ERROR: forecast JSON contains no forecasts — aborting log entry")
        sys.exit(1)

    # Derive the forecast epi-year/week from the first record
    forecast_year = forecasts[0].get("as_of_year")
    forecast_week = forecasts[0].get("as_of_week")

    # ── Step 3: idempotency guard ────────────────────────────────────────────
    if already_logged_this_week(PROSPECTIVE_LOG, forecast_year, forecast_week):
        print(f"[{iso_ts}] Already logged forecast for {forecast_year}-W{forecast_week:02d}. Skipping.")
        return

    # ── Step 4: build log record ─────────────────────────────────────────────
    high   = [f["state"] for f in forecasts if f["risk"] in ("HIGH", "VERY HIGH")]
    medium = [f["state"] for f in forecasts if f["risk"] == "MEDIUM"]
    low    = [f["state"] for f in forecasts if f["risk"] == "LOW"]

    record = {
        "logged_at_utc":   iso_ts,
        "forecast_year":   forecast_year,
        "forecast_week":   forecast_week,
        "horizon_weeks":   forecast.get("forecast_horizon_weeks", 4),
        "model_version":   forecast.get("model", "outbreak-model-v1"),
        "forecast_sha256": sha256_of_file(FORECAST_JSON),
        "n_states":        len(forecasts),
        "n_high":          len(high),
        "n_medium":        len(medium),
        "n_low":           len(low),
        "high_states":     high,
        "medium_states":   medium,
        # Full per-state probabilities — ground truth for AUROC calculation
        "state_forecasts": [
            {
                "state":       f["state"],
                "probability": f["probability"],
                "risk":        f["risk"],
                "change":      f.get("change_vs_last_week"),
            }
            for f in forecasts
        ],
        # Outcome fields — filled in retroactively by outcome-recorder.py
        # once NCDC sitrep is published for the horizon window
        "outcome_recorded_at": None,
        "outcomes": None,   # list of {state, confirmed_cases, is_outbreak}
        "auroc_this_week":  None,
        "notes": None,
    }

    # ── Step 5: append to log (atomic write) ─────────────────────────────────
    PROSPECTIVE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(PROSPECTIVE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[{iso_ts}] Logged forecast for {forecast_year}-W{forecast_week:02d}")
    print(f"  HIGH  ({len(high)}): {', '.join(high) if high else 'none'}")
    print(f"  MEDIUM({len(medium)}): {', '.join(medium[:5]) if medium else 'none'}" +
          (f" ...+{len(medium)-5} more" if len(medium) > 5 else ""))
    print(f"  LOW   ({len(low)} states)")
    print(f"  Log:  {PROSPECTIVE_LOG}")


if __name__ == "__main__":
    main()
