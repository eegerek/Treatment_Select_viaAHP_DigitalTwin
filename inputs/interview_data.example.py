# =====================================================================
#  EXAMPLE / TEMPLATE INTERVIEW DATA  --  SYNTHETIC PLACEHOLDER VALUES
# =====================================================================
#  The numbers below are NOT from any real study. They are synthetic,
#  internally consistent (CR < 0.02) pairwise judgements whose only job is
#  to let the pipeline run end-to-end on a fresh checkout.
#
#  >>> To use your own study: copy this file to  inputs/interview_data.py
#  >>> and replace every matrix with your own elicited judgements. <<<
#
#  If you collected raw per-respondent judgements rather than group matrices,
#  build the group matrices first with dtahp.interviews (see the README), then
#  paste the results here.
#
#  Conventions (must match the analysis):
#    * Alternatives are ordered   MBR, EC, CW.
#    * Criteria are ordered        Efficiency, Cost, Land, Energy, Chemical, Odor.
#    * Every matrix is reciprocal (a_ji = 1/a_ij) with a unit diagonal; Saaty's
#      1-9 scale. Entries may be written as fractions, e.g. 1/3.
# =====================================================================

# --- ALT: alternative comparisons under each criterion (3x3 over MBR, EC, CW) ---
ALT = {
    "Efficiency": [[1,   1/2, 1  ],
                   [2,   1,   2  ],
                   [1,   1/2, 1  ]],

    "Cost":       [[1,   2,   1/3],
                   [1/2, 1,   1/4],
                   [3,   4,   1  ]],

    "Land":       [[1,   1,   1/2],
                   [1,   1,   1/3],
                   [2,   3,   1  ]],

    "Energy":     [[1,   1,   4  ],
                   [1,   1,   3  ],
                   [1/4, 1/3, 1  ]],

    "Chemical":   [[1,   1/9, 1/3],
                   [9,   1,   4  ],
                   [3,   1/4, 1  ]],

    "Odor":       [[1,   7,   3  ],
                   [1/7, 1,   1/2],
                   [1/3, 2,   1  ]],
}

# --- STK: criteria comparisons for each stakeholder group (6x6 over the criteria) ---
#     UP = urban planners, RW = residents & workers, IO = industry operators.
STK = {
    "UP": [[1,   1/2, 1/5, 1,   1/2, 1/3],
           [2,   1,   1/4, 2,   1,   1/2],
           [5,   4,   1,   6,   3,   2  ],
           [1,   1/2, 1/6, 1,   1/2, 1/3],
           [2,   1,   1/3, 2,   1,   1/2],
           [3,   2,   1/2, 3,   2,   1  ]],

    "RW": [[1,   1,   1,   1/2, 1,   1/2],
           [1,   1,   1,   1/2, 1,   1/2],
           [1,   1,   1,   1/2, 1,   1/2],
           [2,   2,   2,   1,   2,   1  ],
           [1,   1,   1,   1/2, 1,   1/2],
           [2,   2,   2,   1,   2,   1  ]],

    "IO": [[1,   1,   1,   1/3, 2,   1/2],
           [1,   1,   1,   1/3, 2,   1/2],
           [1,   1,   1,   1/3, 2,   1/2],
           [3,   3,   3,   1,   6,   1  ],
           [1/2, 1/2, 1/2, 1/6, 1,   1/4],
           [2,   2,   2,   1,   4,   1  ]],
}
