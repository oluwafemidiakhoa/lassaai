# Verifying the LassaAI 2026–27 prospective study freeze

The study `lassa-national-forecast-2026-27-v1.1` (protocol v1.1) was frozen at **2026-09-23T03:12:45.920131+00:00**.
The freeze manifest, [`data/lassa/lassa-national-2026-27-freeze.json`](data/lassa/lassa-national-2026-27-freeze.json),
records the SHA-256 of eight frozen objects. This repository publishes all eight, **byte-identical**,
at the exact paths the manifest and the frozen scripts use, so anyone can recompute every hash.

The manifest's `git.commit_sha` (`1797d581b0755be317043137ee6230167aeb4f83`) refers to the development
repository where the freeze was generated; that commit is not in this repository. What makes the
freeze checkable here is that each published file hashes to the value the manifest recorded.

The freeze establishes prospective-study anteriority and integrity only. It does not establish forecast validity, clinical utility, causality, treatment efficacy, or public-health effectiveness.

## Read this first: what the 2026–27 study can deliver

**We expect the 2026–27 prospective study to end as inconclusive–underpowered, and we are saying so before the season starts.**

Whether a week can be forecast depends on when NCDC publishes it. The frozen forecast code sets the
four-week window to start the day after the last data week ends
(`scripts/lassa/national-forecast-now.py`: `window_start = last_end + timedelta(days=1)`), and protocol §5
excludes any week that could not be logged before its outcome window began. So a week is eligible only if
NCDC publishes its report **by the Sunday that week ends**. No evidence we hold shows NCDC publishing that
fast: our own collector timed the fastest release at **6–8 days** after the week ended, and an upload-time
measure across **36** weeks of 2026 ranged from **9 to 44 days** (median 17).

| Primary window 2026-W45 to 2027-W17 (26 ISO weeks) | Expected eligible windows |
|---|---|
| At the lag we measured (6 days, lower bound) | **0 of 26** |
| Best case (fastest value in any evidence: 6 days) | **0 of 26** |
| Worst case (slowest value in any evidence: 44 days) | **0 of 26** |

