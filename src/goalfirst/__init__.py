"""Goal First — reference implementation of the stock selection framework.

Goal first, constraints second, rank what remains.
"""

from .providers.base import PriceProvider, set_default_provider
from .returns import get_annual_returns, get_prices

__version__ = "0.1.0"

__all__ = [
    "PriceProvider",
    "get_annual_returns",
    "get_prices",
    "set_default_provider",
]
