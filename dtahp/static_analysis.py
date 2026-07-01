"""
Static AHP: the baseline ranking at the survey year, per stakeholder group and
consolidated, plus the inter-stakeholder disagreement heatmap.

The heatmap shows, for each pair of criteria, the variance of the log pairwise
judgement across the stakeholder groups -- a map of where the groups agree
(blue) and where they conflict (red).
"""
import numpy as np

from .config import CRITERIA, METHODS, STAKEHOLDERS, STAKEHOLDER_LABELS, FIGURES_DIR
from . import ahp, dataio

NAVY = "#16324f"


def compute(ALT, STK):
    W_alt, alt_cr = ahp.alternative_weights(ALT, CRITERIA)     # crit x alt
    W_crit, crit_cr = ahp.criteria_weights(STK, STAKEHOLDERS)   # crit x stakeholder
    scores = ahp.global_scores(W_alt, W_crit)                   # alt x stakeholder
    consolidated = ahp.consolidate(scores)
    return dict(W_alt=W_alt, W_crit=W_crit, alt_cr=alt_cr, crit_cr=crit_cr,
                scores=scores, consolidated=consolidated)


def disagreement_matrix(STK):
    """Variance of the log judgement across stakeholders, per criteria pair."""
    logs = np.log(np.array([STK[s] for s in STAKEHOLDERS]))     # stakeholders x 6 x 6
    V = logs.var(axis=0, ddof=1)
    np.fill_diagonal(V, 0.0)
    return V


def save_heatmap(STK, path=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    V = disagreement_matrix(STK)
    path = path or (FIGURES_DIR / "stakeholder_heatmap.png")
    fig, ax = plt.subplots(figsize=(6.6, 5.2))
    im = ax.imshow(V, cmap="coolwarm", vmin=0, vmax=V.max())
    ax.set_xticks(range(6)); ax.set_yticks(range(6))
    ax.set_xticklabels(CRITERIA, rotation=30, ha="right", fontsize=9, color=NAVY)
    ax.set_yticklabels(CRITERIA, fontsize=9, color=NAVY)
    hi = V.max()
    for i in range(6):
        for j in range(6):
            c = "white" if (V[i, j] > hi * 0.55 or V[i, j] < hi * 0.12) else NAVY
            ax.text(j, i, f"{V[i, j]:.2f}", ha="center", va="center",
                    fontsize=8.5, color=c)
    cb = fig.colorbar(im, ax=ax, shrink=0.85)
    cb.set_label("variance of log judgement across stakeholders", fontsize=8.5, color=NAVY)
    ax.set_title("Inter-stakeholder disagreement on pairwise criteria",
                 fontsize=10.5, color=NAVY)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def run(save_fig=True, verbose=True):
    ALT, STK = dataio.load_matrices(verbose=verbose)
    res = compute(ALT, STK)

    if verbose:
        print("\nAlternative priority weights per criterion (CR in brackets):")
        for i, c in enumerate(CRITERIA):
            w = res["W_alt"][i]
            print(f"  {c:<11s} " + "  ".join(f"{m} {w[k]:.3f}" for k, m in enumerate(METHODS))
                  + f"   [CR {res['alt_cr'][c]:.3f}]")
        print("\nStatic global scores (rows = alternatives):")
        header = "  " + " " * 22 + "".join(f"{m:>10s}" for m in METHODS)
        print(header)
        for s_idx, s in enumerate(STAKEHOLDERS):
            row = res["scores"][:, s_idx]
            print(f"  {STAKEHOLDER_LABELS[s]:<22s}" + "".join(f"{v:10.3f}" for v in row))
        print(f"  {'Consolidated':<22s}" + "".join(f"{v:10.3f}" for v in res["consolidated"]))
        winner = METHODS[int(np.argmax(res["consolidated"]))]
        print(f"\n  consolidated winner: {winner}")

    if save_fig:
        path = save_heatmap(STK)
        if verbose:
            print(f"[figure] {path.name}")
    return res
