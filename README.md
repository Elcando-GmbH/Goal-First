# goal-first

[![CI](https://github.com/Elcando-GmbH/Goal-First/actions/workflows/ci.yml/badge.svg)](https://github.com/Elcando-GmbH/Goal-First/actions/workflows/ci.yml)

Reference implementation of the screening framework from *Goal First in Python*.

Goal first, constraints second, rank what remains.

## Install

Not yet on PyPI. From source:

```bash
pip install git+https://github.com/Elcando-GmbH/Goal-First.git
```

Requires Python 3.11 or later.

## What's inside

| Layer | Functions | Guide 2 |
|---|---|---|
| Data quality | `validate_tickers` · `detect_split_anomalies` · `detect_zombies` | Part 2 |
| Prices and returns | `get_prices` · `get_annual_returns` | Part 3 |
| Screener | `screen` · `screen_dividend` · `screen_low_volatility` | Parts 3, 5 |
| Metrics | `average_annual_return` · `max_drawdown` · `benchmark_bias` | Part 4 |

Function names and signatures follow the guide. The guide is the specification; the code
follows the current edition. Every function that needs market data takes an optional
`provider` argument at the end; `None` means yfinance.

Two conventions worth knowing before you read the output:

- Calendar-year returns include the running year as a year-to-date figure. The framework
  is meant to be run intra-year; a stock that is down this year should find it harder to
  pass. Pass `include_current_year=False` to `get_annual_returns` to work with complete
  years only.
- Ratios (benchmark bias, loss-year ratio) divide by the number of observed years, not by
  the requested lookback.

## Quickstart

```python
from goalfirst import validate_tickers, screen, max_drawdown, get_prices

universe = ["AAPL", "MSFT", "JNJ", "PG", "XOM"]   # your own list

checked = validate_tickers(universe, min_years=10)
results = screen(checked["valid"], benchmark="^GSPC",
                 min_bias=0.60, max_loss_ratio=0.25)

results["max_drawdown"] = results["ticker"].apply(
    lambda t: max_drawdown(get_prices(t))
)
print(results)
```

Full walkthroughs for all three strategies are in [`examples/`](examples/).

The screener returns a shortlist, not a buy list. The last step is always a manual review.

## Data

Examples use [yfinance](https://github.com/ranaroussi/yfinance), an independent open-source
library that fetches data from Yahoo Finance. It is not an official API and not affiliated
with Yahoo. What you may do with the retrieved data is governed by Yahoo's terms, not by this
package — check them before distributing, publishing or using results commercially.

This repository contains code only. No price data is stored here.

Depending on your yfinance and pandas versions, fetches may print pandas deprecation
warnings pointing into `yfinance/utils.py`. They originate in yfinance, not in this
package, and do not affect results.

Other data sources plug in through the `PriceProvider` protocol in `goalfirst.providers`.

## The guides

- [*Goal First — A Smarter Way to Select Stocks*](https://leveragethinking.gumroad.com/l/ozgyut) — the method
- [*Goal First in Python — Build Your Own Stock Screener*](https://leveragethinking.gumroad.com/l/meueh) — this implementation
- [*Goal First — Erst das Ziel, dann die Aktien*](https://leveragethinking.gumroad.com/l/iucnby) — German edition of the method
- [*Goal First in Python — Bau dir deinen eigenen Aktien-Screener*](https://leveragethinking.gumroad.com/l/sirpje) — German edition of this implementation

## Author

**Laura Kruse-Stecher** · Quant Investor & Developer  
Equity investor for 20+ years. Proprietary stock selection algorithms in live trading.  
Data integrity and backtesting infrastructure: Python, PostgreSQL/TimescaleDB.  
Economist; managing director and sole shareholder of Elcando GmbH.  
Author of *Goal First*, writing as Leverage Thinking.

## License

MIT · Copyright (c) 2026 Elcando GmbH

For informational purposes only. Not investment advice.

Imprint / Impressum: [leveragethinking.gumroad.com](https://leveragethinking.gumroad.com)
