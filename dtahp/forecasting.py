"""
Trend forecasting for the drivers.

Energy is modelled as a log-linear trend fitted two ways: ordinary least
squares (point estimate and predictive interval) and a conjugate Bayesian
linear regression (Normal-Inverse-Gamma prior), whose posterior on the slope
is the object recursively updated as new data arrive and which yields usable
intervals even from a short series. Urbanisation is bounded, so a logistic
trend is used and selected by an honest out-of-sample back-test.

``get_models()`` returns a small object exposing ``energy_index(t, slope)`` and
``urban_share(t)`` plus the Bayesian slope posterior; the rest of the pipeline
depends only on that object.
"""
from dataclasses import dataclass

import numpy as np
from scipy import stats

from .config import BASE_YEAR, SURVEY_YEAR
from . import data_sources


# --------------------------------------------------------------------------
# ordinary least squares on a log-linear trend
# --------------------------------------------------------------------------
def ols_loglinear(series, t0=BASE_YEAR):
    years = np.array(sorted(series), dtype=float)
    y = np.log(np.array([series[int(t)] for t in years]))
    x = years - t0
    X = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    dof = len(x) - 2
    s2 = resid @ resid / dof if dof > 0 else np.nan
    XtX_inv = np.linalg.inv(X.T @ X)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - (resid @ resid) / ss_tot if ss_tot > 0 else np.nan
    return dict(beta=beta, s2=s2, XtX_inv=XtX_inv, dof=dof, r2=r2, t0=t0)


def ols_predict(fit, year, ci=0.95):
    xq = year - fit["t0"]
    mu = fit["beta"][0] + fit["beta"][1] * xq
    if fit["dof"] > 0:
        xv = np.array([1.0, xq])
        var_pred = fit["s2"] * (1 + xv @ fit["XtX_inv"] @ xv)
        half = stats.t.ppf(0.5 + ci / 2, fit["dof"]) * np.sqrt(var_pred)
    else:
        half = np.nan
    return np.exp(mu), np.exp(mu - half), np.exp(mu + half)


# --------------------------------------------------------------------------
# conjugate Bayesian linear regression
# --------------------------------------------------------------------------
def bayes_loglinear(series, t0=BASE_YEAR, prior_var=(100.0, 1.0), a0=2.0, b0=0.05):
    years = np.array(sorted(series), dtype=float)
    y = np.log(np.array([series[int(t)] for t in years]))
    X = np.column_stack([np.ones(len(years)), years - t0])
    V0_inv = np.linalg.inv(np.diag(prior_var))
    Vn = np.linalg.inv(V0_inv + X.T @ X)
    mn = Vn @ (X.T @ y)
    an = a0 + len(years) / 2
    bn = b0 + 0.5 * (y @ y - mn @ np.linalg.inv(Vn) @ mn)
    slope_sd = np.sqrt(bn / (an - 1) * Vn[1, 1])
    return dict(mn=mn, Vn=Vn, an=an, bn=bn, slope_sd=float(slope_sd), t0=t0)


def bayes_predict(fit, year, ci=0.95):
    xq = np.array([1.0, year - fit["t0"]])
    mu = xq @ fit["mn"]
    scale = np.sqrt(fit["bn"] / fit["an"] * (1 + xq @ fit["Vn"] @ xq))
    half = stats.t.ppf(0.5 + ci / 2, 2 * fit["an"]) * scale
    return np.exp(mu), np.exp(mu - half), np.exp(mu + half)


# --------------------------------------------------------------------------
# bounded (logistic) trend for a saturating share
# --------------------------------------------------------------------------
def _logit(p):
    return np.log(p / (1 - p))


def logistic_fit(series, t0=BASE_YEAR, ceiling=100.0):
    years = np.array(sorted(series), dtype=float)
    z = _logit(np.array([series[int(t)] for t in years]) / ceiling)
    X = np.column_stack([np.ones(len(years)), years - t0])
    beta, *_ = np.linalg.lstsq(X, z, rcond=None)
    return dict(beta=beta, t0=t0, ceiling=ceiling)


def logistic_predict(fit, year):
    z = fit["beta"][0] + fit["beta"][1] * (year - fit["t0"])
    return fit["ceiling"] / (1 + np.exp(-z))


