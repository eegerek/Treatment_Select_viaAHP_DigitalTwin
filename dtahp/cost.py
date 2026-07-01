"""
Transparent lifecycle-cost model. Net present cost of ownership for each
technology over a horizon, with the real energy-price path from the forecasts,
literature-based unit-cost ranges, and a Monte Carlo over every uncertain input.

The unit-cost ranges are engineering literature values (see the manuscript
bibliography), independent of the interview data. Adjust them in COST_RANGES for
a different setting.
"""
import numpy as np

from .config import FIGURES_DIR, SURVEY_YEAR

# capacity and finance
CAPACITY = 100.0        # m3/day (decentralised neighbourhood scale)
HORIZON = 20            # years
DISCOUNT = 0.10         # real discount rate
DAYS = 365.0

# literature unit-cost ranges (uniform priors)
COST_RANGES = {
    "capex":  {"MBR": (800, 1500), "EC": (300, 800), "CW": (100, 400)},   # USD/(m3/d)
    "energy": {"MBR": (0.8, 1.6),  "EC": (1.0, 3.0), "CW": (0.01, 0.05)}, # kWh/m3
    "other":  {"MBR": (0.05, 0.15),"EC": (0.15, 0.35),"CW": (0.01, 0.05)},# USD/m3 non-energy
    "land":   {"MBR": (0.1, 0.3),  "EC": (0.2, 0.4), "CW": (2.0, 5.0)},   # m2/(m3/d)
}
LAND_PRICE = (50, 200)       # USD/m2
ELEC_2025 = (0.09, 0.13)     # USD/kWh
MEMBRANE_UPLIFT = {"MBR": 1.11, "EC": 1.0, "CW": 1.0}   # membrane replacement OPEX


def run(model, n_samples=40000, seed=11, save_fig=True, verbose=True):
    rng = np.random.default_rng(seed)
    U = lambda lo, hi: rng.uniform(lo, hi, n_samples)
    R = COST_RANGES

    capex = {t: U(*R["capex"][t]) for t in ("MBR", "EC", "CW")}
    energy = {t: U(*R["energy"][t]) for t in ("MBR", "EC", "CW")}
    other = {t: U(*R["other"][t]) for t in ("MBR", "EC", "CW")}
    land = {t: U(*R["land"][t]) for t in ("MBR", "EC", "CW")}
    land_price = U(*LAND_PRICE)
    elec0 = U(*ELEC_2025)
    slopes = rng.normal(model.energy_slope_mean, model.energy_slope_sd, n_samples)
    e_2025 = model.energy_index(SURVEY_YEAR, slopes)

    def npv(t):
        cap = capex[t] * CAPACITY + land[t] * CAPACITY * land_price
        annual_energy_kwh = energy[t] * CAPACITY * DAYS
        annual_other = other[t] * CAPACITY * DAYS
        total = cap.copy()
        for k in range(1, HORIZON + 1):
            price = elec0 * model.energy_index(SURVEY_YEAR + k, slopes) / e_2025
            opex = (annual_energy_kwh * price + annual_other) * MEMBRANE_UPLIFT[t]
            total += opex / (1 + DISCOUNT) ** k
        return total

    NPV = {t: npv(t) for t in ("MBR", "EC", "CW")}
    gap_mbr = (NPV["MBR"] - NPV["CW"]) / NPV["MBR"] * 100
    gap_ec = (NPV["EC"] - NPV["CW"]) / NPV["EC"] * 100

    if verbose:
        print(f"\nLifecycle NPV over {HORIZON} yr (Q={CAPACITY:.0f} m3/d, "
              f"r={DISCOUNT:.0%}), USD -- median [5%, 95%]:")
        for t in ("MBR", "EC", "CW"):
            q = np.percentile(NPV[t], [5, 50, 95])
            print(f"  {t}:  {q[1]:9,.0f}   [{q[0]:9,.0f}, {q[2]:9,.0f}]")
        print(f"\nCW saving vs MBR: median {np.median(gap_mbr):.1f}% "
              f"(90% of runs between {np.percentile(gap_mbr, 5):.0f}% and "
              f"{np.percentile(gap_mbr, 95):.0f}%)")
        print(f"CW saving vs EC : median {np.median(gap_ec):.1f}%")
        p_cw = np.mean((NPV["CW"] < NPV["MBR"]) & (NPV["CW"] < NPV["EC"]))
        print(f"P(CW cheapest of the three) = {p_cw:.3f}")

    composition = _median_composition(model, capex, energy, other, land, land_price, elec0)
    if save_fig:
        path = _figure(NPV, composition)
        if verbose:
            print(f"[figure] {path.name}")
    return dict(npv=NPV, gap_vs_mbr=gap_mbr, gap_vs_ec=gap_ec, composition=composition)


def _median_composition(model, capex, energy, other, land, land_price, elec0):
    med = np.median
    comp = {}
    for t in ("MBR", "EC", "CW"):
        cap_eq = med(capex[t]) * CAPACITY
        cap_land = med(land[t]) * CAPACITY * med(land_price)
        en = ot = 0.0
        for k in range(1, HORIZON + 1):
            price = med(elec0) * model.energy_index(SURVEY_YEAR + k) / model.energy_index(SURVEY_YEAR)
            en += med(energy[t]) * CAPACITY * DAYS * price * MEMBRANE_UPLIFT[t] / (1 + DISCOUNT) ** k
            ot += med(other[t]) * CAPACITY * DAYS * MEMBRANE_UPLIFT[t] / (1 + DISCOUNT) ** k
        comp[t] = (cap_eq, cap_land, en, ot)
    return comp


def _figure(NPV, composition):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    NAVY, BLUE, ACC, GREEN, GREY = "#16324f", "#2f6f9f", "#c0392b", "#2e8b6f", "#9bb3c7"
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": NAVY, "axes.labelcolor": NAVY,
                         "axes.titlecolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY})
    meth = ["MBR", "EC", "CW"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.8, 3.6))

    data = [NPV[t] / 1e3 for t in meth]
    bp = ax1.boxplot(data, labels=meth, patch_artist=True, whis=(5, 95), showfliers=False)
    for patch, c in zip(bp["boxes"], [BLUE, ACC, GREEN]):
        patch.set_facecolor(c); patch.set_alpha(0.65)
    for med in bp["medians"]:
        med.set_color(NAVY)
    ax1.set_title("(a) 20-yr lifecycle cost (Monte Carlo)")
    ax1.set_ylabel("NPV of total cost (1000 USD)")

    labels = ["equip CAPEX", "land", "energy OPEX", "other OPEX"]
    cols = [NAVY, GREY, ACC, BLUE]
    vals = np.array([composition[t] for t in meth]) / 1e3
    bottom = np.zeros(3)
    for k in range(4):
        ax2.bar(meth, vals[:, k], bottom=bottom, color=cols[k], label=labels[k])
        bottom += vals[:, k]
    ax2.set_title("(b) cost composition (median)")
    ax2.set_ylabel("NPV (1000 USD)")
    ax2.legend(frameon=False, fontsize=7.5, loc="upper right")

    fig.tight_layout()
    path = FIGURES_DIR / "cost_analysis.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path
