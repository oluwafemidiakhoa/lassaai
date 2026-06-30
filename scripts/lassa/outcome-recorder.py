"""
LassaAI — Outcome Recorder
============================
After NCDC publishes a sitrep, run this script to record ground-truth
outcomes against previously logged forecasts. This is what makes the
prospective log scientifically valid — predictions are timestamped
BEFORE outcomes are known, outcomes recorded AFTER.

Usage:
  python scripts/lassa/outcome-recorder.py --week 2026-W22 --sitrep data/lassa/sitreps/2026-W22.csv

CSV format (one row per state):
  state,confirmed_cases,deaths

The script matches the sitrep week to forecast records in prospective-log.jsonl
and fills in the outcome fields. It also recomputes a running AUROC.
"""

import argparse
import json
import re
import csv
from datetime import datetime, timezone
from pathlib import Path
from sklearn.metrics import roc_auc_score  # type: ignore

PROSPECTIVE_LOG = Path("data/lassa/prospective-log.jsonl")
OUTBREAK_THRESHOLD = 1  # ≥1 confirmed case = outbreak week for a state


def load_log() -> list[dict]:
    if not PROSPECTIVE_LOG.exists():
        return []
    records = []
    with open(PROSPECTIVE_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def save_log(records: list[dict]):
    PROSPECTIVE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(PROSPECTIVE_LOG, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def parse_sitrep_csv(path: Path) -> dict[str, dict]:
    outcomes = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            state = row.get("state", "").strip()
            if not state:
                continue
            cases  = int(float(row.get("confirmed_cases", 0) or 0))
            deaths = int(float(row.get("deaths", 0) or 0))
            outcomes[state] = {
                "confirmed_cases": cases,
                "deaths": deaths,
                "is_outbreak": cases >= OUTBREAK_THRESHOLD,
            }
    return outcomes


def compute_running_auroc(records: list[dict]) -> float | None:
    y_true, y_score = [], []
    for rec in records:
        if not rec.get("outcomes"):
            continue
        oc_map = {o["state"]: o["is_outbreak"] for o in rec["outcomes"]}
        for sf in rec.get("state_forecasts", []):
            state = sf["state"]
            if state in oc_map:
                y_true.append(int(oc_map[state]))
                y_score.append(sf["probability"])
    if len(y_true) < 2 or len(set(y_true)) < 2:
        return None
    return float(roc_auc_score(y_true, y_score))


def main():
    parser = argparse.ArgumentParser(description="Record NCDC sitrep outcomes against forecast log")
    parser.add_argument("--week",    required=True, help="Epi week to record, e.g. 2026-W22")
    parser.add_argument("--sitrep",  required=True, help="Path to sitrep CSV")
    parser.add_argument("--notes",   default=None,  help="Optional free-text notes")
    args = parser.parse_args()

    # Parse year/week
    m = re.match(r"(\d{4})-W(\d{1,2})$", args.week)
    if not m:
        print("ERROR: --week must be in format YYYY-WNN (e.g. 2026-W22)")
        raise SystemExit(1)
    year, week = int(m.group(1)), int(m.group(2))

    sitrep_path = Path(args.sitrep)
    if not sitrep_path.exists():
        print(f"ERROR: sitrep file not found: {sitrep_path}")
        raise SystemExit(1)

    outcomes = parse_sitrep_csv(sitrep_path)
    print(f"Loaded sitrep: {len(outcomes)} states, {sum(1 for o in outcomes.values() if o['is_outbreak'])} outbreak states")

    records = load_log()
    matched = False
    for rec in records:
        if rec.get("forecast_year") == year and rec.get("forecast_week") == week:
            rec["outcome_recorded_at"] = datetime.now(tz=timezone.utc).isoformat()
            rec["outcomes"] = [
                {"state": s, **v}
                for s, v in outcomes.items()
            ]
            rec["notes"] = args.notes
            matched = True
            break

    if not matched:
        print(f"ERROR: No forecast found for {year}-W{week:02d} in {PROSPECTIVE_LOG}")
        print("Available forecast weeks:", [
            f"{r['forecast_year']}-W{r['forecast_week']:02d}"
            for r in records if r.get("forecast_year")
        ])
        raise SystemExit(1)

    # Recompute running AUROC across all completed records
    auroc = compute_running_auroc(records)
    for rec in records:
        if rec.get("forecast_year") == year and rec.get("forecast_week") == week:
            rec["auroc_this_week"] = auroc

    save_log(records)

    print(f"\nOutcomes recorded for {year}-W{week:02d}")
    print(f"Running prospective AUROC ({sum(1 for r in records if r.get('outcomes'))} weeks): "
          f"{auroc:.4f}" if auroc else "Running prospective AUROC: insufficient data (need ≥2 weeks with both classes)")
    print(f"Log updated: {PROSPECTIVE_LOG}")


if __name__ == "__main__":
    main()
