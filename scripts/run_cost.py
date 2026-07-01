#!/usr/bin/env python3
"""Monte-Carlo lifecycle-cost model + figure."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from dtahp import forecasting, cost
if __name__ == "__main__":
    cost.run(forecasting.get_models())
