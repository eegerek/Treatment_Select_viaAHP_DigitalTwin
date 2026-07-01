"""
Load the elicited pairwise-comparison matrices.

The pipeline reads them from ``inputs/interview_data.py``. That file is not part
of the repository (it holds your own study data); if it is absent, the bundled
``inputs/interview_data.example.py`` is used instead and a notice is printed, so
a fresh checkout runs end-to-end on the synthetic template.

Each input file must define two dictionaries:
    ALT  -- criterion name -> 3x3 matrix over (MBR, EC, CW)
    STK  -- stakeholder key -> 6x6 matrix over the six criteria
"""
import importlib.util

import numpy as np

from .config import INPUTS_DIR, CRITERIA, STAKEHOLDERS


def _load_module(path):
    spec = importlib.util.spec_from_file_location("interview_data", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_matrices(verbose=True):
    """Return (ALT, STK) with every matrix as a float numpy array."""
    user_file = INPUTS_DIR / "interview_data.py"
    example_file = INPUTS_DIR / "interview_data.example.py"

    if user_file.exists():
        source = user_file
    elif example_file.exists():
        source = example_file
        if verbose:
            print("[inputs] interview_data.py not found -- using the synthetic "
                  "template (inputs/interview_data.example.py).")
            print("[inputs] Copy it to inputs/interview_data.py and replace the "
                  "matrices with your own elicited judgements.")
    else:
        raise FileNotFoundError(
            "no interview data found in inputs/ (expected interview_data.py "
            "or interview_data.example.py)")

    mod = _load_module(source)
    ALT = {c: np.array(mod.ALT[c], dtype=float) for c in CRITERIA}
    STK = {s: np.array(mod.STK[s], dtype=float) for s in STAKEHOLDERS}
    return ALT, STK
