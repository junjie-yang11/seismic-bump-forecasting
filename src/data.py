"""
Data loading, encoding and integrity checks for the UCI Seismic Bumps dataset.

Dataset
-------
Sikora M., Wrobel L. (2010). Application of rule induction algorithms for analysis
of data collected by seismic hazard monitoring systems in coal mines.
Archives of Mining Sciences 55(1), 91-114.

2,584 shift records (8 h each) from two longwalls of a Polish coal mine.
Target `class = 1` means a seismic bump with energy > 1e4 J occurred during the
NEXT shift. Class 1 accounts for ~6.6 % of records.
"""
from __future__ import annotations

import os
import urllib.request

import numpy as np
import pandas as pd
from input_checks import supervised_arrays

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(HERE), "data")
CSV_PATH = os.path.join(DATA_DIR, "seismic-bumps.csv")

# Mirror of the UCI data (csv, duplicates removed by the mirror).
MIRROR_URL = ("https://raw.githubusercontent.com/datasets/seismic-bumps/"
              "main/data/seismic-bumps.csv")
UCI_URL = ("https://archive.ics.uci.edu/ml/machine-learning-databases/"
           "00266/seismic-bumps.arff")

CATEGORICAL = {
    "seismic": "abcd",          # a = no hazard ... d = danger state
    "seismoacoustic": "abcd",
    "shift": "NW",              # N = preparation shift, W = coal-getting shift
    "ghazard": "abcd",
}

# `nbumps` is the total count; nbumps2..nbumps89 are the same bumps split into
# energy bins, so the columns are linearly dependent. See integrity_report().
REDUNDANT = ["nbumps"]


def download(force: bool = False) -> str:
    """Fetch the dataset into data/ if it is not already there."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(CSV_PATH) and not force:
        return CSV_PATH
    with urllib.request.urlopen(MIRROR_URL, timeout=60) as r:
        payload = r.read()
    with open(CSV_PATH, "wb") as f:
        f.write(payload)
    return CSV_PATH


def integrity_report(df: pd.DataFrame) -> dict:
    """Checks a reader should run before trusting any result."""
    bump_cols = [c for c in df.columns if c.startswith("nbumps") and c != "nbumps"]
    constant = [c for c in df.columns if df[c].nunique() <= 1]
    rep = {
        "n_rows": int(len(df)),
        "n_cols": int(df.shape[1]),
        "n_positive": int((df["class"] == 1).sum()),
        "prevalence": float((df["class"] == 1).mean()),
        "duplicate_rows": int(df.duplicated().sum()),
        "constant_columns": constant,
        "nbumps_range_rank": int(np.linalg.matrix_rank(df[bump_cols].to_numpy(float))),
        "nbumps_range_ncols": len(bump_cols),
    }
    # Describe prevalence variation; it does not isolate the cause of a
    # random-versus-record-order validation difference.
    q = pd.qcut(np.arange(len(df)), 5, labels=False)
    rep["prevalence_by_quintile"] = (
        df.groupby(q)["class"].mean().round(4).to_dict())
    return rep


def load(force_download: bool = False):
    """Return (X, y, feature_names, dataframe).

    X is float64 with categorical fields ordinally encoded; y is 0/1.
    nbumps is dropped; constant columns remain, so full rank is not guaranteed.
    """
    path = download(force_download)
    df = pd.read_csv(path)

    y = df["class"].to_numpy(dtype=float)

    features = [c for c in df.columns if c != "class" and c not in REDUNDANT]
    X = pd.DataFrame(index=df.index)
    for c in features:
        if c in CATEGORICAL:
            mapping = {ch: i for i, ch in enumerate(CATEGORICAL[c])}
            unknown = set(df[c].unique()) - set(mapping)
            if unknown:
                raise ValueError(f"unexpected category in {c}: {unknown}")
            X[c] = df[c].map(mapping).astype(float)
        else:
            X[c] = df[c].astype(float)

    integrity_report(df)  # available to callers that want it
    design, y = supervised_arrays(X.to_numpy(float), y)
    return design, y, list(X.columns), df
