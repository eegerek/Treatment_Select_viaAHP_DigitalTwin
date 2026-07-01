#!/usr/bin/env python3
"""Stress scenarios (shocks and induced preference shifts) + figure."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from dtahp import forecasting, stress, dataio
if __name__ == "__main__":
    ALT, STK = dataio.load_matrices()
    stress.run(forecasting.get_models(), ALT, STK)
