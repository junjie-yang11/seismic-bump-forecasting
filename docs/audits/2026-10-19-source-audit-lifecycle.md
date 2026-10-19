# Source-audit lifecycle and environment-recording fix

Baseline: `6870417fada097a4ab1748a64a638cf7ff6f604a`, branch `main`, clean working tree. Implementation and checks ran in an isolated copy. Work branch: `fix/source-audit-lifecycle-20261019`.

## Changes

- `phase1/audit_source.py`: invalidate earlier success before source acquisition, then handle download, ZIP extraction, cache writes and comparison within the same error-recording invocation. Keep supplied-file and explicit-proxy entry points. Catch interruption as well as ordinary errors. The `_audit` comparison implementation and successful output schema are unchanged.
- `tests/test_source_audit.py`: add seven regressions covering failed downloads, invalid ZIPs, missing members, cache-write failure, interruption, downloaded/supplied success equivalence and explicit proxy use. Fixtures are synthetic unit inputs, not study results.
- `docs/REPRODUCING.md`: record the baseline environment immediately before fitting, using the same activated baseline environment in the reproduction checkout. Preserve the published environment record when only checking saved evidence.

## Actual execution

Windows x64, Python 3.12.14 with the existing research dependencies. No complete model fitting was performed. The real acquisition and environment smoke checks used separate output roots; neither overwrote the isolated evidence used for Quick Check or the original checkout.

| Invocation from isolated checkout | Actual outcome | Wall seconds |
| --- | --- | --- |
| `python -B -m unittest tests.test_source_audit -v` | All eight source-audit tests passed | 0.90 |
| `python -B ../source_probe/phase1/audit_source.py` | Real official UCI ZIP downloaded and audited; 2,584 original rows, 2,578 mirror rows, six duplicate occurrences removed, 170 positives retained | 1.87 |
| `python -B ../environment_probe/phase1/record_environment.py` | Separate environment record written for the actual Python 3.12.14 checking runtime; package capture completed | 1.54 |
| `python -B -m phase1.quick_check` | 91 shared tests and 12 decision tests passed; 233 local links and 274 Stage 2 Word items checked | 60.09 |

The probe scripts were byte-identical copies of the corresponding current repository scripts placed in separate output roots. Their paths above describe the actual launches, not new repository entry points. Reproduction users run the ordinary module commands in the guide.

Quick Check additionally passed Stage 1 evidence (8,169 checks), Stage 2 decisions/block arithmetic (63,809), decision accounting (13,036), formula reconstruction (10,342), grade comparisons (26,911), ranking replay (26,342; all 80,000 reranked contrasts), integrated report agreement (1,837) and ranking report agreement (139). All final commands exited zero.

The freshly downloaded source audit, row mapping and duplicate-record files match the retained baseline files byte-for-byte. AST comparison confirms the `_audit` transformation implementation is unchanged. Published `environment.txt`, all 74 original CSV files, model implementations, locked protocols, saved predictions, thresholds, result manifests, verification records and every manuscript/Word/PDF remain unchanged.

This fixes invocation status and documents environment capture; it does not claim a new baseline model run. The environment smoke check does not replace the published Python 3.7 model-run record. Reports were not regenerated because their inputs, calculations and generators were unchanged. Quick Check is saved-evidence validation, not complete model replay or a new PDF layout inspection. The source audit establishes the official-to-mirror transformation, not the accuracy of the original mine measurements.
