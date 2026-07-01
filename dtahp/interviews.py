"""
Build group pairwise-comparison matrices from raw interview judgements.

Each respondent compares every pair of items on Saaty's 1-9 scale. Given one
row of upper-triangular judgements per respondent, this module screens each
respondent for consistency, drops those above CR = 0.10, and aggregates the
kept respondents by the *geometric* mean of their judgements (AIJ). The
geometric mean is the only aggregation that preserves reciprocity, so it is the
correct one; arithmetic averaging silently breaks it and is a common mistake.

An aggregation-of-individual-priorities (AIP) cross-check is also provided for
the case where respondents are distinct decision makers rather than one group.

The pair order for n items is the upper triangle read left-to-right, top-down:
    n = 3:  (1,2) (1,3) (2,3)
    n = 6:  (1,2) (1,3) (1,4) (1,5) (1,6) (2,3) (2,4) (2,5) (2,6)
            (3,4) (3,5) (3,6) (4,5) (4,6) (5,6)
"""
import numpy as np

from .ahp import priority


def build_reciprocal(upper, n):
    """Assemble a full reciprocal matrix from an upper-triangular vector."""
    A = np.eye(n)
    idx = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            A[i, j] = upper[idx]
            A[j, i] = 1.0 / upper[idx]
            idx += 1
    return A


def aggregate_group(judgements, n, cr_threshold=0.10):
    """Aggregate respondents by AIJ with per-respondent consistency screening.

    ``judgements`` is a (respondents x n(n-1)/2) array of upper-triangular Saaty
    values. Returns (group_matrix, weights, group_cr, individual_crs, kept_idx).
    """
    J = np.asarray(judgements, dtype=float)
    n_pairs = n * (n - 1) // 2
    if J.shape[1] != n_pairs:
        raise ValueError(f"each row needs n(n-1)/2 = {n_pairs} judgements")

    individual_cr = np.array([priority(build_reciprocal(row, n))[1] for row in J])
    kept = np.where(individual_cr <= cr_threshold)[0]
    if kept.size == 0:
        # nothing passed the screen; fall back to all rows but flag it
        print("  warning: no respondent met CR <= %.2f; keeping all" % cr_threshold)
        kept = np.arange(J.shape[0])

    group_upper = np.exp(np.mean(np.log(J[kept]), axis=0))   # geometric mean
    group_matrix = build_reciprocal(group_upper, n)
    w, group_cr = priority(group_matrix)
    return group_matrix, w, group_cr, individual_cr, kept


def aggregate_priorities(judgements, n):
    """AIP cross-check: geometric mean of each respondent's weight vector."""
    J = np.asarray(judgements, dtype=float)
    W = np.array([priority(build_reciprocal(row, n))[0] for row in J])
    geo = np.exp(np.mean(np.log(W), axis=0))
    return geo / geo.sum()


def report_group(judgements, n, names):
    """Print a short diagnostic for one set of interview rows."""
    A, w, cr, cr_ind, kept = aggregate_group(judgements, n)
    total = np.asarray(judgements).shape[0]
    print(f"  respondents: {total} total, {kept.size} kept, {total - kept.size} dropped")
    print("  individual CRs: " + " ".join(f"{c:.3f}" for c in cr_ind))
    print("  group weights (eigenvector):")
    for name, wi in zip(names, w):
        print(f"    {name:<12s} {wi:.4f}")
    verdict = "acceptable" if cr <= 0.10 else "TOO HIGH (>0.10)"
    print(f"  group CR = {cr:.3f}  ({verdict})")
    print("  AIP cross-check: " + " ".join(f"{x:.4f}" for x in aggregate_priorities(judgements, n)))
    return A, w, cr
