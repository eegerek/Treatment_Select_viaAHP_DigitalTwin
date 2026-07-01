#!/usr/bin/env python3
"""Static AHP ranking + stakeholder disagreement heatmap."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from dtahp import static_analysis
if __name__ == "__main__":
    static_analysis.run()
