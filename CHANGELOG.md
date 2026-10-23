# Changelog

## 0.1.0 — 2026-10-23

First complete implementation of the framework from *Goal First in Python*.

- Data quality layer: `validate_tickers`, `detect_split_anomalies`, `detect_zombies`
- Screener: `screen`, `screen_dividend`, `screen_low_volatility`
- Metrics: `average_annual_return`, `max_drawdown`, `benchmark_bias`
- Prices and calendar-year returns: `get_prices`, `get_annual_returns`
- `PriceProvider` protocol with a yfinance default; any data source can be plugged in
- Calendar-year returns include the running year as year-to-date by default
- Ratios divide by the number of observed years, not by the requested lookback
- Tests run offline on synthetic data

Not yet on PyPI.