The protocol needs at least **10** scoreable weeks. An underpowered readout is a **pre-specified outcome**
of the protocol (§11: "reported specifically as inconclusive-underpowered and does not count as evidence
that the model failed"). It is **not evidence that the model failed**: it means the v1.1 design cannot be
scored at NCDC's publication speed. We will publish it as that, and we will not change v1.1 to rescue it.
A different forecast lead would be a new, separately versioned study.

The computation is in [`data/lassa/v1-1-eligibility-yield.json`](data/lassa/v1-1-eligibility-yield.json),
stated 2026-10-25; its `source` paths refer to the development repository, where the first-observation ledger lives. The window has 25 weeks if NCDC numbers 2026 with 52 weeks; the answer is the same.

## The eight frozen objects

| Manifest key | File in this repository | What it is | SHA-256 (from the manifest) |
|---|---|---|---|
| `dataset_sha256` | `data/lassa/lassa_fever_timeseries_full.csv` | Frozen national weekly NCDC series (snapshot used by the freeze) | `e34fb6c31dcd3ccd8aeacb16b09b34a053bceabcb478d767c6be4051a8c9c29e` |
| `forecast_code_sha256` | `scripts/lassa/national-forecast-now.py` | Forecast code | `947448afbfbcb123fe0a01c8cd18c67534481e9e491b8b8fc74abc5e958ce9f5` |
| `logger_code_sha256` | `scripts/lassa/national-forecast-logger.py` | Forecast logger | `3bcc092b1ca73c1b0aa8f557680c4d35541aa869839b4d6ea818d05c0fdb48a2` |
| `outcome_recorder_sha256` | `scripts/lassa/national-outcome-recorder.py` | Outcome recorder | `88a342ad059172e1ebb5333cad297ecbec7f3d9ef2122c529bfb31ec892d5db6` |
| `readout_code_sha256` | `scripts/lassa/prospective-readout.py` | Prospective readout | `6f04e4ef28eb72fb5b26b4cc2f5f0327c84672a324f7106f569b7a7db072b18a` |
| `protocol_sha256` | `docs/lassa/PROSPECTIVE_PROTOCOL_LASSA.md` | Protocol v1.1 | `22ee44e4f33b355a513484b89761bc914db4638c9e750c6832c3afaa6fc2c7e9` |
| `environment_lock_sha256` | `scripts/lassa/prospective-requirements.txt` | Environment lock (package pins) | `9f0994f577d301ff63465795c9754f174fd70f948ace8a2bc37ab291029cdafe` |
| `source_review_sha256` | `docs/lassa/PRE_FREEZE_SOURCE_REVIEW_2026-09-22.md` | Pre-freeze source review | `909d413a6b0f21ae4d9d0975424b4c543d0759d5b172a813e77a2ecfabf88896` |

## 1. Recompute the hashes

Clone a fresh copy (this repository's `.gitattributes` turns off line-ending conversion, so a
checkout on any operating system is byte-identical):

```bash
git clone https://github.com/oluwafemidiakhoa/lassaai.git
cd lassaai
```

**Linux** (`sha256sum`) or **macOS** (replace `sha256sum -c` with `shasum -a 256 -c`): save the
expected values, which are copied from the manifest, and check every file against them:

```bash
cat > freeze.sha256 <<'EOF'
e34fb6c31dcd3ccd8aeacb16b09b34a053bceabcb478d767c6be4051a8c9c29e  data/lassa/lassa_fever_timeseries_full.csv
947448afbfbcb123fe0a01c8cd18c67534481e9e491b8b8fc74abc5e958ce9f5  scripts/lassa/national-forecast-now.py
3bcc092b1ca73c1b0aa8f557680c4d35541aa869839b4d6ea818d05c0fdb48a2  scripts/lassa/national-forecast-logger.py
88a342ad059172e1ebb5333cad297ecbec7f3d9ef2122c529bfb31ec892d5db6  scripts/lassa/national-outcome-recorder.py
6f04e4ef28eb72fb5b26b4cc2f5f0327c84672a324f7106f569b7a7db072b18a  scripts/lassa/prospective-readout.py
22ee44e4f33b355a513484b89761bc914db4638c9e750c6832c3afaa6fc2c7e9  docs/lassa/PROSPECTIVE_PROTOCOL_LASSA.md
9f0994f577d301ff63465795c9754f174fd70f948ace8a2bc37ab291029cdafe  scripts/lassa/prospective-requirements.txt
909d413a6b0f21ae4d9d0975424b4c543d0759d5b172a813e77a2ecfabf88896  docs/lassa/PRE_FREEZE_SOURCE_REVIEW_2026-09-22.md
EOF
sha256sum -c freeze.sha256
```

Every line must end in `OK`.

**Any OS, straight from the manifest** (Python 3 standard library only):

```bash
python3 - <<'EOF'
import hashlib, json
m = json.load(open("data/lassa/lassa-national-2026-27-freeze.json", encoding="utf-8"))
files = {
    "dataset_sha256": "data/lassa/lassa_fever_timeseries_full.csv",
    "forecast_code_sha256": "scripts/lassa/national-forecast-now.py",
    "logger_code_sha256": "scripts/lassa/national-forecast-logger.py",
    "outcome_recorder_sha256": "scripts/lassa/national-outcome-recorder.py",
    "readout_code_sha256": "scripts/lassa/prospective-readout.py",
    "protocol_sha256": "docs/lassa/PROSPECTIVE_PROTOCOL_LASSA.md",
    "environment_lock_sha256": "scripts/lassa/prospective-requirements.txt",
    "source_review_sha256": "docs/lassa/PRE_FREEZE_SOURCE_REVIEW_2026-09-22.md",
}
bad = 0
for key, path in files.items():
    got = hashlib.sha256(open(path, "rb").read()).hexdigest()
    ok = got == m["hashes"][key]
    bad += not ok
    print(("OK      " if ok else "MISMATCH"), key, path, got)
print("all 8 match" if not bad else f"{bad} mismatch(es)")
EOF
```

**Windows PowerShell:**

```powershell
(Get-FileHash -Algorithm SHA256 'data/lassa/lassa_fever_timeseries_full.csv').Hash.ToLower()  # expect e34fb6c31dcd3ccd8aeacb16b09b34a053bceabcb478d767c6be4051a8c9c29e
(Get-FileHash -Algorithm SHA256 'scripts/lassa/national-forecast-now.py').Hash.ToLower()  # expect 947448afbfbcb123fe0a01c8cd18c67534481e9e491b8b8fc74abc5e958ce9f5
(Get-FileHash -Algorithm SHA256 'scripts/lassa/national-forecast-logger.py').Hash.ToLower()  # expect 3bcc092b1ca73c1b0aa8f557680c4d35541aa869839b4d6ea818d05c0fdb48a2
(Get-FileHash -Algorithm SHA256 'scripts/lassa/national-outcome-recorder.py').Hash.ToLower()  # expect 88a342ad059172e1ebb5333cad297ecbec7f3d9ef2122c529bfb31ec892d5db6
(Get-FileHash -Algorithm SHA256 'scripts/lassa/prospective-readout.py').Hash.ToLower()  # expect 6f04e4ef28eb72fb5b26b4cc2f5f0327c84672a324f7106f569b7a7db072b18a
(Get-FileHash -Algorithm SHA256 'docs/lassa/PROSPECTIVE_PROTOCOL_LASSA.md').Hash.ToLower()  # expect 22ee44e4f33b355a513484b89761bc914db4638c9e750c6832c3afaa6fc2c7e9
(Get-FileHash -Algorithm SHA256 'scripts/lassa/prospective-requirements.txt').Hash.ToLower()  # expect 9f0994f577d301ff63465795c9754f174fd70f948ace8a2bc37ab291029cdafe
(Get-FileHash -Algorithm SHA256 'docs/lassa/PRE_FREEZE_SOURCE_REVIEW_2026-09-22.md').Hash.ToLower()  # expect 909d413a6b0f21ae4d9d0975424b4c543d0759d5b172a813e77a2ecfabf88896
```

## 2. Recompute the feature importance shown on gailabai.com/lassa

[`data/lassa/national-feature-importance.json`](data/lassa/national-feature-importance.json) is the
gain importance of the frozen model, computed by
[`scripts/lassa/national-feature-importance.py`](scripts/lassa/national-feature-importance.py),
which executes the frozen forecast code on the frozen dataset. The script refuses to run unless both
hash to the manifest's values.

### Platform: results are reproducible only on Linux

- **Canonical environment:** Linux x86_64 (GitHub Actions ubuntu24), CPython 3.11.16, numpy 1.26.4, scikit-learn 1.4.2, xgboost 2.0.3
  (platform `Linux-6.17.0-1022-azure-x86_64-with-glibc2.39`; the freeze manifest records `Linux-6.17.0-1022-azure-x86_64-with-glibc2.39`).
  The prospective forecasts run on GitHub Actions `ubuntu-latest`, so the canonical file is produced there too.
- **Linux:** the computation reproduces exactly across Python 3.11 and 3.12.
- **Windows: it does not.** The Windows build of the same xgboost version fits a different model from the same seed
  (dry-season importance 28.1% vs 47.8%). That changes the **forecasts** too, not just the
  importances (checked on the frozen data: the final-week forecast probability differed), so results are only comparable within
  the canonical Linux environment.

Every run recorded in the file, with its source in this repository:

| Platform | Python | dry_season gain | vs canonical | Source run |
|---|---|---|---|---|
| Linux x86_64 (GitHub Actions ubuntu24) (canonical) | CPython 3.11.16 | 47.8% | n/a | `data/lassa/national-feature-importance.json` |
| Linux x86_64 (WSL2) | CPython 3.11.16 | 47.8% | identical | `data/lassa/feature-importance-runs/linux-wsl2-cpython-3.11.16.json` |
| Linux x86_64 (WSL2) | CPython 3.12.3 | 47.8% | identical | `data/lassa/feature-importance-runs/linux-wsl2-cpython-3.12.3.json` |
| Windows x86_64 | CPython 3.12.10 | 28.1% | different | `data/lassa/feature-importance-runs/windows-cpython-3.12.10.json` |

In this repository the dataset at `data/lassa/lassa_fever_timeseries_full.csv` *is* the frozen
snapshot, so pass it directly (requires [uv](https://docs.astral.sh/uv/)):

```bash
uv venv --python 3.11.16 /tmp/lassa-fi
uv pip install --python /tmp/lassa-fi -r scripts/lassa/prospective-requirements.txt
/tmp/lassa-fi/bin/python scripts/lassa/national-feature-importance.py \
    data/lassa/lassa_fever_timeseries_full.csv --out /tmp/fi-check.json
python3 -c "import json;a=json.load(open('data/lassa/national-feature-importance.json'))['run']['importance_raw'];b=json.load(open('/tmp/fi-check.json'))['run']['importance_raw'];print('identical' if a==b else 'DIFFERENT')"
```

Importance describes what the fitted model relies on; it is not a causal or prospective claim.
