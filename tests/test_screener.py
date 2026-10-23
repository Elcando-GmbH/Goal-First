import pytest

from goalfirst.screener import screen, screen_dividend, screen_low_volatility

from .conftest import prices_from_annual_returns

YEARS = list(range(2005, 2025))                       # 20 complete years

BENCH = {y: 0.08 for y in YEARS}
WINNER = {y: 0.12 for y in YEARS}                     # beats bench every year, no loss
STRONG = {y: 0.20 for y in YEARS}                     # beats bench, higher avg
LOSER = {y: 0.05 for y in YEARS}                      # never beats bench
LOSSY = {**WINNER, **{y: -0.10 for y in YEARS[:8]}}   # 8/20 loss years = 0.40
SHORT = {y: 0.30 for y in YEARS[-5:]}                 # only 5 complete years


@pytest.fixture
def universe(provider):
    provider.add("^GSPC", prices_from_annual_returns(BENCH))
    provider.add("WIN", prices_from_annual_returns(WINNER))
    provider.add("STRONG", prices_from_annual_returns(STRONG))
    provider.add("LOSE", prices_from_annual_returns(LOSER))
    provider.add("LOSSY", prices_from_annual_returns(LOSSY))
    provider.add("SHORT", prices_from_annual_returns(SHORT))
    return provider


# -- screen -------------------------------------------------------------------

def test_screen_columns_and_order(universe):
    df = screen(["WIN", "STRONG", "LOSE", "LOSSY", "SHORT", "NOPE"], provider=universe)
    assert list(df.columns) == ["ticker", "bias_score", "loss_year_ratio", "avg_annual_return"]
    assert list(df["ticker"]) == ["STRONG", "WIN"]          # ranked by avg return desc


def test_screen_goal_threshold_excludes(universe):
    df = screen(["LOSE"], provider=universe)
    assert df.empty


def test_screen_loss_ratio_constraint_excludes(universe):
    df = screen(["LOSSY"], max_loss_ratio=0.25, provider=universe)
    assert df.empty
    df = screen(["LOSSY"], max_loss_ratio=0.50, provider=universe)
    assert list(df["ticker"]) == ["LOSSY"]
    assert df["loss_year_ratio"].iloc[0] == pytest.approx(0.40)


def test_screen_min_years_excludes_short_history(universe):
    assert screen(["SHORT"], min_years=10, provider=universe).empty
    assert list(screen(["SHORT"], min_years=5, provider=universe)["ticker"]) == ["SHORT"]


def test_screen_values(universe):
    df = screen(["WIN"], provider=universe)
    assert df["bias_score"].iloc[0] == pytest.approx(1.0)
    assert df["loss_year_ratio"].iloc[0] == 0.0
    assert df["avg_annual_return"].iloc[0] == pytest.approx(0.12)


def test_screen_empty_universe_returns_empty_frame_with_columns(universe):
    df = screen([], provider=universe)
    assert df.empty and list(df.columns) == ["ticker", "bias_score", "loss_year_ratio",
                                              "avg_annual_return"]


# -- screen_dividend ---------------------------------------------------------

def test_dividend_ranks_by_total_return_not_yield(provider):
    provider.add("HIYIELD", prices_from_annual_returns({y: 0.04 for y in YEARS}),
                 dividend_yield=0.08, payout_ratio=0.60)
    provider.add("GROWER", prices_from_annual_returns({y: 0.12 for y in YEARS}),
                 dividend_yield=0.04, payout_ratio=0.50)
    df = screen_dividend(["HIYIELD", "GROWER"], provider=provider)
    assert list(df.columns) == ["ticker", "dividend_yield", "loss_year_ratio", "payout_ratio",
                                "avg_annual_return"]
    assert list(df["ticker"]) == ["GROWER", "HIYIELD"]


def test_dividend_goal_threshold(provider):
    provider.add("LOW", prices_from_annual_returns(WINNER), dividend_yield=0.02, payout_ratio=0.5)
    assert screen_dividend(["LOW"], min_yield=0.035, provider=provider).empty


def test_dividend_payout_constraint(provider):
    provider.add("ATT", prices_from_annual_returns(WINNER), dividend_yield=0.07, payout_ratio=0.95)
    assert screen_dividend(["ATT"], max_payout_ratio=0.90, provider=provider).empty


def test_dividend_loss_ratio_constraint(provider):
    provider.add("LOSSY", prices_from_annual_returns(LOSSY), dividend_yield=0.05, payout_ratio=0.5)
    assert screen_dividend(["LOSSY"], provider=provider).empty


def test_dividend_missing_data_excludes(provider):
    provider.add("NOYIELD", prices_from_annual_returns(WINNER), dividend_yield=None, payout_ratio=0.5)
    provider.add("NOPAYOUT", prices_from_annual_returns(WINNER), dividend_yield=0.05, payout_ratio=None)
    assert screen_dividend(["NOYIELD", "NOPAYOUT"], provider=provider).empty


# -- screen_low_volatility ---------------------------------------------------

def test_low_vol_ranks_ascending(provider):
    calm = {y: 0.06 + (0.01 if y % 2 else -0.01) for y in YEARS}       # std ~0.01
    wild = {y: 0.20 + (0.15 if y % 2 else -0.15) for y in YEARS}       # std ~0.15, no loss years
    provider.add("CALM", prices_from_annual_returns(calm))
    provider.add("WILD", prices_from_annual_returns(wild))
    df = screen_low_volatility(["WILD", "CALM"], provider=provider)
    assert list(df.columns) == ["ticker", "annual_std", "loss_year_ratio", "worst_year_return"]
    assert list(df["ticker"]) == ["CALM", "WILD"]


def test_low_vol_single_year_drawdown_constraint(provider):
    one_bad_year = {**{y: 0.05 for y in YEARS}, 2008: -0.38}
    provider.add("CRASH", prices_from_annual_returns(one_bad_year))
    assert screen_low_volatility(["CRASH"], max_single_drawdown=0.30, provider=provider).empty
    df = screen_low_volatility(["CRASH"], max_single_drawdown=0.40, provider=provider)
    assert df["worst_year_return"].iloc[0] == pytest.approx(-0.38)


def test_low_vol_loss_ratio_constraint(provider):
    provider.add("LOSSY", prices_from_annual_returns(LOSSY))
    assert screen_low_volatility(["LOSSY"], provider=provider).empty
