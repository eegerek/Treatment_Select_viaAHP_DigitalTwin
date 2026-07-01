#!/usr/bin/env python3
"""Fetch drivers, fit/validate forecasts, and write the forecast figure."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from dtahp import forecasting
if __name__ == "__main__":
    model = forecasting.get_models()
    print("\nenergy real-growth slope (Bayesian): "
          f"{model.energy_slope_mean:+.4f} +/- {model.energy_slope_sd:.4f} /yr")
    mae = forecasting.backtest_mae(model.drivers["urban"], train_end=2018)
    print(f"urbanisation back-test MAE (pp): log-linear {mae['loglinear']:.2f}, "
          f"logistic {mae['logistic']:.2f}")
    for y in (2030, 2035, 2040):
        m, lo, hi = forecasting.bayes_predict(model.energy_bayes, y)
        print(f"  energy index {y}: {m:.2f}  (95% PPI [{lo:.2f}, {hi:.2f}])")
    print("[figure]", forecasting.save_forecast_figure(model).name)
