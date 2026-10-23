"""Default provider backed by yfinance.

yfinance is an independent open-source library that fetches data from Yahoo
Finance. It is not an official API. Use of the retrieved data is governed by
Yahoo's terms, not by this package.
"""

from __future__ import annotations

import warnings

import pandas as pd


def _import_yfinance():
    """Import yfinance lazily and silence pandas deprecation noise it triggers.

    Lazy, so the offline test suite does not need yfinance installed. The
    filter is registered *after* the import: yfinance/pandas install their own
    warning filters at import time, and a filter added before that would be
    shadowed. Limited to the yfinance module; goalfirst's own warnings show.
    """
    import yfinance as yf

    warnings.filterwarnings("ignore", module=r"yfinance(\..*)?")
    return yf


class YFinanceProvider:
    """:class:`~goalfirst.providers.base.PriceProvider` implementation using yfinance.

    Price history is fetched once per (ticker, years) and cached for the
    lifetime of the provider instance, so the screener does not hit Yahoo
    several times for the same symbol.
    """

    def __init__(self) -> None:
        self._history: dict[tuple[str, int], pd.DataFrame] = {}

    # -- internals ---------------------------------------------------------

    def _ticker(self, ticker: str):
        return _import_yfinance().Ticker(ticker)

    def _fetch(self, ticker: str, years: int) -> pd.DataFrame:
        key = (ticker, years)
        if key not in self._history:
            # One extra year so that the first calendar year has a prior close.
            hist = self._ticker(ticker).history(period=f"{years + 1}y", auto_adjust=True)
            if hist is None or hist.empty:
                hist = pd.DataFrame(columns=["Close", "Volume"])
            else:
                hist = hist.sort_index()
                hist.index = pd.DatetimeIndex(hist.index).tz_localize(None)
            self._history[key] = hist
        return self._history[key]

    # -- PriceProvider -----------------------------------------------------

    def prices(self, ticker: str, years: int) -> pd.Series:
        hist = self._fetch(ticker, years)
        return hist["Close"].dropna().astype(float).rename(ticker)

    def volume(self, ticker: str, years: int) -> pd.Series:
        hist = self._fetch(ticker, years)
        return hist["Volume"].dropna().astype(float).rename(ticker)

    def splits(self, ticker: str) -> pd.Series:
        s = self._ticker(ticker).splits
        if s is None or len(s) == 0:
            return pd.Series(dtype=float)
        s = s.sort_index()
        s.index = pd.DatetimeIndex(s.index).tz_localize(None)
        return s.astype(float)

    def dividend_yield(self, ticker: str) -> float | None:
        info = self._ticker(ticker).info or {}
        value = info.get("dividendYield")
        if value is None:
            return None
        # yfinance has reported this field both as a decimal and as a percentage
        # across versions; normalise to a decimal.
        value = float(value)
        return value / 100 if value > 1 else value

    def payout_ratio(self, ticker: str) -> float | None:
        info = self._ticker(ticker).info or {}
        value = info.get("payoutRatio")
        return None if value is None else float(value)
