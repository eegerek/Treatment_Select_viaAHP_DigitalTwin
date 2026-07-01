#!/usr/bin/env python3
"""Time-varying AHP trajectory, Markov chain, and resilience index."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from dtahp import forecasting, dynamic, dataio
if __name__ == "__main__":
    ALT, STK = dataio.load_matrices()
    dynamic.run(forecasting.get_models(), ALT, STK)
