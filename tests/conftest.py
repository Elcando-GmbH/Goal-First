"""Shared test fixtures. No network access anywhere in the test suite."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def daily_index(start_year: int, end_year: int) -> pd.DatetimeIndex:
    """Business days from 1 Jan ``start_year`` to 31 Dec ``end_year``."""
    return pd.bdate_range(f"{start_year}-01-01", f"{end_year}-12-31")


def prices_from_annual_returns(annual: dict[int, float], start_price: float = 100.0) -> pd.Series:
    """Build a daily price series whose calendar-year returns equal ``annual``.

    Prices move linearly within each year, so the year-end close is exact and
    the path in between is irrelevant for calendar-year arithmetic.
    """
    years = sorted(annual)
    first = years[0] - 1
    idx = daily_index(first, years[-1])
    out = pd.Series(index=idx, dtype=float)

    # Prior year: flat at start_price so the first return has a base.
    out[out.index.year == first] = start_price
    level = start_price
    for y in years:
        target = level * (1 + annual[y])
        mask = out.index.year == y
        n = mask.sum()
        out[mask] = np.linspace(level, target, n)
        level = target
    return out


class FakeProvider:
    """In-memory PriceProvider for tests."""

    def __init__(self) -> None:
        self._prices: dict[str, pd.Series] = {}
        self._volume: dict[str, pd.Series] = {}
        self._splits: dict[str, pd.Series] = {}
        self._yield: dict[str, float | None] = {}
        self._payout: dict[str, float | None] = {}

    # -- setup helpers ----------------------------------------------------

    def add(self, ticker: str, prices: pd.Series, *, volume: pd.Series | None = None,
            splits: pd.Series | None = None, dividend_yield: float | None = None,
            payout_ratio: float | None = None) -> FakeProvider:
        self._prices[ticker] = prices
        self._volume[ticker] = volume if volume is not None else pd.Series(
            1_000_000.0, index=prices.index)
        self._splits[ticker] = splits if splits is not None else pd.Series(dtype=float)
        self._yield[ticker] = dividend_yield
        self._payout[ticker] = payout_ratio
        return self

    # -- PriceProvider ------------------------------------------------------

    def prices(self, ticker: str, years: int) -> pd.Series:
        return self._prices.get(ticker, pd.Series(dtype=float))

    def volume(self, ticker: str, years: int) -> pd.Series:
        return self._volume.get(ticker, pd.Series(dtype=float))

    def splits(self, ticker: str) -> pd.Series:
        return self._splits.get(ticker, pd.Series(dtype=float))

    def dividend_yield(self, ticker: str) -> float | None:
        return self._yield.get(ticker)

    def payout_ratio(self, ticker: str) -> float | None:
        return self._payout.get(ticker)


@pytest.fixture
def provider() -> FakeProvider:
    return FakeProvider()
