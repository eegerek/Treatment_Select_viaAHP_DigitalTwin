# Digital-Twin AHP for greywater treatment selection

A small, self-contained Python toolkit that keeps an Analytic Hierarchy Process
(AHP) technology-selection decision *current* from real macro-economic data. It
compares three greywater treatment technologies — membrane bioreactor (**MBR**),
electrocoagulation (**EC**) and constructed wetlands (**CW**) — across six
criteria (efficiency, cost, land, energy, chemical use, odour) for three
stakeholder groups, and then rolls the decision forward in time:

1. **Static AHP** — priority weights, consistency ratios, per-stakeholder and
   consolidated scores, and a heatmap of where stakeholders (dis)agree.
2. **Forecasting** — fetches the driver series (World Bank + national tariff),
   deflates them, and fits validated trend models (OLS, conjugate Bayesian,
   logistic) with out-of-sample back-testing.
3. **Dynamic engine** — maps the forecasts onto time-varying Saaty matrices,
   tracks the ranking to the horizon, and summarises stability with a Markov
   chain and a resilience index.
4. **Lifecycle cost** — a Monte-Carlo net-present-cost model with a real
   energy-price path.
5. **Baselines** — TOPSIS and fuzzy-AHP cross-checks.
6. **Stress testing** — plausible shocks and shock-induced preference shifts,
   and how far each pulls the decision forward.

This code accompanies the manuscript and is meant to be readable and re-runnable
by a reviewer, not just by us.

---

## Install

Python 3.9+.

```bash
git clone https://github.com/<your-account>/greywater-dtahp.git
cd greywater-dtahp
pip install -r requirements.txt
```

(Optional, to import `dtahp` from anywhere: `pip install -e .`)

## Run everything

```bash
python scripts/run_all.py
```

That prints the full set of results and writes four figures into `figures/`.
On a fresh checkout it runs on the **synthetic template** input (see below), so
the AHP-based numbers are illustrative until you plug in your own judgements;
the data-driven parts (forecasting, cost) are real either way.

Each stage can also be run on its own:

```bash
python scripts/run_static.py        # ranking + disagreement heatmap
python scripts/run_forecasting.py   # drivers, forecasts, back-test, figure
python scripts/run_dynamic.py       # trajectory, Markov chain, resilience
python scripts/run_cost.py          # Monte-Carlo lifecycle cost + figure
python scripts/run_baselines.py     # TOPSIS + fuzzy-AHP
python scripts/run_stress.py        # stress scenarios + figure
```

---

## Your input data (please read)

**The interview judgements are the one thing this repository does not ship.**
The pipeline reads them from `inputs/interview_data.py`, which is *not* in the
repo. A synthetic, clearly-labelled template ships as
`inputs/interview_data.example.py`; if the real file is absent, the template is
used automatically (with a printed notice) so everything runs.

The template values are **not from any study** — they are synthetic, internally
consistent placeholders. To use your own data:

```bash
cp inputs/interview_data.example.py inputs/interview_data.py
# then edit inputs/interview_data.py and replace every matrix
```

Keep the orderings: alternatives **MBR, EC, CW**; criteria **Efficiency, Cost,
Land, Energy, Chemical, Odor**. Matrices are reciprocal on Saaty's 1–9 scale.
`inputs/interview_data.py` is git-ignored, so your data is never committed by
accident.

If you have **raw per-respondent judgements** rather than group matrices, build
the group matrices first (geometric-mean aggregation with per-respondent
consistency screening):

```bash
python scripts/build_matrices_from_interviews.py
```

Edit that script to feed in your respondent rows, then paste the resulting
matrices into `inputs/interview_data.py`. See `inputs/README.md` for details.

---

## Where the numbers come from

- **Driver data** are fetched live from the public **World Bank API** (no key
  needed): inflation `FP.CPI.TOTL.ZG` and urban population `SP.URB.TOTL.IN.ZS`
  for Turkiye. If the network is unavailable, the pipeline falls back to the
  cached CSV snapshots in `data/` and says so. The industrial electricity tariff
  has no clean public API and is bundled in `data/electricity_tariff_TR.csv`
  (TUIK / EPDK anchors) — update it as newer figures appear. See `data/README.md`.
- **Cost ranges** in `dtahp/cost.py` are engineering literature values, not
  study data.

Because of that split, **the forecasting and cost results reproduce the
manuscript exactly** (they depend only on public data and literature ranges),
while the **AHP / dynamic / baseline / stress** results reproduce the manuscript
only once you supply the study's own interview matrices — with the shipped
template they run correctly but on placeholder judgements.

A quick self-check ships with the code:

```bash
python tests/test_sanity.py
```

---

## Repository layout

```
greywater-dtahp/
├── dtahp/                     the package
│   ├── ahp.py                 priority weights, consistency ratio, consolidation
│   ├── interviews.py          build group matrices from raw judgements
│   ├── dataio.py              load the interview matrices (user file / template)
│   ├── data_sources.py        World Bank fetch + cached fallback + deflation
│   ├── forecasting.py         OLS / Bayesian / logistic trends + back-test
│   ├── mapping.py             forecasts -> time-varying Saaty matrices (map f)
│   ├── static_analysis.py     static ranking + disagreement heatmap
│   ├── dynamic.py             trajectory, Markov chain, resilience
│   ├── cost.py                Monte-Carlo lifecycle cost
│   ├── baselines.py           TOPSIS + fuzzy-AHP
│   └── stress.py              stress scenarios
├── scripts/                   one runnable entry point per stage (+ run_all)
├── inputs/                    interview_data.example.py (template) + guide
├── data/                      cached public series (+ provenance)
├── matlab/                    AHP.m and ahp_from_interviews.m (MATLAB companion)
├── figures/                   generated figures land here
└── tests/                     sanity checks
```

## MATLAB companion

For MATLAB users, `matlab/AHP.m` reproduces the static part (weights, CRs,
global scores, consolidated ranking) and `matlab/ahp_from_interviews.m` builds
group matrices from raw judgements. They carry the same synthetic template data
and the same replace-me notice as the Python version.

## Citation

If you use this code, please cite the accompanying paper. Fill in the authors,
year and DOI here and in `LICENSE` before publishing the repository.

## License

MIT — see `LICENSE` (add your name and year).
