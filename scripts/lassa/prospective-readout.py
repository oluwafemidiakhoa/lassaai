#!/usr/bin/env python3
"""Frozen LassaAI 2026-27 prospective readout.

Reads only the immutable forecast and outcome ledgers, verifies both hash chains,
matches outcomes to their original forecast records, and computes the pre-specified
prospective metrics and verdict. This program is hashed into the one-time pre-season
freeze manifest and must not change after the first scored forecast.

Primary scoring boundary:
- study: lassa-national-forecast-2026-27-v1.1
- forecast issue/data-through weeks: 2026-W45 through 2027-W17
- comparator: strongest pre-specified comparator by AUROC on the same scoreable weeks
- calibration: Brier + 5 equal-width-bin reliability/ECE
- uncertainty: paired moving-block bootstrap, 4-week blocks primary, 8-week sensitivity
- bootstrap: 4000 requested replicates, seed 20260922
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from sklearn.metrics import brier_score_loss, roc_auc_score

FORECAST_LOG = Path("data/lassa/national-prospective-log.jsonl")
OUTCOME_LOG = Path("data/lassa/national-prospective-outcomes.jsonl")
STUDY_ID = "lassa-national-forecast-2026-27-v1.1"
BOOTSTRAP_REPS = 4000
BOOTSTRAP_SEED = 20260922
ECE_BINS = 5
PRIMARY_BLOCK = 4
SENSITIVITY_BLOCK = 8

COMPARATORS = (
    "primary_baseline",
    "secondary_baseline",
    "seasonal_climatology_baseline",
    "seasonal_plus_persistence_baseline",
)


def canonical_bytes(obj: dict) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_forecasts() -> list[dict]:
    records, previous = [], None
    if not FORECAST_LOG.exists():
        return []
    for line_no, line in enumerate(FORECAST_LOG.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        rec = json.loads(line)
        stored = rec.get("record_sha256")
        unsigned = dict(rec)
        unsigned.pop("record_sha256", None)
        if not stored or sha256_bytes(canonical_bytes(unsigned)) != stored:
            raise RuntimeError(f"forecast line {line_no} failed SHA-256 integrity")
        if rec.get("previous_record_sha256") != previous:
            raise RuntimeError(f"forecast line {line_no} broke the hash chain")
        if rec.get("study_id") != STUDY_ID:
            raise RuntimeError(f"forecast line {line_no} belongs to a different study")
        records.append(rec)
        previous = stored
    return records


def load_outcomes() -> list[dict]:
    records, previous = [], None
    if not OUTCOME_LOG.exists():
        return []
    for line_no, line in enumerate(OUTCOME_LOG.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        rec = json.loads(line)
        stored = rec.get("outcome_record_sha256")
        unsigned = dict(rec)
        unsigned.pop("outcome_record_sha256", None)
        if not stored or sha256_bytes(canonical_bytes(unsigned)) != stored:
            raise RuntimeError(f"outcome line {line_no} failed SHA-256 integrity")
        if rec.get("previous_outcome_sha256") != previous:
            raise RuntimeError(f"outcome line {line_no} broke the hash chain")
        if rec.get("study_id") != STUDY_ID:
            raise RuntimeError(f"outcome line {line_no} belongs to a different study")
        records.append(rec)
        previous = stored
    return records


def in_primary_window(forecast: dict) -> bool:
    dt = forecast.get("data_through") or {}
    year, week = int(dt.get("epi_year", -1)), int(dt.get("epi_week", -1))
    return (year == 2026 and week >= 45) or (year == 2027 and week <= 17)


def ece_and_reliability(y_true, prob, bins=ECE_BINS):
    y_true = np.asarray(y_true, dtype=int)
    prob = np.asarray(prob, dtype=float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    curve = []
    for b in range(bins):
        lo, hi = float(edges[b]), float(edges[b + 1])
        mask = (prob >= lo) & (prob < hi if b < bins - 1 else prob <= hi)
        n = int(mask.sum())
        if n == 0:
            curve.append({"bin": b + 1, "lower": lo, "upper": hi, "n": 0, "mean_probability": None, "observed_rate": None})
            continue
        mean_prob = float(prob[mask].mean())
        obs_rate = float(y_true[mask].mean())
        ece += (n / len(y_true)) * abs(obs_rate - mean_prob)
        curve.append({"bin": b + 1, "lower": lo, "upper": hi, "n": n, "mean_probability": mean_prob, "observed_rate": obs_rate})
    return float(ece), curve


def metrics(y_true, score, prob):
    ece, curve = ece_and_reliability(y_true, prob)
    return {
        "auroc": float(roc_auc_score(y_true, score)),
        "brier": float(brier_score_loss(y_true, prob)),
        "ece_5bin": ece,
        "reliability_5bin": curve,
    }


def paired_block_ci(y_true, model_score, model_prob, base_score, base_prob, block_len):
    y_true = np.asarray(y_true, dtype=int)
    model_score = np.asarray(model_score, dtype=float)
    model_prob = np.asarray(model_prob, dtype=float)
    base_score = np.asarray(base_score, dtype=float)
    base_prob = np.asarray(base_prob, dtype=float)
    n = len(y_true)
    if n < block_len * 2 or len(np.unique(y_true)) < 2:
        return None
    starts = np.arange(0, n - block_len + 1)
    n_blocks = int(math.ceil(n / block_len))
    rng = np.random.default_rng(BOOTSTRAP_SEED + 1000 * block_len + n)
    auc_delta, brier_delta = [], []
    for _ in range(BOOTSTRAP_REPS):
        idx = []
        for start in rng.choice(starts, size=n_blocks, replace=True):
            idx.extend(range(int(start), int(start) + block_len))
        idx = np.asarray(idx[:n], dtype=int)
        yy = y_true[idx]
        if len(np.unique(yy)) < 2:
            continue
        auc_delta.append(roc_auc_score(yy, model_score[idx]) - roc_auc_score(yy, base_score[idx]))
        brier_delta.append(brier_score_loss(yy, model_prob[idx]) - brier_score_loss(yy, base_prob[idx]))
    if len(auc_delta) < max(500, BOOTSTRAP_REPS // 4):
        return None
    return {
        "block_length": block_len,
        "replicates_requested": BOOTSTRAP_REPS,
        "replicates_valid": len(auc_delta),
        "delta_auc_ci95": [float(x) for x in np.quantile(auc_delta, [0.025, 0.975])],
        "delta_brier_ci95": [float(x) for x in np.quantile(brier_delta, [0.025, 0.975])],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/lassa/prospective-readout.json")
    args = parser.parse_args()

    forecasts = load_forecasts()
    outcomes = load_outcomes()
    forecast_by_sha = {r["record_sha256"]: r for r in forecasts}

    joined = []
    for out in outcomes:
        fc = forecast_by_sha.get(out.get("forecast_record_sha256"))
        if not fc or not in_primary_window(fc):
            continue
        joined.append((fc, out))

    joined.sort(key=lambda pair: (
        int(pair[0]["data_through"]["epi_year"]),
        int(pair[0]["data_through"]["epi_week"]),
    ))

    if len(joined) < 10:
        verdict = "neutral_inconclusive_underpowered"
        result = {
            "study_id": STUDY_ID,
            "scoreable_weeks": len(joined),
            "verdict": verdict,
            "reason": "fewer than 10 scoreable weeks",
            "bootstrap_reps": BOOTSTRAP_REPS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "ece_bins": ECE_BINS,
        }
    else:
        y = np.asarray([int(out["was_elevated"]) for _, out in joined], dtype=int)
        if len(np.unique(y)) < 2:
            verdict = "neutral_inconclusive_underpowered"
            result = {
                "study_id": STUDY_ID,
                "scoreable_weeks": len(joined),
                "verdict": verdict,
                "reason": "scoreable weeks do not contain both outcome classes",
                "bootstrap_reps": BOOTSTRAP_REPS,
                "bootstrap_seed": BOOTSTRAP_SEED,
                "ece_bins": ECE_BINS,
            }
        else:
            model_prob = np.asarray([float(out["model_probability"]) for _, out in joined])
            model = metrics(y, model_prob, model_prob)

            comp = {}
            for name in COMPARATORS:
                probs = np.asarray([float((out[name] or {})["probability"]) for _, out in joined])
                if name in ("primary_baseline", "secondary_baseline"):
                    scores = np.asarray([float((out[name] or {})["raw_score"]) for _, out in joined])
                else:
                    scores = probs
                comp[name] = {
                    "scores": scores,
                    "probabilities": probs,
                    "metrics": metrics(y, scores, probs),
                }

            best_name = max(COMPARATORS, key=lambda n: comp[n]["metrics"]["auroc"])
            best = comp[best_name]
            gain = model["auroc"] - best["metrics"]["auroc"]
            brier_delta = model["brier"] - best["metrics"]["brier"]
            block4 = paired_block_ci(y, model_prob, model_prob, best["scores"], best["probabilities"], PRIMARY_BLOCK)
            block8 = paired_block_ci(y, model_prob, model_prob, best["scores"], best["probabilities"], SENSITIVITY_BLOCK)

            if model["auroc"] < best["metrics"]["auroc"] or model["auroc"] < 0.70:
                verdict = "failure"
            elif gain >= 0.02 and block4 and block4["delta_auc_ci95"][0] > 0 and brier_delta <= 0:
                verdict = "success"
            else:
                verdict = "neutral"

            result = {
                "study_id": STUDY_ID,
                "scoreable_weeks": len(joined),
                "outcome_class_counts": {"elevated": int(y.sum()), "not_elevated": int((1-y).sum())},
                "model": model,
                "comparators": {k: v["metrics"] for k, v in comp.items()},
                "strongest_comparator": best_name,
                "auroc_gain": float(gain),
                "brier_delta": float(brier_delta),
                "primary_uncertainty": block4,
                "sensitivity_uncertainty": block8,
                "verdict": verdict,
                "decision_contract": {
                    "success": "gain >= 0.02 AND 4-week paired CI lower bound > 0 AND Brier <= strongest comparator AND absolute AUROC >= 0.70",
                    "neutral": "not success and not failure; includes gain < 0.02, binding CI spanning 0, or Brier worse than the strongest comparator",
                    "failure": "with a scoreable two-class evaluation, model AUROC below strongest comparator OR absolute AUROC < 0.70",
                    "inconclusive_underpowered": "fewer than 10 scoreable weeks or absence of both outcome classes; reported as neutral/inconclusive, not failure",
                },
                "bootstrap_reps": BOOTSTRAP_REPS,
                "bootstrap_seed": BOOTSTRAP_SEED,
                "ece_bins": ECE_BINS,
            }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
