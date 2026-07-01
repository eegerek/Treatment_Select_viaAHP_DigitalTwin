#!/usr/bin/env python3
"""
Demonstrate building a group comparison matrix from raw per-respondent
judgements (geometric-mean aggregation with consistency screening).

Replace the demo rows with your interview data: one row per respondent, each
row being the upper-triangular Saaty judgements in the documented pair order.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from dtahp import interviews

if __name__ == "__main__":
    # Example: 5 respondents comparing 3 alternatives (pairs: (1,2)(1,3)(2,3)).
    demo = [[9, 5, 1/3],
            [7, 5, 1/2],
            [9, 4, 1/3],
            [8, 6, 1/4],
            [9, 5, 1/3]]
    print("Alternatives under one criterion (demo rows -- replace with your data):")
    interviews.report_group(demo, n=3, names=["MBR", "EC", "CW"])
