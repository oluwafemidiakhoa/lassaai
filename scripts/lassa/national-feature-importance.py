#!/usr/bin/env python3
"""
national-feature-importance.py -- gain importance of the FROZEN v1.1 national Lassa model.

Writes data/lassa/national-feature-importance.json, which /api/lassa/study-status serves and the
public /lassa page reads. It fits the model by executing the frozen forecast code itself
(scripts/lassa/national-forecast-now.py, up to its model.fit) on the frozen dataset snapshot, so
the numbers describe exactly the model the 2026-27 freeze locks: 9 national features, XGBoost,
random_state=0, n_jobs=1, trained on every labelled week of the frozen dataset.

Refuses to run unless:
  - the dataset's SHA-256 equals the freeze manifest's dataset_sha256 (the live CSV gains weeks
    after the freeze, so pass the frozen snapshot explicitly);
  - the forecast code's SHA-256 equals its forecast_code_sha256;
  - the interpreter and packages are exactly the freeze environment lock (CPython 3.11.16,
    numpy 1.26.4, scikit-learn 1.4.2, xgboost 2.0.3), unless --out writes a non-canonical file.

Regenerate (Linux x86_64, as recorded in the freeze manifest; any directory, from the repo root):

    git show 1797d581b0755be317043137ee6230167aeb4f83:data/lassa/lassa_fever_timeseries_full.csv > /tmp/frozen.csv
    uv venv --python 3.11.16 /tmp/lassa-fi && uv pip install --python /tmp/lassa-fi -r scripts/lassa/prospective-requirements.txt
    /tmp/lassa-fi/bin/python scripts/lassa/national-feature-importance.py /tmp/frozen.csv

Optional:
  --out PATH           write somewhere else (no environment-lock check; for cross-checks)
  --cross-check PATH   record another environment's run (a file written with --out) in the output,
                       with whether its full-precision importances are identical to this run's
                       (repeatable)

Platform matters: on 2026-10-23 the Linux runs (CPython 3.11.16 and 3.12.3) were identical, while the
Windows build of the same xgboost 2.0.3 fitted a different model from the same seed (dry_season gain
0.281 vs 0.478). The freeze manifest records Linux, so the canonical file comes from Linux.

Importance is XGBoost's sklearn feature_importances_ (importance_type "gain", normalised to sum 1).
It describes what the fitted model relies on; it is not a causal or prospective claim.
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data/lassa/lassa-national-2026-27-freeze.json"
FORECAST_CODE = ROOT / "scripts/lassa/national-forecast-now.py"
CANONICAL_OUT = ROOT / "data/lassa/national-feature-importance.json"
SEASONAL = ["dry_season", "epi_week"]
REGENERATE = (
    "git show 1797d581b0755be317043137ee6230167aeb4f83:data/lassa/lassa_fever_timeseries_full.csv > /tmp/frozen.csv && "
    "uv venv --python 3.11.16 /tmp/lassa-fi && uv pip install --python /tmp/lassa-fi -r scripts/lassa/prospective-requirements.txt && "
    "/tmp/lassa-fi/bin/python scripts/lassa/national-feature-importance.py /tmp/frozen.csv"
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def environment():
    import numpy, sklearn, xgboost  # noqa: E401
    return {
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "scikit-learn": sklearn.__version__,
        "xgboost": xgboost.__version__,
    }


def fit_frozen_model(dataset):
    """Execute the frozen forecast code up to model.fit, in a directory holding only the snapshot."""
    src = FORECAST_CODE.read_text(encoding="utf-8")
    marker = "model.fit(X, y)\n"
    work = tempfile.mkdtemp(prefix="lassa-fi-")
    try:
        (Path(work) / "data/lassa").mkdir(parents=True)
        shutil.copyfile(dataset, Path(work) / "data/lassa/lassa_fever_timeseries_full.csv")
        cwd = os.getcwd()
        os.chdir(work)
        try:
            scope = {"__name__": "frozen_forecast_fit"}
            exec(compile(src[: src.index(marker) + len(marker)], str(FORECAST_CODE), "exec"), scope)
        finally:
            os.chdir(cwd)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return scope


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    ap.add_argument("--out")
    ap.add_argument("--cross-check", action="append", default=[])
    args = ap.parse_args()

    dataset = Path(args.dataset).resolve()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha256(dataset) != manifest["hashes"]["dataset_sha256"]:
        raise SystemExit("REFUSING: dataset SHA-256 does not match the freeze manifest's dataset_sha256")
    if sha256(FORECAST_CODE) != manifest["hashes"]["forecast_code_sha256"]:
        raise SystemExit("REFUSING: forecast code SHA-256 does not match the freeze manifest's forecast_code_sha256")

    env = environment()
    lock = manifest["environment_contract"]
    in_lock = (env["python"] == lock["python"] and env["python_implementation"] == lock["python_implementation"]
               and all(env[k] == v for k, v in lock["packages"].items()))
    out_path = Path(args.out).resolve() if args.out else CANONICAL_OUT
    if out_path == CANONICAL_OUT and not in_lock:
        raise SystemExit(f"REFUSING to write the canonical file outside the freeze environment lock: {env}")

    scope = fit_frozen_model(dataset)
    model, feats = scope["model"], scope["FEATS"]
    gain = {f: float(v) for f, v in zip(feats, model.feature_importances_)}
    ranked = sorted(gain.items(), key=lambda kv: -kv[1])
    seasonal = sum(gain[f] for f in SEASONAL)

    run = {"environment": env, "within_freeze_environment_lock": in_lock,
           "importance_raw": {f: v for f, v in ranked}}
    cross_checks = []
    for path in args.cross_check:
        other = json.loads(Path(path).read_text(encoding="utf-8"))["run"]
        cross_checks.append({
            "environment": other["environment"],
            "within_freeze_environment_lock": other["within_freeze_environment_lock"],
            "identical_full_precision_importances": other["importance_raw"] == run["importance_raw"],
            "max_abs_difference": max(abs(other["importance_raw"][f] - gain[f]) for f in feats),
        })

    out = {
        "schema_version": "gaialab.lassa-national-feature-importance.v1",
        "study_id": manifest["study_id"],
        "model_version": manifest["model_contract"]["model_version"],
        "description": "Gain importance of the frozen v1.1 national model fitted on every labelled week of the frozen dataset. Describes what the fitted model relies on; not a causal or prospective claim.",
        "importance_type": "gain",
        "normalized": True,
        "training": {
            "labelled_weeks": int(len(scope["y"])),
            "data_through": {"epi_year": scope["year"][-1], "epi_week": scope["week"][-1]},
        },
        "provenance": {
            "dataset_sha256": manifest["hashes"]["dataset_sha256"],
            "forecast_code_sha256": manifest["hashes"]["forecast_code_sha256"],
            "freeze_commit_sha": manifest["git"]["commit_sha"],
            "script": "scripts/lassa/national-feature-importance.py",
            "environment": env,
            "within_freeze_environment_lock": in_lock,
            "regenerate": REGENERATE,
            "cross_checks": cross_checks,
        },
        "features": [{"feature": f, "importance": round(v, 4)} for f, v in ranked],
        "grouped": {
            "seasonal": {"features": SEASONAL, "importance": round(seasonal, 4)},
            "case_history": {"features": [f for f in feats if f not in SEASONAL], "importance": round(1 - seasonal, 4)},
        },
        "run": run,
    }
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}: top {ranked[0][0]} {ranked[0][1]:.4f}; seasonal {seasonal:.4f}; in lock: {in_lock}")


if __name__ == "__main__":
    main()
