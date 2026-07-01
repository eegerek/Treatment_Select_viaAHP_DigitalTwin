#!/usr/bin/env python3
"""
Run the whole pipeline end-to-end and regenerate every figure.

    python scripts/run_all.py

Steps: load drivers and fit forecasts -> static ranking + heatmap -> dynamic
trajectory, Markov chain and resilience -> lifecycle cost -> baselines ->
stress tests. Figures land in figures/.
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from dtahp import forecasting, static_analysis, dynamic, cost, baselines, stress
from dtahp import dataio


def main():
    print("=" * 68)
    print("DIGITAL-TWIN AHP -- full pipeline")
    print("=" * 68)

    ALT, STK = dataio.load_matrices()
    model = forecasting.get_models()

    print("\n" + "-" * 68 + "\n[1/6] STATIC AHP\n" + "-" * 68)
    static_analysis.run()

    print("\n" + "-" * 68 + "\n[2/6] FORECAST FIGURE\n" + "-" * 68)
    print("[figure]", forecasting.save_forecast_figure(model).name)

    print("\n" + "-" * 68 + "\n[3/6] DYNAMIC ENGINE\n" + "-" * 68)
    dynamic.run(model, ALT, STK)

    print("\n" + "-" * 68 + "\n[4/6] LIFECYCLE COST\n" + "-" * 68)
    cost.run(model)

    print("\n" + "-" * 68 + "\n[5/6] BASELINES\n" + "-" * 68)
    baselines.run(ALT, STK)

    print("\n" + "-" * 68 + "\n[6/6] STRESS TESTING\n" + "-" * 68)
    stress.run(model, ALT, STK)

    print("\n" + "=" * 68)
    print("done. figures written to figures/")
    print("=" * 68)


if __name__ == "__main__":
    main()
