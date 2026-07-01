"""
Stress testing. Push the drivers with shocks the central forecast cannot see
(an energy-price step, a carbon-price ramp) and, separately, let a shock induce
a shift in stakeholder priorities. Report how far each pulls forward the year in
which CW overtakes MBR, and plot the consolidated gap.

The point is the contrast: data-only shocks barely move the ranking, whereas a
shock-induced preference shift flips it quickly -- which is exactly why the
decision should be re-elicited, not inferred from indices.
"""
import numpy as np

from .config import CRITERIA, METHODS, STAKEHOLDERS, SURVEY_YEAR, FIGURES_DIR
from . import ahp, mapping

# Cost is criterion index 1, Energy is index 3 (the ones a crisis re-weights).
_COST_IDX, _ENERGY_IDX = 1, 3

SCENARIOS = {
    "Baseline (central forecast)": {},
    "S1 Energy shock only (+80%, 2028)": {"shock": (2028, 1.8)},
    "S2 Carbon price only (->+40% by 2035)": {"carbon": (0.40, 2035)},
    "S3 Energy crisis + induced reweighting (2028)": {"shock": (2028, 1.8), "pref": (1.4, 2028)},
    "S4 Severe compound (shock+carbon+reweight, 2027)":
        {"shock": (2027, 2.0), "carbon": (0.40, 2035), "pref": (1.5, 2027)},
}
_COLORS = {
    "Baseline (central forecast)": "#16324f",
    "S1 Energy shock only (+80%, 2028)": "#c0392b",
    "S2 Carbon price only (->+40% by 2035)": "#2e8b6f",
    "S3 Energy crisis + induced reweighting (2028)": "#b8860b",
    "S4 Severe compound (shock+carbon+reweight, 2027)": "#7d3c98",
}


def _energy_mult(model, t, scn):
    m = model.energy_index(t) / model.energy_index(SURVEY_YEAR)
    if scn.get("shock") and t >= scn["shock"][0]:
        m *= scn["shock"][1]
    if scn.get("carbon"):
        target, by = scn["carbon"]
        m *= 1 + target * np.clip((t - SURVEY_YEAR) / (by - SURVEY_YEAR), 0, 1.3)
    return m


def _criteria_weights(STK, scn, t):
    base = {s: ahp.priority(STK[s])[0] for s in STAKEHOLDERS}
    if scn.get("pref") and t >= scn["pref"][1]:
        factor = scn["pref"][0]
        out = {}
        for s, w in base.items():
            w = w.copy()
            w[_COST_IDX] *= factor
            w[_ENERGY_IDX] *= factor
            out[s] = w / w.sum()
        return out
    return base


def _consolidated(model, ALT, STK, t, scn):
    e_mult = _energy_mult(model, t, scn)
    u_mult = model.urban_share(t) / model.urban_share(SURVEY_YEAR)
    W = np.array([ahp.priority(mapping.matrix_at(ALT[c], model, c, t,
                  energy_mult=e_mult, urban_mult=u_mult))[0] for c in CRITERIA])
    cw = _criteria_weights(STK, scn, t)
    per = np.array([cw[s] @ W for s in STAKEHOLDERS])
    return np.prod(per, axis=0) ** (1.0 / len(STAKEHOLDERS))


def run(model, ALT, STK, years=None, save_fig=True, verbose=True):
    years = years if years is not None else np.arange(SURVEY_YEAR, 2051)
    mbr_i, cw_i = METHODS.index("MBR"), METHODS.index("CW")
    gaps, crossovers = {}, {}
    for name, scn in SCENARIOS.items():
        gap = np.array([(lambda c: c[cw_i] - c[mbr_i])(_consolidated(model, ALT, STK, t, scn))
                        for t in years])
        gaps[name] = gap
        crossovers[name] = next((int(y) for y, g in zip(years, gap) if g > 0), None)

    if verbose:
        print("\nscenario -> first year CW overtakes MBR (consolidated):")
        for name, yr in crossovers.items():
            print(f"  {name:<48s}: {yr if yr else '>' + str(int(years[-1]))}")

    if save_fig:
        path = _figure(years, gaps)
        if verbose:
            print(f"[figure] {path.name}")
    return dict(gaps=gaps, crossovers=crossovers, years=years)


def _figure(years, gaps):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    NAVY = "#16324f"
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": NAVY, "axes.labelcolor": NAVY,
                         "axes.titlecolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY})
    fig, ax = plt.subplots(figsize=(8.2, 4.0))
    for name, gap in gaps.items():
        ax.plot(years, gap, color=_COLORS[name], lw=2, label=name)
        cross = next((y for y, g in zip(years, gap) if g > 0), None)
        if cross:
            ax.scatter([cross], [0], color=_COLORS[name], zorder=5, s=30)
    ax.axhline(0, color="grey", lw=0.8, ls=":")
    ax.set_xlabel("Year")
    ax.set_ylabel(r"Consolidated gap  $S_{CW} - S_{MBR}$")
    ax.set_title("Stress testing: when does CW overtake MBR?")
    ax.annotate("CW overtakes MBR\n(gap > 0)", xy=(years[-5], 0.004), fontsize=8, color=NAVY)
    ax.legend(frameon=False, fontsize=7.3, loc="upper left")
    fig.tight_layout()
    path = FIGURES_DIR / "stress_scenarios.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path
