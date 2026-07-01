"""
Driver data: fetch the macro series, deflate money to constant prices, and hand
back the real industrial-electricity index that powers the dynamic model.

Two World Bank indicators are pulled live from the public v2 API (no key
needed); if the network is unavailable the bundled CSV snapshots in ``data/``
are used instead, so the pipeline always runs. The industrial electricity
tariff has no clean public API and is read from the bundled CSV.
"""
import csv

import numpy as np

from .config import DATA_DIR, WB_INDICATORS, WB_COUNTRY, BASE_YEAR

WB_URL = "https://api.worldbank.org/v2/country/{country}/indicator/{ind}?format=json&per_page=20000"


# --------------------------------------------------------------------------
# fetching
# --------------------------------------------------------------------------
def _fetch_worldbank(indicator, country=WB_COUNTRY, timeout=20):
    """Return {year: value} from the live World Bank API, or None on failure."""
    try:
        import requests
    except ImportError:
        return None
    url = WB_URL.format(country=country, ind=indicator)
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
        records = payload[1]
    except Exception:
        return None
    out = {}
    for rec in records:
        val = rec.get("value")
        if val is not None:
            out[int(rec["date"])] = float(val)
    return out or None


def _read_cached(filename, value_col):
    """Read a two-column {year: value} series from a bundled CSV (skips #comments)."""
    out = {}
    with open(DATA_DIR / filename, newline="") as fh:
        reader = csv.DictReader(row for row in fh if not row.startswith("#"))
        for row in reader:
            if row.get(value_col):
                out[int(row["year"])] = float(row[value_col])
    return out


def load_series(name, verbose=True):
    """Load a World Bank series by short name ('cpi' or 'urban').

    Tries the live API first, falls back to the cached CSV, and reports which
    source was used.
    """
    cache = {"cpi": ("wb_cpi_TUR.csv", "inflation_pct"),
             "urban": ("wb_urban_TUR.csv", "urban_pct")}[name]
    live = _fetch_worldbank(WB_INDICATORS[name])
    if live:
        if verbose:
            print(f"[data] {name}: fetched {len(live)} points from the World Bank API")
        return live
    if verbose:
        print(f"[data] {name}: World Bank API unavailable -- using cached {cache[0]}")
    return _read_cached(*cache)


def load_tariff(verbose=True):
    """Nominal industrial electricity tariff, {year: TRY/kWh} (bundled CSV)."""
    if verbose:
        print("[data] electricity tariff: reading bundled electricity_tariff_TR.csv")
    return _read_cached("electricity_tariff_TR.csv", "nominal_try_per_kwh")


# --------------------------------------------------------------------------
# deflation
# --------------------------------------------------------------------------
def cpi_level(inflation_pct, base_year=BASE_YEAR, extend_to=None, extend_rate=None):
    """Build a CPI price-level index (base_year = 100) from annual rates.

    Optionally extrapolate one or more years forward at ``extend_rate`` (%),
    useful when the tariff has a more recent anchor than the CPI series.
    """
    years = sorted(inflation_pct)
    level = {base_year: 100.0}
    for y in range(base_year + 1, max(years) + 1):
        level[y] = level[y - 1] * (1 + inflation_pct[y] / 100.0)
    for y in range(base_year - 1, min(years) - 1, -1):
        level[y] = level[y + 1] / (1 + inflation_pct[y + 1] / 100.0)
    if extend_to and extend_rate is not None:
        for y in range(max(level) + 1, extend_to + 1):
            level[y] = level[y - 1] * (1 + extend_rate / 100.0)
    return level


def real_electricity_index(tariff_nominal, level, base_year=BASE_YEAR):
    """Deflate the nominal tariff to a real index normalised to 1 at base_year."""
    base = tariff_nominal[base_year] / (level[base_year] / 100.0)
    idx = {}
    for y, p in tariff_nominal.items():
        idx[y] = (p / (level[y] / 100.0)) / base
    return idx


def get_drivers(verbose=True, extend_cpi_rate=34.88):
    """Convenience bundle: real electricity index, urbanisation series, CPI level.

    ``extend_cpi_rate`` extrapolates the CPI one year past the last observation
    so the latest tariff anchor can be deflated (Turkiye 2025 provisional).
    """
    cpi = load_series("cpi", verbose)
    urban = load_series("urban", verbose)
    tariff = load_tariff(verbose)
    max_tariff_year = max(tariff)
    level = cpi_level(cpi, extend_to=max_tariff_year, extend_rate=extend_cpi_rate)
    elec_real = real_electricity_index(tariff, level)
    if verbose:
        ratio = level[2022] / level[BASE_YEAR]
        print(f"[data] deflator check: CPI(2022)/CPI({BASE_YEAR}) = {ratio:.4f} "
              f"(World Bank/OECD level ~ 3.999)")
    return dict(elec_real=elec_real, urban=urban, cpi_level=level)
