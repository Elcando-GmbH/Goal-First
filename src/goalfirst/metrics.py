"""Descriptive metrics for screener candidates.

Each metric is a single-responsibility function: a return or price series in,
one number (or a small dict) out. The screener does not need to know which
metrics are attached; the metrics do not need to know about the screener.
See *Goal First in Python*, Part 4.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


def average_annual_return(annual_returns: Sequence[float] | pd.Series) -> float:
    """Arithmetic mean of calendar-year returns.

    annual_returns: decimal returns, e.g. ``[0.15, -0.12, 0.23]``
    returns: arithmetic mean as decimal, e.g. ``0.087`` for 8.7 %

    Each year is treated as an independent observation. This measures the
    consistency of annual performance across stocks, not terminal wealth.
    Returns ``nan`` for an empty input.
    """
    values = np.asarray(list(annual_returns), dtype=float)
    if values.size == 0:
        return float("nan")
    return float(values.mean())


def max_drawdown(prices: pd.Series) -> float:
    """Largest peak-to-trough decline over the period.

    prices: adjusted closing prices in chronological order
    returns: maximum drawdown as a negative decimal, e.g. ``-0.43`` for a
             43 % decline; ``0.0`` if prices never fell below a prior peak;
             ``nan`` for an empty series
    """
    if prices is None or len(prices) == 0:
        return float("nan")
    p = pd.Series(prices).dropna().astype(float).sort_index()
    if p.empty:
        return float("nan")
    running_peak = p.cummax()
    drawdown = p / running_peak - 1.0
    return float(drawdown.min())


def benchmark_bias(stock_returns: pd.Series, benchmark_returns: pd.Series) -> dict:
    """How often, and by how much, a stock beat its benchmark.

    stock_returns:     annual returns as ``pd.Series`` indexed by year
    benchmark_returns: annual returns as ``pd.Series`` indexed by year

    Only years present in both series are compared. Returns::

        {
            'bias_score': float,         # fraction of years beating benchmark
            'avg_outperformance': float  # avg excess return in years stock won
        }

    ``bias_score`` is ``nan`` with no overlapping years; ``avg_outperformance``
    is ``nan`` when the stock never beat the benchmark.
    """
    common = stock_returns.index.intersection(benchmark_returns.index)
    if len(common) == 0:
        return {"bias_score": float("nan"), "avg_outperformance": float("nan")}

    excess = (stock_returns.loc[common] - benchmark_returns.loc[common]).astype(float)
    wins = excess[excess > 0]
    return {
        "bias_score": float(len(wins) / len(common)),
        "avg_outperformance": float(wins.mean()) if len(wins) else float("nan"),
    }
