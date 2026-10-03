# Verify the published evidence

Use this entry to check the saved predictions, decision counts, formulas and manuscript agreement before undertaking full reproduction. It fits no complete research model and keeps the checkout's published sources, evidence and reports unchanged. Existing verifiers run in a disposable copy because some write verification records.

## Environment and command

Clone or download the complete repository, including `results/` and `reports/`. Use Python 3.12 and install the research dependencies in a virtual environment. These are the same dependencies used for complete checks; Word and document-authoring packages are not required for this entry.

```text
python -m venv .venv-check
```

Activate `.venv-check` using `.venv-check\Scripts\Activate.ps1` on Windows PowerShell, or `source .venv-check/bin/activate` on Linux/macOS. Run from the repository root:

```text
python -m pip install -r requirements/requirements-research.txt
python -B -m phase1.quick_check
```

The only data download is the public CSV mirror when `data/seismic-bumps.csv` is absent. In that case it is downloaded into the disposable copy and checked against the recorded data/evidence. An existing local mirror is copied and checked. The quick entry does not fetch the official ARFF again; [complete reproduction](REPRODUCING.md) performs the original-to-mirror source audit.

If your network requires an HTTPS proxy, supply its actual local address:

```text
python -B -m phase1.quick_check --proxy http://127.0.0.1:PORT
```

Replace `PORT` with your proxy's port. No proxy address is required or stored by default. Temporary outputs disappear when the command exits.

## What is checked

| Check | Existing code used | Scope |
| --- | --- | --- |
| Behavioral regression tests | `tests/`, `phase2/tests.py` | Inputs, folds, ties, extreme rules, thresholds and decision accounting |
| Stage 1 | `phase1/verify_results.py --reports` | Saved predictions, metrics, cohorts, calibration, research evidence and Word/Markdown agreement |
| Stage 2 | `phase2/verify.py` | Saved references, choices, decisions, losses, capacity and all paired block replicates; source hashes |
| Supplement | `phase2/verify_supplement.py` | No-alarm reasons and value, finite/extreme rules, capacity contrasts and frozen scenarios |
| Formulas | `phase1/verify_formulae.py` | Independent arithmetic reconstruction from saved row-level evidence |
| Navigation and documents | `phase1/quick_check.py` | Current local file/image links, Stage 2 generator/input hashes, Word/Markdown text and tables, PDF file headers |

Success ends with `QUICK CHECK PASSED`, a measured elapsed time and a statement that published sources/results/reports were preserved. Any failed check exits with a nonzero status. A terminal success line is not a stored certification for later file edits.

For this edition, the command completed in **50.35 seconds** on the review machine with the mirror already cached. This excludes dependency installation and is an observed runtime, not a time limit or a promise for other machines. The saved-evidence block calculations account for most of that run. The clean-checkout check also exercises the mirror download; its measured duration is recorded in the release review.

This entry checks recorded evidence; it does not replay the complete fitted research models, establish independent field validity or inspect PDF layout. Full model fitting and `--replay` checks are in [REPRODUCING.md](REPRODUCING.md). The current release's actual run timings and document review are recorded in [the release review](audits/RESEARCH_PRESENTATION_REVIEW.md).
