"""Goal First — reference implementation of the stock selection framework.

Goal first, constraints second, rank what remains.
"""

from .metrics import average_annual_return, benchmark_bias, max_drawdown
from .providers.base import PriceProvider, set_default_provider
from .returns import get_annual_returns, get_prices

__version__ = "0.1.0"

__all__ = [
    "PriceProvider",
    "average_annual_return",
    "benchmark_bias",
    "get_annual_returns",
    "get_prices",
    "max_drawdown",
    "set_default_provider",
]
