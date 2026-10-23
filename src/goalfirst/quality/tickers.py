"""Ticker validation: does the symbol yield data, and enough of it?"""

from __future__ import annotations

from ..providers.base import PriceProvider, resolve
from ..returns import annual_returns_from_prices


def validate_tickers(tickers: list[str], min_years: int = 10, years: int = 20,
                     provider: PriceProvider | None = None) -> dict:
    """Checks each ticker for data availability and minimum history length.

    A ticker is *invalid* when the provider returns no prices at all.
    *Available years* counts complete calendar years with a return; the
    running year is not counted, so a stock listed in January does not have
    "one year" of history. A ticker with data but fewer than ``min_years``
    complete years goes to *insufficient_history*.

    Returns::

        {
          'valid': [...],
          'invalid': [...],
          'insufficient_history': [...],
          'years': {ticker: int}      # complete years with data, 0 if invalid
        }

    ``years`` is the lookback window requested from the provider (same
    default as the screener, so the data is fetched once and reused).
    Input order is preserved within each list.
    """
    src = resolve(provider)
    valid: list[str] = []
    invalid: list[str] = []
    short: list[str] = []
    available: dict[str, int] = {}

    for ticker in tickers:
        prices = src.prices(ticker, years)
        if prices is None or prices.dropna().empty:
            invalid.append(ticker)
            available[ticker] = 0
            continue
        n = len(annual_returns_from_prices(prices, include_current_year=False))
        available[ticker] = n
        (valid if n >= min_years else short).append(ticker)

    return {"valid": valid, "invalid": invalid,
            "insufficient_history": short, "years": available}
