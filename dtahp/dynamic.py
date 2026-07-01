"""
Dynamic engine: roll the AHP forward under the driver forecasts, then summarise
stability with a Markov chain over the winning alternative and a resilience
index R_X(T) = probability that X stays top through every epoch to horizon T.
"""
import numpy as np

from .config import CRITERIA, METHODS, STAKEHOLDERS, SURVEY_YEAR, HORIZON_END
from . import ahp, mapping


def _criteria_weights(STK):
    return {s: ahp.priority(STK[s])[0] for s in STAKEHOLDERS}


def scores_at(model, ALT, crit_w, t, slope=None):
    """Per-stakeholder and consolidated scores at year t."""
    alt_w, max_cr = {}, 0.0
    for c in CRITERIA:
        w, cr = ahp.priority(mapping.matrix_at(ALT[c], model, c, t, slope))
        alt_w[c] = w
        max_cr = max(max_cr, cr)
    W = np.array([alt_w[c] for c in CRITERIA])                 # crit x alt
    per = {s: crit_w[s] @ W for s in STAKEHOLDERS}
    consolidated = np.prod(np.array(list(per.values())), axis=0) ** (1.0 / len(STAKEHOLDERS))
    return per, consolidated, max_cr


def trajectory(model, ALT, STK, years=None):
    years = years if years is not None else np.arange(SURVEY_YEAR, HORIZON_END + 1)
    crit_w = _criteria_weights(STK)
    rows, winners = [], []
    for t in years:
        _, cons, _ = scores_at(model, ALT, crit_w, t)
        rows.append(cons)
        winners.append(METHODS[int(np.argmax(cons))])
    return years, np.array(rows), winners


def markov_matrix(model, ALT, STK, years=None, n_samples=4000, seed=7):
    """Estimate the annual transition matrix over winner states by Monte Carlo."""
    years = years if years is not None else np.arange(SURVEY_YEAR, HORIZON_END + 1)
    crit_w = _criteria_weights(STK)
    rng = np.random.default_rng(seed)
    slopes = rng.normal(model.energy_slope_mean, model.energy_slope_sd, n_samples)
    idx = {m: k for k, m in enumerate(METHODS)}
    P = np.zeros((3, 3))
    for sl in slopes:
        prev = None
        for t in years:
            _, cons, _ = scores_at(model, ALT, crit_w, t, sl)
            w = METHODS[int(np.argmax(cons))]
            if prev is not None:
                P[idx[prev], idx[w]] += 1
            prev = w
    P = P / np.maximum(P.sum(axis=1, keepdims=True), 1)
    return P


def resilience(model, ALT, STK, method, horizon, n_samples=4000, seed=11, slope_sd=None):
    """R_X(T): probability that ``method`` stays the winner through the horizon."""
    crit_w = _criteria_weights(STK)
    rng = np.random.default_rng(seed)
    sd = model.energy_slope_sd if slope_sd is None else slope_sd
    slopes = rng.normal(model.energy_slope_mean, sd, n_samples)
    stays = 0
    for sl in slopes:
        ok = True
        for t in range(SURVEY_YEAR + 1, SURVEY_YEAR + horizon + 1):
            _, cons, _ = scores_at(model, ALT, crit_w, t, sl)
            if METHODS[int(np.argmax(cons))] != method:
                ok = False
                break
        stays += ok
    R = stays / n_samples
    se = np.sqrt(R * (1 - R) / n_samples)
    return R, se


def run(model, ALT, STK, verbose=True, n_samples=3000):
    years, cons, winners = trajectory(model, ALT, STK)
    if verbose:
        print("\nyear   " + "".join(f"{m:>8s}" for m in METHODS) + "   winner")
        for t, row, w in zip(years, cons, winners):
            print(f"{int(t)}  " + "".join(f"{v:8.3f}" for v in row) + f"   {w}")
        flip = next((int(y) for y, w in zip(years, winners) if w != winners[0]), None)
        print(f"\n  consolidated crossover: "
              + (f"year {flip}" if flip else "none within the horizon"))

    P = markov_matrix(model, ALT, STK, n_samples=n_samples)
    if verbose:
        print("\nMarkov transition matrix over", METHODS)
        print(np.round(P, 3))

    if verbose:
        print("\nResilience index R_X(T)  [Monte Carlo, +/- s.e.]:")
        top = winners[0]
        for T in (5, 10, 15):
            R, se = resilience(model, ALT, STK, top, T, n_samples=n_samples)
            print(f"  T={T:2d} yr:  {top} {R:.3f} +/- {se:.3f}")
    return dict(years=years, consolidated=cons, winners=winners, markov=P)
