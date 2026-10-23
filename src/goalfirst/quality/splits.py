"""Split anomaly detection: extreme annual returns without a known split."""

from __future__ import annotations

from ..providers.base import PriceProvider, resolve
from ..returns import annual_returns_from_prices


def detect_split_anomalies(ticker: str, threshold: float = 0.8, years: int = 20,
                           provider: PriceProvider | None = None) -> list[dict]:
    """Flags years where the annual return exceeds ``threshold`` in either
    direction and cross-checks them against known split dates.

    What this can and cannot do: the framework works on adjusted prices, so a
    split that the data source processed correctly is invisible here. The
    detector therefore catches one specific pattern, an extreme return with
    *no* split on record, and marks it ``'check'``. An extreme return *with* a
    split on record is marked ``'plausible'``: an explanation exists, which is
    not the same as proof that the adjustment was correct.

    Nothing is removed. The decision to keep or exclude a year stays with you.

    Returns a list, one entry per flagged year::

        {
          'year': int,
          'annual_return': float,       # decimal
          'split_in_year': bool,
          'split_ratio': float | None,  # e.g. 2.0 for a 2:1 split
          'assessment': 'plausible' | 'check'
        }
    """
    src = resolve(provider)
    returns = annual_returns_from_prices(src.prices(ticker, years), years)
    if returns.empty:
        return []

    splits = src.splits(ticker)
    splits_by_year: dict[int, float] = {}
    if splits is not None and len(splits):
        for date, ratio in splits.items():
            splits_by_year[int(date.year)] = float(ratio)

    flagged: list[dict] = []
    for year, r in returns.items():
        if abs(float(r)) <= threshold:
            continue
        ratio = splits_by_year.get(int(year))
        flagged.append({
            "year": int(year),
            "annual_return": float(r),
            "split_in_year": ratio is not None,
            "split_ratio": ratio,
            "assessment": "plausible" if ratio is not None else "check",
        })
    return flagged
