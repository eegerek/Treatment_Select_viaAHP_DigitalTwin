"""
Digital-twin AHP toolkit for greywater treatment technology selection.

A small, self-contained pipeline that keeps an Analytic Hierarchy Process (AHP)
decision current from real macro-economic data: it fetches driver series, fits
and validates trend forecasts, maps those forecasts onto time-varying Saaty
judgements, and reports the ranking together with a Markov/resilience summary,
a Monte-Carlo lifecycle-cost model, and stress tests.

See the top-level README for the intended workflow.
"""

__version__ = "1.0.0"

from .config import (CRITERIA, METHODS, STAKEHOLDERS, STAKEHOLDER_LABELS)  # noqa: F401

