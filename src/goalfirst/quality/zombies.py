"""Zombie detection: stocks that trade on paper but have no real market."""

from __future__ import annotations

import pandas as pd

from ..providers.base import PriceProvider, resolve
from ..returns import annual_returns_from_prices

TRADING_DAYS_PER_YEAR = 252
SPIKE_THRESHOLD = 0.8          # same bar as detect_split_anomalies
MIN_DORMANT_YEARS = 2


def detect_zombies(ticker: str, price_floor: float = 2.0, min_avg_volume: int = 100_000,
                   dormancy_threshold: float = 0.05, years: int = 20,
                   provider: PriceProvider | None = None) -> dict:
    """Detects two zombie patterns.

    1. **Active zombie** – trading but effectively illiquid: average daily
       volume over the last 252 trading days below ``min_avg_volume``. One
       year, not the whole window: a stock that was illiquid fifteen years ago
       and is not today is not a zombie.

    2. **Reactivated zombie** – a dormancy period followed by an extreme
       return spike. Dormancy means at least two consecutive calendar years in
       which *both* hold: ``|annual return| < dormancy_threshold`` *and*
       average price below ``price_floor``. A flat return alone (a utility at
       80) or a low price alone (a penny stock that moves) is not dormancy.
       The spike is the year right after, with ``|annual return| > 0.8``.

    ``price_floor`` is in the stock's trading currency, not in dollars. For
    a Tokyo listing 2.0 means 2 yen; adjust the floor to your universe.

    Returns::

        {
          'ticker': str,
          'classification': 'none' | 'active' | 'reactivated' | 'both',
          'avg_volume_1y': float | None,
          'flagged_periods': [
            {'start': int, 'end': int, 'type': str, 'note': str}, ...
          ]
        }
    """
    src = resolve(provider)
    prices = src.prices(ticker, years)
    flagged: list[dict] = []

    # -- 1. active zombie: illiquid over the last trading year ---------------
    volume = src.volume(ticker, years)
    avg_volume: float | None = None
    active = False
    if volume is not None and len(volume.dropna()):
        avg_volume = float(volume.dropna().iloc[-TRADING_DAYS_PER_YEAR:].mean())
        if avg_volume < min_avg_volume:
            active = True
            last_year = int(volume.dropna().index[-1].year)
            flagged.append({
                "start": last_year, "end": last_year, "type": "active",
                "note": f"avg daily volume {avg_volume:,.0f} < {min_avg_volume:,}",
            })

    # -- 2. reactivated zombie: dormancy then spike -------------------------
    reactivated = False
    if prices is not None and len(prices.dropna()):
        p = prices.dropna().sort_index()
        returns = annual_returns_from_prices(p, years)
        avg_price = p.groupby(p.index.year).mean()
        avg_price.index = avg_price.index.astype(int)

        dormant = pd.Series(
            {y: abs(float(r)) < dormancy_threshold and float(avg_price.get(y, float("inf"))) < price_floor
             for y, r in returns.items()}
        )
        yrs = list(returns.index)
        run_start: int | None = None
        for i, y in enumerate(yrs):
            if dormant.get(y, False):
                if run_start is None:
                    run_start = y
                continue
            # run ended at yrs[i-1]; check length and spike in year y
            if run_start is not None:
                run_len = yrs[i - 1] - run_start + 1
                if run_len >= MIN_DORMANT_YEARS and abs(float(returns[y])) > SPIKE_THRESHOLD:
                    reactivated = True
                    flagged.append({
                        "start": int(run_start), "end": int(y), "type": "reactivated",
                        "note": (f"dormant {run_start}–{yrs[i - 1]} "
                                 f"(|return| < {dormancy_threshold:.0%}, price < {price_floor}), "
                                 f"then {float(returns[y]):+.0%} in {y}"),
                    })
            run_start = None

    if active and reactivated:
        classification = "both"
    elif active:
        classification = "active"
    elif reactivated:
        classification = "reactivated"
    else:
        classification = "none"

    return {"ticker": ticker, "classification": classification,
            "avg_volume_1y": avg_volume, "flagged_periods": flagged}
