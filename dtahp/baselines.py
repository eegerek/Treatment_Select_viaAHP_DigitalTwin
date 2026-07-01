"""
Cross-method baselines. Score the same alternatives at the survey year with
TOPSIS and Buckley fuzzy-AHP, to check that the ranking is not an artefact of
the AHP aggregation. All three use the same elicited matrices.
"""
import numpy as np

from .config import CRITERIA, METHODS, STAKEHOLDERS
from . import ahp

SAATY_GRID = np.array([1/9, 1/8, 1/7, 1/6, 1/5, 1/4, 1/3, 1/2, 1, 2, 3, 4, 5, 6, 7, 8, 9])


def mean_criteria_weights(STK):
    W = np.array([ahp.priority(STK[s])[0] for s in STAKEHOLDERS])
    wc = W.mean(axis=0)
    return wc / wc.sum()


def topsis(W_alt, wc):
    """TOPSIS closeness coefficients for benefit-type criteria."""
    D = W_alt.T                                      # alt x crit
    N = D / np.sqrt((D ** 2).sum(axis=0))
    V = N * wc
    ideal, anti = V.max(axis=0), V.min(axis=0)
    d_plus = np.sqrt(((V - ideal) ** 2).sum(axis=1))
    d_minus = np.sqrt(((V - anti) ** 2).sum(axis=1))
    return d_minus / (d_plus + d_minus)


def _fuzzify(a):
    i = int(np.argmin(np.abs(np.log(SAATY_GRID) - np.log(a))))
    lo = SAATY_GRID[max(i - 1, 0)]
    hi = SAATY_GRID[min(i + 1, len(SAATY_GRID) - 1)]
    return np.array([min(lo, a), a, max(hi, a)])


def buckley_weights(matrix):
    """Triangular fuzzy weights (Buckley geometric-mean method)."""
    M = np.asarray(matrix, dtype=float)
    n = M.shape[0]
    F = np.empty((n, n, 3))
    for i in range(n):
        for j in range(n):
            F[i, j] = _fuzzify(M[i, j]) if i != j else np.array([1.0, 1.0, 1.0])
    r = np.array([[np.prod(F[i, :, k]) ** (1 / n) for k in range(3)] for i in range(n)])
    s = r.sum(axis=0)
    w = np.array([[r[i, 0] / s[2], r[i, 1] / s[1], r[i, 2] / s[0]] for i in range(n)])
    crisp = w.mean(axis=1)
    return crisp / crisp.sum()


def run(ALT, STK, verbose=True):
    W_alt, _ = ahp.alternative_weights(ALT, CRITERIA)
    wc = mean_criteria_weights(STK)

    ahp_scores = wc @ W_alt
    topsis_scores = topsis(W_alt, wc)
    W_fuzzy = np.array([buckley_weights(ALT[c]) for c in CRITERIA])
    fuzzy_scores = wc @ W_fuzzy

    results = {"AHP (additive)": ahp_scores, "TOPSIS": topsis_scores,
               "Fuzzy-AHP (Buckley)": fuzzy_scores}
    if verbose:
        print("\nCross-method comparison at the survey year:")
        for name, sc in results.items():
            ranked = METHODS[int(np.argmax(sc))]
            print(f"  {name:<20s} " + "  ".join(f"{m} {sc[k]:.3f}"
                  for k, m in enumerate(METHODS)) + f"   -> {ranked}")
    return results
