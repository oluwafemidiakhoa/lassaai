"""
national-forecast-logger.py — append the VALIDATED national forecast to the
prospective log (append-only, hashed, idempotent per data epi-week).

This is the honest prospective-validation record for the national model
(out-of-time AUROC 0.880 vs 0.849 naive). Each line is immutable JSONL; outcomes
are filled in later by an outcome recorder once NCDC publishes the window.

HONESTY GUARD: refuses to log a forecast whose outcome window is already in the
past (window_is_future = false). The prospective log must contain ONLY genuine
forward forecasts — never a stale window relabelled as "prospective".

Usage (run weekly, AFTER national-forecast-now.py, BEFORE the window's NCDC sitreps):
  python scripts/lassa/national-forecast-now.py
  python scripts/lassa/national-forecast-logger.py
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

FORECAST = Path("data/lassa/national-forecast.json")
LOG      = Path("data/lassa/national-prospective-log.jsonl")


def main():
    if not FORECAST.exists():
        print("ERROR: national-forecast.json not found — run national-forecast-now.py first.")
        sys.exit(1)

    fc = json.loads(FORECAST.read_text(encoding="utf-8"))

    # ── Honesty guard: never log a stale (already-resolved) window as prospective ──
    if not fc.get("window_is_future"):
        print("REFUSING to log: the forecast window is not in the future (data is stale).")
        print(f"  {fc.get('note')}")
        print(f"  data_through = {fc.get('data_through')}  window = {fc.get('forecast_window')}")
        sys.exit(2)

    dt = fc.get("data_through", {})
    yr, wk = dt.get("epi_year"), dt.get("epi_week")

    # ── Idempotency: one record per (data epi-year, epi-week) ─────────────────────
    if LOG.exists():
        for line in LOG.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            rdt = r.get("data_through", {})
            if rdt.get("epi_year") == yr and rdt.get("epi_week") == wk:
                print(f"Already logged for data-through {yr}-W{wk:02d}. Skipping (append-only).")
                return

    record = dict(fc)
    record["logged_at_utc"]      = datetime.now(tz=timezone.utc).isoformat()
    record["forecast_sha256"]    = hashlib.sha256(FORECAST.read_bytes()).hexdigest()
    record["outcome_recorded_at"] = None
    record["outcome"]            = None   # {confirmed_4wk_burden, was_elevated} — filled later
    record["outcome_correct"]    = None

    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    w = fc["forecast_window"]
    print(f"Logged national prospective forecast (append-only).")
    print(f"  data through : {yr}-W{wk:02d} ({dt.get('week_end_date')})")
    print(f"  window       : {w['start']} .. {w['end']} ({w['horizon_weeks']} wks)")
    print(f"  P(elevated)  : {fc['national_probability_elevated']}  → {fc['risk']}")
    print(f"  sha256       : {record['forecast_sha256'][:16]}…")
    print(f"  log          : {LOG}")


if __name__ == "__main__":
    main()
