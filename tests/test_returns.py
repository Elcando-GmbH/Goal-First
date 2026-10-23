import pandas as pd
import pytest

from goalfirst.providers.base import PriceProvider
from goalfirst.returns import annual_returns_from_prices, get_annual_returns, get_prices

from .conftest import prices_from_annual_returns

ANNUAL = {2015: 0.10, 2016: -0.05, 2017: 0.20, 2018: 0.00, 2019: 0.15}


def test_fake_provider_satisfies_protocol(provider):
    assert isinstance(provider, PriceProvider)


def test_annual_returns_match_construction():
    prices = prices_from_annual_returns(ANNUAL)
    result = annual_returns_from_prices(prices)
    assert list(result.index) == sorted(ANNUAL)
    for year, expected in ANNUAL.items():
        assert result[year] == pytest.approx(expected, abs=1e-9)


def test_annual_returns_are_decimals_not_percent():
    prices = prices_from_annual_returns({2020: 0.25})
    assert annual_returns_from_prices(prices)[2020] == pytest.approx(0.25)


def test_years_window_keeps_most_recent():
    prices = prices_from_annual_returns(ANNUAL)
    result = annual_returns_from_prices(prices, years=3)
    assert list(result.index) == [2017, 2018, 2019]


def test_current_year_included_as_year_to_date():
    this_year = pd.Timestamp.today().year
    prices = prices_from_annual_returns({this_year - 1: 0.1, this_year: 0.5})
    prices = prices[prices.index <= pd.Timestamp.today()]  # data only up to today
    result = annual_returns_from_prices(prices)
    assert this_year in result.index
    assert result[this_year - 1] == pytest.approx(0.1)


def test_current_year_can_be_excluded():
    this_year = pd.Timestamp.today().year
    prices = prices_from_annual_returns({this_year - 1: 0.1, this_year: 0.5})
    result = annual_returns_from_prices(prices, include_current_year=False)
    assert this_year not in result.index


def test_years_window_counts_complete_years_only():
    this_year = pd.Timestamp.today().year
    annual = {y: 0.05 for y in range(this_year - 5, this_year + 1)}
    prices = prices_from_annual_returns(annual)
    result = annual_returns_from_prices(prices, years=3)
    assert list(result.index) == [this_year - 3, this_year - 2, this_year - 1, this_year]


def test_empty_prices_give_empty_returns():
    assert annual_returns_from_prices(pd.Series(dtype=float)).empty


def test_get_functions_use_provider(provider):
    prices = prices_from_annual_returns(ANNUAL)
    provider.add("AAA", prices)
    assert get_prices("AAA", provider=provider).equals(prices)
    result = get_annual_returns("AAA", years=20, provider=provider)
    assert result[2017] == pytest.approx(0.20)


def test_unknown_ticker_is_empty_not_error(provider):
    assert get_annual_returns("NOPE", provider=provider).empty