def backtest_mae(series, train_end, ceiling=100.0):
    """Mean absolute error of the logistic vs log-linear trend on a hold-out."""
    train = {y: v for y, v in series.items() if y <= train_end}
    test = {y: v for y, v in series.items() if y > train_end}
    log_fit = ols_loglinear(train)
    logi_fit = logistic_fit(train, ceiling=ceiling)
    log_err = [ols_predict(log_fit, y)[0] - v for y, v in test.items()]
    logi_err = [logistic_predict(logi_fit, y) - v for y, v in test.items()]
    return dict(loglinear=float(np.mean(np.abs(log_err))),
                logistic=float(np.mean(np.abs(logi_err))))


# --------------------------------------------------------------------------
# shared driver model
# --------------------------------------------------------------------------
@dataclass
class DriverModel:
    energy_bayes: dict
    energy_ols: dict
    urban_logistic: dict
    drivers: dict
    base_year: int = BASE_YEAR
    survey_year: int = SURVEY_YEAR

    def energy_index(self, t, slope=None):
        b = self.energy_bayes["mn"][1] if slope is None else slope
        return np.exp(self.energy_bayes["mn"][0] + b * (t - self.base_year))

    def urban_share(self, t):
        return logistic_predict(self.urban_logistic, t)

    @property
    def energy_slope_mean(self):
        return float(self.energy_bayes["mn"][1])

    @property
    def energy_slope_sd(self):
        return float(self.energy_bayes["slope_sd"])


def get_models(verbose=True):
    """Fetch drivers and fit all trend models; returns a DriverModel."""
    drivers = data_sources.get_drivers(verbose=verbose)
    return DriverModel(
        energy_bayes=bayes_loglinear(drivers["elec_real"]),
        energy_ols=ols_loglinear(drivers["elec_real"]),
        urban_logistic=logistic_fit(drivers["urban"]),
        drivers=drivers,
    )


def save_forecast_figure(model, path=None):
    """Two-panel figure: real energy index (Bayesian band) and urbanisation."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from .config import FIGURES_DIR

    NAVY, BLUE, ACC = "#16324f", "#2f6f9f", "#c0392b"
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": NAVY, "axes.labelcolor": NAVY,
                         "axes.titlecolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY})
    path = path or (FIGURES_DIR / "forecast_fits.png")
    elec = model.drivers["elec_real"]
    urban = model.drivers["urban"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 3.7))

    # (a) energy with Bayesian trend + 95% predictive band
    yrs = np.arange(BASE_YEAR, 2041)
    mean = np.array([bayes_predict(model.energy_bayes, y)[0] for y in yrs])
    lo = np.array([bayes_predict(model.energy_bayes, y)[1] for y in yrs])
    hi = np.array([bayes_predict(model.energy_bayes, y)[2] for y in yrs])
    ax1.fill_between(yrs, lo, hi, color=BLUE, alpha=0.18, label="95% posterior pred.")
    ax1.plot(yrs, mean, color=BLUE, lw=2, label="Bayesian trend")
    ax1.scatter(sorted(elec), [elec[y] for y in sorted(elec)], color=ACC, zorder=5,
                label="TUIK/EPDK anchors (real)")
    ax1.set_title("(a) Real industrial electricity price index")
    ax1.set_xlabel("Year"); ax1.set_ylabel(f"Index ({BASE_YEAR} = 1)")
    ax1.legend(frameon=False, fontsize=7.5, loc="upper left")

    # (b) urbanisation: full logistic vs trained-to-2018
    yrs2 = np.arange(2000, 2041)
    full = model.urban_logistic
    trained = logistic_fit({y: v for y, v in urban.items() if y <= 2018})
    ax2.plot(yrs2, [logistic_predict(full, y) for y in yrs2], color=BLUE, lw=2,
             label="logistic trend (full)")
    ax2.plot(yrs2, [logistic_predict(trained, y) for y in yrs2], color=ACC, lw=1.5,
             ls="--", label="trained on 2000-2018")
    tr = {y: v for y, v in urban.items() if y <= 2018}
    te = {y: v for y, v in urban.items() if y > 2018}
    ax2.scatter(sorted(tr), [tr[y] for y in sorted(tr)], color=NAVY, s=18, label="WB data (train)")
    ax2.scatter(sorted(te), [te[y] for y in sorted(te)], facecolors="none",
                edgecolors=ACC, s=28, label="WB data (held-out)")
    ax2.set_title("(b) Urbanization, % of total (WB WDI)")
    ax2.set_xlabel("Year"); ax2.set_ylabel("Urban population (%)")
    ax2.legend(frameon=False, fontsize=7.5, loc="lower right")

    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path
