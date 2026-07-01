#!/usr/bin/env python3
"""TOPSIS and fuzzy-AHP cross-check at the survey year."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from dtahp import baselines, dataio
if __name__ == "__main__":
    ALT, STK = dataio.load_matrices()
    baselines.run(ALT, STK)
