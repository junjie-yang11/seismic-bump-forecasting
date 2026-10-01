# Data sources and version audit

Raw data files are excluded from Git. `src/data.py` downloads the 2,578-row CSV mirror when experiments run:
https://raw.githubusercontent.com/datasets/seismic-bumps/main/data/seismic-bumps.csv

The original 2,584-row UCI ARFF is available at:
https://archive.ics.uci.edu/static/public/266/seismic+bumps.zip
Dataset description and citation:
https://archive.ics.uci.edu/dataset/266/seismic+bumps

The mirror preparation documents repeated-row removal:
https://github.com/datasets/seismic-bumps

A direct audit on 2 October 2026 confirms that removing exact duplicate rows and keeping the first occurrence reproduces the local mirror without reordering. Six removed rows are class 0; no positive record is removed. Original data-row IDs are 90, 91, 973, 974, 1018 and 1019 (one-based, excluding headers).

Run `python audit_source.py` after downloading the mirror, or `python audit_source.py --source PATH_TO_ORIGINAL_ARFF`. Outputs include SHA-256 hashes, full duplicate contents and the row mapping in `results/source_*`. The original cache created by the audit is excluded from Git.

The audit confirms a transformation, not that identical readings were invalid shifts. Results use the mirror version and are not full-original-data baselines. Explicit timestamps and wall IDs are unavailable, so order-preserving deduplication does not confirm chronological ordering.
