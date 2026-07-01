"""
Project paths and shared constants.

Everything that the rest of the package needs to locate files (data cache,
interview inputs, figure output) is resolved here relative to the repository
root, so the scripts run the same way regardless of the current directory.
"""
from pathlib import Path

# --- decision structure --------------------------------------------------
CRITERIA = ["Efficiency", "Cost", "Land", "Energy", "Chemical", "Odor"]
METHODS = ["MBR", "EC", "CW"]
STAKEHOLDERS = ["UP", "RW", "IO"]
STAKEHOLDER_LABELS = {
    "UP": "Urban Planners",
    "RW": "Residents & Workers",
    "IO": "Industry Operators",
}


# --- locations -----------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
INPUTS_DIR = ROOT / "inputs"
FIGURES_DIR = ROOT / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# --- temporal anchors ----------------------------------------------------
BASE_YEAR = 2014        # reference year for the price/index deflation
SURVEY_YEAR = 2025      # year the stakeholder survey is anchored to (t0)
HORIZON_END = 2040      # end of the routine planning horizon

# --- Saaty random-consistency index, RI[n] for an n x n matrix -----------
# (index 0 is a placeholder so that RI[n] reads naturally for n >= 1)
RANDOM_INDEX = [0.0, 0.0, 0.0, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49]

# World Bank indicator codes used by the data layer
WB_INDICATORS = {
    "cpi": "FP.CPI.TOTL.ZG",       # inflation, consumer prices (annual %)
    "urban": "SP.URB.TOTL.IN.ZS",  # urban population (% of total)
}
WB_COUNTRY = "TUR"
