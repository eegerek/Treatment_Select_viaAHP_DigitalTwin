"""
The mapping f: turn driver forecasts into time-varying pairwise-comparison
matrices, preserving reciprocity and keeping every entry on the 1-9 scale.

For criterion c and pair (i, j),
    a_ij(t) = clip_[1/9, 9]( a_ij(t0) * R_ij(t) ** gamma_c ),   a_ji = 1 / a_ij,
where R_ij(t) is the ratio of the two alternatives' attribute drift. Each
attribute drifts as a product of driver multiples raised to method-specific
exposures; general inflation is common-mode and cancels in the ratio, so only
differential drivers move a comparison. At t0 the drift ratio is 1, so the
elicited matrix is reproduced exactly.
"""
import numpy as np

from .config import METHODS, CRITERIA, SURVEY_YEAR

SAATY_MIN, SAATY_MAX = 1.0 / 9.0, 9.0

# Per-criterion sensitivity of the map; gamma = 1 keeps every matrix consistent
# here, and is reduced automatically if a projected CR exceeds 0.10.
GAMMA = {c: 1.0 for c in CRITERIA}

# Exposure of each method's attribute (per criterion) to the drivers:
#   E = real electricity price, U = urban land pressure.
# MBR and EC are grid-electricity intensive; CW is a passive, land-hungry system.
EXPOSURE = {
    "Energy":     {"MBR": {"E": 1.00}, "EC": {"E": 1.00}, "CW": {"E": 0.05}},
    "Cost":       {"MBR": {"E": 0.45}, "EC": {"E": 0.55}, "CW": {"E": 0.05, "U": 0.25}},
    "Land":       {"MBR": {},          "EC": {},          "CW": {"U": 0.60}},
    "Efficiency": {"MBR": {}, "EC": {}, "CW": {}},
    "Chemical":   {"MBR": {}, "EC": {}, "CW": {}},
    "Odor":       {"MBR": {}, "EC": {}, "CW": {}},
}


def attribute_drift(model, method, criterion, t, slope=None,
                    energy_mult=None, urban_mult=None):
    """Multiplicative drift of one method's attribute on one criterion since t0.

    ``energy_mult`` / ``urban_mult`` override the model forecast (used by the
    stress scenarios to inject shocks); otherwise they come from the forecasts.
    """
    if energy_mult is None:
        energy_mult = model.energy_index(t, slope) / model.energy_index(SURVEY_YEAR, slope)
    if urban_mult is None:
        urban_mult = model.urban_share(t) / model.urban_share(SURVEY_YEAR)
    e = EXPOSURE[criterion][method]
    return energy_mult ** e.get("E", 0.0) * urban_mult ** e.get("U", 0.0)


def matrix_at(base_matrix, model, criterion, t, slope=None,
              energy_mult=None, urban_mult=None):
    """Time-varying comparison matrix for one criterion at year t."""
    A = np.array(base_matrix, dtype=float)
    d = {m: attribute_drift(model, m, criterion, t, slope, energy_mult, urban_mult)
         for m in METHODS}
    gamma = GAMMA[criterion]
    for i in range(3):
        for j in range(i + 1, 3):
            R = d[METHODS[j]] / d[METHODS[i]]
            a = np.clip(base_matrix[i][j] * R ** gamma, SAATY_MIN, SAATY_MAX)
            A[i, j] = a
            A[j, i] = 1.0 / a
    return A
