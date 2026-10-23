"""Outperformance strategy — Goal First in Python, Parts 2 to 4.

Data quality layer, then the screener, then metrics attached to the result.
Replace UNIVERSE with your own ticker list.
"""

import pandas as pd

from goalfirst import (
    benchmark_bias,
    detect_split_anomalies,
    detect_zombies,
    get_annual_returns,
    get_prices,
    max_drawdown,
    screen,
    validate_tickers,
)

UNIVERSE = ["AAPL", "MSFT", "JNJ", "PG", "XOM", "KO", "WMT", "INTC", "GE", "T"]
BENCHMARK = "^GSPC"
YEARS = 20

pd.set_option("display.width", 120)
pd.set_option("display.float_format", "{:.3f}".format)


def main() -> None:
    # 1. Data quality: who yields data, and enough of it?
    checked = validate_tickers(UNIVERSE, min_years=10, years=YEARS)
    print("valid:               ", checked["valid"])
    print("invalid:             ", checked["invalid"])
    print("insufficient history:", checked["insufficient_history"])

    for t in checked["valid"]:
        for flag in detect_split_anomalies(t, years=YEARS):
            print(f"  split check {t} {flag['year']}: {flag['annual_return']:+.0%} "
                  f"-> {flag['assessment']}")
        z = detect_zombies(t, years=YEARS)
        if z["classification"] != "none":
            print(f"  zombie {t}: {z['classification']}")

    # 2. Screen: goal threshold, constraints, ranking.
    results = screen(checked["valid"], benchmark=BENCHMARK,
                     min_bias=0.60, max_loss_ratio=0.25, min_years=10, years=YEARS)

    # 3. Metrics on what passed.
    bench = get_annual_returns(BENCHMARK, years=YEARS)
    results["max_drawdown"] = results["ticker"].apply(
        lambda t: max_drawdown(get_prices(t, years=YEARS))
    )
    results["avg_outperformance"] = results["ticker"].apply(
        lambda t: benchmark_bias(get_annual_returns(t, years=YEARS), bench)["avg_outperformance"]
    )

    print()
    print(results.to_string(index=False))
    print(f"\n{len(UNIVERSE)} in, {len(results)} passed. Review each candidate before acting.")


if __name__ == "__main__":
    main()
