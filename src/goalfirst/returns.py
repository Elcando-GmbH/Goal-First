"""Prices and calendar-year returns.

The framework counts in calendar years, not rolling windows: each year is one
observation, counted exactly once. See *Goal First in Python*, Part 3.
"""

from __future__ import annotations

import pandas as pd

from .providers.base import PriceProvider, resolve


def get_prices(ticker: str, years: int = 20,
               provider: PriceProvider | None = None) -> pd.Series:
    """Daily adjusted closing prices for ``ticker``.

    Returns a ``pd.Series`` indexed by date, ascending, covering roughly the
    last ``years`` years plus the preceding year (needed for the first
    calendar-year return). Empty series if the ticker yields no data.
    """
    return resolve(provider).prices(ticker, years)


def annual_returns_from_prices(prices: pd.Series, years: int | None = None,
                               include_current_year: bool = True) -> pd.Series:
    """Calendar-year returns from a daily price series.

    One value per calendar year: last close of the year divided by the last
    close of the previous year, minus one. With ``years`` given, the most
    recent ``years`` complete years are kept.

    The current, still running year is included by default as a year-to-date
    return (latest close against last year's close) and counts as one more
    observation on top of ``years``. This is deliberate: the framework is
    meant to be run intra-year, and a stock that is down in the current year
    should find it harder to pass, even in January. Pass
    ``include_current_year=False`` to work with complete years only.

    Returns a ``pd.Series`` indexed by year (``int``), values as decimals
    (0.15 for +15 %).
    """
    if prices is None or prices.empty:
        return pd.Series(dtype=float)

    prices = prices.dropna().sort_index()
    year_end = prices.groupby(prices.index.year).last()
    year_end.index = year_end.index.astype(int)
    returns = year_end.pct_change().dropna()

    current_year = pd.Timestamp.today().year
    complete = returns[returns.index < current_year]
    current = returns[returns.index == current_year]

    if years is not None:
        complete = complete.iloc[-years:]
    if include_current_year:
        returns = pd.concat([complete, current])
    else:
        returns = complete

    returns.index.name = "year"
    return returns.astype(float)


def get_annual_returns(ticker: str, years: int = 20,
                       provider: PriceProvider | None = None,
                       include_current_year: bool = True) -> pd.Series:
    """Fetches adjusted closing prices and calculates calendar year returns.

    Returns ``pd.Series`` indexed by year (``int``), values as decimals,
    e.g. 0.15 for +15 %: up to ``years`` complete calendar years plus the
    running year as year-to-date (see :func:`annual_returns_from_prices`).
    """
    prices = get_prices(ticker, years, provider)
    return annual_returns_from_prices(prices, years, include_current_year)
