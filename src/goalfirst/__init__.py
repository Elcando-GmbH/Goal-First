"""Goal First — reference implementation of the stock selection framework.

Goal first, constraints second, rank what remains.
"""

from .metrics import average_annual_return, benchmark_bias, max_drawdown
from .providers.base import PriceProvider, set_default_provider
from .quality import detect_split_anomalies, detect_zombies, validate_tickers
from .returns import get_annual_returns, get_prices
from .screener import screen, screen_dividend, screen_low_volatility

__version__ = "0.1.0"

__all__ = [
    "PriceProvider",
    "average_annual_return",
    "benchmark_bias",
    "detect_split_anomalies",
    "detect_zombies",
    "get_annual_returns",
    "get_prices",
    "max_drawdown",
    "screen",
    "screen_dividend",
    "screen_low_volatility",
    "set_default_provider",
    "validate_tickers",
]
