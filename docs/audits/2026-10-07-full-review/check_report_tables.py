"""Compatibility entry for the Stage 2 report-table verifier.

The current implementation belongs to phase2/verify_report.py.
Retain this dated command for audit instructions and external callers.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from phase2.verify_report import main

if __name__ == '__main__':
    main()
