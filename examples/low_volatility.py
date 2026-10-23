"""Low volatility strategy — Goal First in Python, Part 5, variant 2.

Goal metric: standard deviation of calendar-year returns, lowest first.
Constraints: loss year ratio, worst single-year return. Replace UNIVERSE with
your own list.
"""

import pandas as pd

from goalfirst import screen_low_volatility, validate_tickers

UNIVERSE = ["JNJ", "PG", "KO", "WMT", "MCD", "PEP", "CL", "GIS", "DUK", "SO"]
YEARS = 20

pd.set_option("display.width", 120)
pd.set_option("display.float_format", "{:.3f}".format)


def main() -> None:
    checked = validate_tickers(UNIVERSE, min_years=10, years=YEARS)
    results = screen_low_volatility(checked["valid"], max_loss_ratio=0.25,
                                    max_single_drawdown=0.30, min_years=10, years=YEARS)
    print(results.to_string(index=False))
    print(f"\n{len(UNIVERSE)} in, {len(results)} passed. Review each candidate before acting.")


if __name__ == "__main__":
    main()
