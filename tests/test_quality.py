import pandas as pd

from goalfirst.quality import detect_split_anomalies, detect_zombies, validate_tickers

from .conftest import prices_from_annual_returns

CLEAN = {y: 0.08 for y in range(2005, 2025)}            # 20 complete years, nothing odd
SHORT = {y: 0.08 for y in range(2021, 2025)}            # 4 complete years
SPIKE_NO_SPLIT = {**CLEAN, 2015: 1.5}                   # +150 % in 2015, no split
SPIKE_WITH_SPLIT = {**CLEAN, 2015: 1.5}                 # same, but a 2:1 split on record


# -- validate_tickers --------------------------------------------------------

def test_validate_sorts_into_three_groups(provider):
    provider.add("CLEAN", prices_from_annual_returns(CLEAN))
    provider.add("SHORT", prices_from_annual_returns(SHORT))
    result = validate_tickers(["CLEAN", "NOPE", "SHORT"], min_years=10, provider=provider)
    assert result["valid"] == ["CLEAN"]
    assert result["invalid"] == ["NOPE"]
    assert result["insufficient_history"] == ["SHORT"]


def test_validate_reports_available_years(provider):
    provider.add("CLEAN", prices_from_annual_returns(CLEAN))
    provider.add("SHORT", prices_from_annual_returns(SHORT))
    result = validate_tickers(["CLEAN", "SHORT", "NOPE"], provider=provider)
    assert result["years"] == {"CLEAN": 20, "SHORT": 4, "NOPE": 0}


def test_validate_does_not_count_running_year(provider):
    this_year = pd.Timestamp.today().year
    annual = {y: 0.05 for y in range(this_year - 3, this_year + 1)}  # 3 complete + running
    provider.add("YTD", prices_from_annual_returns(annual))
    result = validate_tickers(["YTD"], min_years=4, provider=provider)
    assert result["years"]["YTD"] == 3
    assert result["insufficient_history"] == ["YTD"]


def test_validate_preserves_input_order(provider):
    for t in ["C", "A", "B"]:
        provider.add(t, prices_from_annual_returns(CLEAN))
    assert validate_tickers(["C", "A", "B"], provider=provider)["valid"] == ["C", "A", "B"]


# -- detect_split_anomalies --------------------------------------------------

def test_clean_series_has_no_anomalies(provider):
    provider.add("CLEAN", prices_from_annual_returns(CLEAN))
    assert detect_split_anomalies("CLEAN", provider=provider) == []


def test_spike_without_split_is_flagged_for_check(provider):
    provider.add("SPK", prices_from_annual_returns(SPIKE_NO_SPLIT))
    flags = detect_split_anomalies("SPK", provider=provider)
    assert len(flags) == 1
    f = flags[0]
    assert f["year"] == 2015
    assert f["split_in_year"] is False
    assert f["split_ratio"] is None
    assert f["assessment"] == "check"
    assert abs(f["annual_return"] - 1.5) < 1e-9


def test_spike_with_split_is_plausible(provider):
    splits = pd.Series({pd.Timestamp("2015-06-15"): 2.0})
    provider.add("SPL", prices_from_annual_returns(SPIKE_WITH_SPLIT), splits=splits)
    flags = detect_split_anomalies("SPL", provider=provider)
    assert len(flags) == 1
    assert flags[0]["split_in_year"] is True
    assert flags[0]["split_ratio"] == 2.0
    assert flags[0]["assessment"] == "plausible"


def test_negative_spike_is_flagged_too(provider):
    provider.add("CRASH", prices_from_annual_returns({**CLEAN, 2008: -0.85}))
    flags = detect_split_anomalies("CRASH", provider=provider)
    assert [f["year"] for f in flags] == [2008]


def test_threshold_is_respected(provider):
    provider.add("MILD", prices_from_annual_returns({**CLEAN, 2015: 0.5}))
    assert detect_split_anomalies("MILD", threshold=0.8, provider=provider) == []
    assert len(detect_split_anomalies("MILD", threshold=0.4, provider=provider)) == 1


