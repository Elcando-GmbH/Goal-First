"""Dividend strategy — Goal First in Python, Part 5, variant 1.

Goal: dividend yield above a threshold. Constraints: loss year ratio, payout
ratio. Ranking: average annual total return. Replace UNIVERSE with your own list.
"""

import pandas as pd

from goalfirst import screen_dividend, validate_tickers

UNIVERSE = ["JNJ", "PG", "KO", "PEP", "XOM", "CVX", "T", "VZ", "MO", "IBM"]
YEARS = 20

pd.set_option("display.width", 120)
pd.set_option("display.float_format", "{:.3f}".format)


def main() -> None:
    checked = validate_tickers(UNIVERSE, min_years=10, years=YEARS)
    results = screen_dividend(checked["valid"], min_yield=0.035, max_loss_ratio=0.25,
                              max_payout_ratio=0.90, min_years=10, years=YEARS)
    print(results.to_string(index=False))
    print(f"\n{len(UNIVERSE)} in, {len(results)} passed. Review each candidate before acting.")


if __name__ == "__main__":
    main()
