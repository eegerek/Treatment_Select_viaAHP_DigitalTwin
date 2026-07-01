"""
Quick sanity checks. Run with either:

    python -m pytest tests
    python tests/test_sanity.py
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import numpy as np

from dtahp import ahp, interviews, data_sources, dataio
from dtahp.config import CRITERIA, STAKEHOLDERS


def test_priority_perfectly_consistent():
    # a_ij = w_i / w_j is perfectly consistent -> CR ~ 0 and weights recovered
    w_true = np.array([0.5, 0.3, 0.2])
    A = np.outer(w_true, 1 / w_true)
    w, cr = ahp.priority(A)
    assert abs(cr) < 1e-8
    assert np.allclose(w, w_true, atol=1e-8)


def test_reciprocity_build():
    A = interviews.build_reciprocal([2, 4, 3], n=3)
    assert np.allclose(A * A.T, 1.0)
    assert np.allclose(np.diag(A), 1.0)


def test_geometric_mean_preserves_reciprocity():
    rows = [[9, 5, 1 / 3], [7, 5, 1 / 2], [8, 4, 1 / 3]]
    A, w, cr, *_ = interviews.aggregate_group(rows, n=3)
    assert np.allclose(A * A.T, 1.0)     # group matrix still reciprocal
    assert abs(w.sum() - 1.0) < 1e-9


def test_deflator_check():
    drivers = data_sources.get_drivers(verbose=False)
    level = drivers["cpi_level"]
    ratio = level[2022] / level[2014]
    assert abs(ratio - 3.999) < 0.02     # matches the World Bank/OECD level


def test_example_inputs_consistent():
    ALT, STK = dataio.load_matrices(verbose=False)
    for c in CRITERIA:
        assert ahp.priority(ALT[c])[1] <= 0.10, f"{c} inconsistent"
    for s in STAKEHOLDERS:
        assert ahp.priority(STK[s])[1] <= 0.10, f"{s} inconsistent"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} checks passed.")
