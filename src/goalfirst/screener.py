"""The screener: goal first, constraints second, rank what remains.

One core routine, three public variants. Each variant differs only in which
goal threshold it applies, which second constraint it checks and which column
it ranks by. See *Goal First in Python*, Parts 3 and 5.

Every function returns only candidates that passed the goal threshold and all
constraints. Excluded tickers do not appear in the output.
"""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np
import pandas as pd

from .metrics import average_annual_return, benchmark_bias
from .providers.base import PriceProvider, resolve
from .returns import annual_returns_from_prices

# -- internal ---------------------------------------------------------------

def _loss_year_ratio(returns: pd.Series) -> float:
    """Fraction of observed years with a negative return.

    Divides by the number of observations actually present (complete years
    plus the running year), not by the requested lookback.
    """
    return float((returns < 0).sum() / len(returns))


def _candidates(tickers: list[str], years: int, min_years: int,
                provider: PriceProvider) -> Iterator[tuple[str, pd.Series]]:
    """Yield ``(ticker, annual_returns)`` for tickers with enough history.

    The history constraint counts complete calendar years, consistent with
    :func:`~goalfirst.quality.validate_tickers`. Tickers without data or with
    fewer than ``min_years`` complete years are skipped silently; run
    ``validate_tickers`` first if you want to see them.
    """
    for ticker in tickers:
        prices = provider.prices(ticker, years)
        if prices is None or prices.dropna().empty:
            continue
        complete = annual_returns_from_prices(prices, years, include_current_year=False)
        if len(complete) < min_years:
            continue
        yield ticker, annual_returns_from_prices(prices, years)


def _frame(rows: list[dict], columns: list[str], sort_by: str, ascending: bool) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=columns)
    if df.empty:
        return df
    return df.sort_values(sort_by, ascending=ascending, kind="stable").reset_index(drop=True)


# -- public -------------------------------------------------------------------

def screen(tickers: list[str],
           benchmark: str = '^GSPC',
           min_bias: float = 0.60,
           max_loss_ratio: float = 0.25,
           min_years: int = 10,
           years: int = 20,
           provider: PriceProvider | None = None) -> pd.DataFrame:
    """Applies goal-first screening logic to a validated ticker list.

    Parameters:
        tickers        - validated ticker list
        benchmark      - benchmark ticker (default: S&P 500)
        min_bias       - goal: min fraction of years beating benchmark
        max_loss_ratio - constraint: max fraction of years with negative return
        min_years      - constraint: minimum complete years of data required
        years          - lookback period in years

    Returns:
        pd.DataFrame sorted by avg_annual_return descending.
        Columns: ticker | bias_score | loss_year_ratio | avg_annual_return
    """
    src = resolve(provider)
    bench = annual_returns_from_prices(src.prices(benchmark, years), years)
    rows: list[dict] = []

    for ticker, returns in _candidates(tickers, years, min_years, src):
        bias = benchmark_bias(returns, bench)["bias_score"]
        if np.isnan(bias) or bias < min_bias:
            continue                                   # goal not met
        loss_ratio = _loss_year_ratio(returns)
        if loss_ratio > max_loss_ratio:
            continue                                   # constraint 1
        rows.append({
            "ticker": ticker,
            "bias_score": bias,
            "loss_year_ratio": loss_ratio,
            "avg_annual_return": average_annual_return(returns),
        })

    return _frame(rows, ["ticker", "bias_score", "loss_year_ratio", "avg_annual_return"],
                  sort_by="avg_annual_return", ascending=False)


def screen_dividend(tickers: list[str],
                    min_yield: float = 0.035,
                    max_loss_ratio: float = 0.25,
                    max_payout_ratio: float = 0.90,
                    min_years: int = 10,
                    years: int = 20,
                    provider: PriceProvider | None = None) -> pd.DataFrame:
    """Dividend variant of the core screener.

    Goal:        dividend yield above min_yield
    Constraints: loss year ratio, payout ratio
    Ranking:     average annual total return, descending

    Returns:
        pd.DataFrame sorted by avg_annual_return descending.
        Columns: ticker | dividend_yield | loss_year_ratio | payout_ratio | avg_annual_return
    """
    src = resolve(provider)
    rows: list[dict] = []

    for ticker, returns in _candidates(tickers, years, min_years, src):
        div_yield = src.dividend_yield(ticker)
        payout = src.payout_ratio(ticker)
        # A goal or constraint that cannot be checked is not passed. A missing
        # yield or payout ratio from the provider therefore excludes the ticker
        # rather than letting it through with a blank. Conservative by design.
        if div_yield is None or payout is None:
            continue
        if div_yield < min_yield:
            continue                                   # goal not met
        if _loss_year_ratio(returns) > max_loss_ratio:
            continue                                   # constraint 1
        if payout > max_payout_ratio:
            continue                                   # constraint 2
        rows.append({
            "ticker": ticker,
            "dividend_yield": float(div_yield),
            "loss_year_ratio": _loss_year_ratio(returns),
            "payout_ratio": float(payout),
            "avg_annual_return": average_annual_return(returns),
        })

    return _frame(rows, ["ticker", "dividend_yield", "loss_year_ratio", "payout_ratio",
                         "avg_annual_return"],
                  sort_by="avg_annual_return", ascending=False)


def screen_low_volatility(tickers: list[str],
                          max_loss_ratio: float = 0.25,
                          max_single_drawdown: float = 0.30,
                          min_years: int = 10,
                          years: int = 20,
                          provider: PriceProvider | None = None) -> pd.DataFrame:
    """Low volatility variant of the core screener.

    Goal metric: standard deviation of calendar-year returns (sample, ddof=1).
                 Annual observations, so no further annualisation is applied.
    Constraints: loss year ratio, max single-year drawdown
    Ranking:     std deviation ascending (lowest first)

    ``max_single_drawdown`` is checked against the worst calendar-year return:
    a stock whose worst year was -38 % fails a 0.30 threshold even if its
    standard deviation looks moderate. That one year is the event that makes
    investors sell at the worst moment; it must not vanish in the average.

    Returns:
        pd.DataFrame sorted by annual_std ascending.
        Columns: ticker | annual_std | loss_year_ratio | worst_year_return
    """
    src = resolve(provider)
    rows: list[dict] = []

    for ticker, returns in _candidates(tickers, years, min_years, src):
        if len(returns) < 2:
            continue                                   # std undefined
        if _loss_year_ratio(returns) > max_loss_ratio:
            continue                                   # constraint 1
        worst = float(returns.min())
        if worst < -max_single_drawdown:
            continue                                   # constraint 2
        rows.append({
            "ticker": ticker,
            "annual_std": float(returns.std(ddof=1)),
            "loss_year_ratio": _loss_year_ratio(returns),
            "worst_year_return": worst,
        })

    return _frame(rows, ["ticker", "annual_std", "loss_year_ratio", "worst_year_return"],
                  sort_by="annual_std", ascending=True)
