"""
Core AHP algebra: priority weights, consistency ratio, and the two-level
consolidation across criteria and stakeholder groups.

This is a direct port of the MATLAB reference implementation (AHP.m): the
priority vector is the principal eigenvector of the pairwise-comparison matrix,
the consistency ratio is CI/RI with Saaty's random index, and the consolidated
ranking is the geometric mean of the per-stakeholder global scores.
"""
import numpy as np

from .config import RANDOM_INDEX


def priority(matrix):
    """Return (weights, consistency_ratio) for one pairwise-comparison matrix.

    Weights are the normalised principal eigenvector. For n <= 2 the matrix is
    trivially consistent and CR is defined as 0.
    """
    A = np.asarray(matrix, dtype=float)
    n = A.shape[0]
    eigvals, eigvecs = np.linalg.eig(A)
    k = int(np.argmax(eigvals.real))
    lambda_max = eigvals[k].real

    w = np.abs(eigvecs[:, k].real)   # eigenvectors are sign-ambiguous
    w = w / w.sum()

    if n <= 2:
        cr = 0.0
    else:
        ci = (lambda_max - n) / (n - 1)
        ri = RANDOM_INDEX[n] if n < len(RANDOM_INDEX) else RANDOM_INDEX[-1]
        cr = ci / ri if ri > 0 else ci
    return w, float(cr)


def is_consistent(cr, threshold=0.10):
    """Saaty's acceptance rule."""
    return cr <= threshold


def alternative_weights(alt_matrices, criteria):
    """Stack the per-criterion alternative weights into an (n_crit x n_alt) array.

    ``alt_matrices`` maps each criterion name to its alternative comparison
    matrix; ``criteria`` fixes the row order.
    """
    rows, crs = [], {}
    for c in criteria:
        w, cr = priority(alt_matrices[c])
        rows.append(w)
        crs[c] = cr
    return np.array(rows), crs


def criteria_weights(stakeholder_matrices, stakeholders):
    """Return an (n_crit x n_stakeholder) array of criteria weights plus CRs."""
    cols, crs = [], {}
    for s in stakeholders:
        w, cr = priority(stakeholder_matrices[s])
        cols.append(w)
        crs[s] = cr
    return np.array(cols).T, crs


def global_scores(W_alt, W_crit):
    """Global score matrix: (n_alt x n_stakeholder).

    ``W_alt`` is (n_crit x n_alt), ``W_crit`` is (n_crit x n_stakeholder);
    the product gives each alternative's score under each stakeholder group.
    """
    return W_alt.T @ W_crit


def consolidate(score_matrix):
    """Consolidate the per-stakeholder scores by the row-wise geometric mean.

    Returns weights normalised to sum to one (the consolidated priority of each
    alternative across all stakeholder groups).
    """
    geo = np.prod(score_matrix, axis=1) ** (1.0 / score_matrix.shape[1])
    return geo / geo.sum()
