"""Price data provider protocol.

Every function in ``goalfirst`` that needs market data accepts an optional
``provider`` argument. ``None`` means the default provider (yfinance). Any
object that satisfies :class:`PriceProvider` can be passed instead, which keeps
the package independent of a single data source.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class PriceProvider(Protocol):
    """Minimal interface the framework needs from a data source.

    All series are indexed by ``pd.DatetimeIndex`` in ascending order.
    A ticker that yields no data returns an empty series, never raises.
    """

    def prices(self, ticker: str, years: int) -> pd.Series:
        """Daily adjusted closing prices covering roughly the last ``years`` years."""
        ...

    def volume(self, ticker: str, years: int) -> pd.Series:
        """Daily traded volume over the same window as :meth:`prices`."""
        ...

    def splits(self, ticker: str) -> pd.Series:
        """Split ratios indexed by effective date (e.g. 2.0 for a 2:1 split)."""
        ...

    def dividend_yield(self, ticker: str) -> float | None:
        """Trailing dividend yield as a decimal (0.035 for 3.5 %), or ``None``."""
        ...

    def payout_ratio(self, ticker: str) -> float | None:
        """Dividend payout ratio as a decimal (0.62 for 62 %), or ``None``."""
        ...


_default: PriceProvider | None = None


def default_provider() -> PriceProvider:
    """Return the process-wide default provider, creating it on first use."""
    global _default
    if _default is None:
        from .yfinance import YFinanceProvider

        _default = YFinanceProvider()
    return _default


def set_default_provider(provider: PriceProvider | None) -> None:
    """Replace the default provider. ``None`` restores yfinance on next use."""
    global _default
    _default = provider


def resolve(provider: PriceProvider | None) -> PriceProvider:
    """Return ``provider`` if given, otherwise the default."""
    return provider if provider is not None else default_provider()