def test_unknown_ticker_gives_empty_list(provider):
    assert detect_split_anomalies("NOPE", provider=provider) == []


# -- detect_zombies ------------------------------------------------------------

def test_clean_liquid_stock_is_not_a_zombie(provider):
    provider.add("CLEAN", prices_from_annual_returns(CLEAN))
    result = detect_zombies("CLEAN", provider=provider)
    assert result["classification"] == "none"
    assert result["flagged_periods"] == []


def test_active_zombie_by_low_volume(provider):
    prices = prices_from_annual_returns(CLEAN)
    volume = pd.Series(8_200.0, index=prices.index)
    provider.add("THIN", prices, volume=volume)
    result = detect_zombies("THIN", min_avg_volume=100_000, provider=provider)
    assert result["classification"] == "active"
    assert result["avg_volume_1y"] == 8_200.0
    assert result["flagged_periods"][0]["type"] == "active"


def test_illiquid_long_ago_but_liquid_now_is_not_active(provider):
    prices = prices_from_annual_returns(CLEAN)
    volume = pd.Series(8_200.0, index=prices.index)
    volume[volume.index.year >= 2023] = 2_000_000.0
    provider.add("RECOVERED", prices, volume=volume)
    assert detect_zombies("RECOVERED", provider=provider)["classification"] == "none"


def test_reactivated_zombie_jal_pattern(provider):
    # flat at ~0.9 for three years, then +200 %
    annual = {2007: 0.10, 2008: -0.95, 2009: 0.01, 2010: -0.01, 2011: 0.02, 2012: 2.0, 2013: 0.05}
    prices = prices_from_annual_returns(annual, start_price=20.0)
    provider.add("JAL", prices)
    result = detect_zombies("JAL", price_floor=2.0, provider=provider)
    assert result["classification"] == "reactivated"
    period = result["flagged_periods"][0]
    assert period["type"] == "reactivated"
    assert period["start"] == 2009
    assert period["end"] == 2012


def test_penny_stock_that_moves_is_not_dormant(provider):
    # low price, but +-20 % every year: no dormancy, so no reactivation
    annual = {2010: 0.2, 2011: -0.2, 2012: 0.2, 2013: -0.2, 2014: 2.0}
    prices = prices_from_annual_returns(annual, start_price=1.0)
    provider.add("PENNY", prices)
    assert detect_zombies("PENNY", provider=provider)["classification"] == "none"


def test_flat_but_expensive_stock_is_not_dormant(provider):
    # utility at 80: flat returns but far above the floor
    annual = {2010: 0.01, 2011: -0.01, 2012: 0.02, 2013: 1.0}
    prices = prices_from_annual_returns(annual, start_price=80.0)
    provider.add("UTIL", prices)
    assert detect_zombies("UTIL", provider=provider)["classification"] == "none"


def test_single_dormant_year_is_not_enough(provider):
    annual = {2010: 0.3, 2011: 0.01, 2012: 1.5}
    prices = prices_from_annual_returns(annual, start_price=1.0)
    provider.add("ONE", prices)
    assert detect_zombies("ONE", provider=provider)["classification"] == "none"


def test_both_patterns_are_reported_together(provider):
    annual = {2009: 0.01, 2010: -0.01, 2011: 2.0, 2012: 0.05}
    prices = prices_from_annual_returns(annual, start_price=1.0)
    volume = pd.Series(500.0, index=prices.index)
    provider.add("BOTH", prices, volume=volume)
    assert detect_zombies("BOTH", provider=provider)["classification"] == "both"


def test_unknown_ticker_is_none_not_error(provider):
    result = detect_zombies("NOPE", provider=provider)
    assert result["classification"] == "none"
    assert result["avg_volume_1y"] is None
