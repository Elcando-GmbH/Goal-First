import math

import pandas as pd
import pytest

from goalfirst.metrics import average_annual_return, benchmark_bias, max_drawdown

# -- average_annual_return ------------------------------------------------

def test_average_matches_guide_example():
    # Guide 2, Part 4: +15 %, -12 %, +23 % -> 8.7 %
    assert average_annual_return([0.15, -0.12, 0.23]) == pytest.approx(0.0867, abs=1e-4)


def test_average_accepts_series():
    s = pd.Series({2020: 0.10, 2021: 0.20})
    assert average_annual_return(s) == pytest.approx(0.15)


def test_average_of_empty_is_nan():
    assert math.isnan(average_annual_return([]))


# -- max_drawdown ----------------------------------------------------------

def test_drawdown_peak_to_trough():
    idx = pd.date_range("2020-01-01", periods=6, freq="D")
    prices = pd.Series([100, 120, 90, 60, 80, 130], index=idx)
    # peak 120 -> trough 60 = -50 %
    assert max_drawdown(prices) == pytest.approx(-0.5)


def test_drawdown_uses_running_peak_not_global_max():
    idx = pd.date_range("2020-01-01", periods=5, freq="D")
    prices = pd.Series([100, 50, 200, 180, 190], index=idx)
    # 100 -> 50 is -50 %; later 200 -> 180 is only -10 %
    assert max_drawdown(prices) == pytest.approx(-0.5)


def test_drawdown_zero_for_monotonic_rise():
    idx = pd.date_range("2020-01-01", periods=4, freq="D")
    assert max_drawdown(pd.Series([1, 2, 3, 4], index=idx)) == 0.0


def test_drawdown_is_negative_or_zero_never_positive():
    idx = pd.date_range("2020-01-01", periods=3, freq="D")
    assert max_drawdown(pd.Series([10, 9, 8], index=idx)) <= 0.0


def test_drawdown_of_empty_is_nan():
    assert math.isnan(max_drawdown(pd.Series(dtype=float)))


# -- benchmark_bias --------------------------------------------------------

def test_bias_score_and_outperformance():
    stock = pd.Series({2019: 0.20, 2020: -0.05, 2021: 0.30, 2022: -0.10})
    bench = pd.Series({2019: 0.10, 2020: 0.00, 2021: 0.20, 2022: -0.20})
    result = benchmark_bias(stock, bench)
    # wins: 2019 (+0.10), 2021 (+0.10), 2022 (+0.10) -> 3/4
    assert result["bias_score"] == pytest.approx(0.75)
    assert result["avg_outperformance"] == pytest.approx(0.10)


def test_bias_only_compares_overlapping_years():
    stock = pd.Series({2019: 0.20, 2020: 0.20, 2021: 0.20})
    bench = pd.Series({2020: 0.10, 2021: 0.30, 2022: 0.00})
    result = benchmark_bias(stock, bench)
    # overlap 2020 (win), 2021 (loss) -> 0.5
    assert result["bias_score"] == pytest.approx(0.5)
    assert result["avg_outperformance"] == pytest.approx(0.10)


def test_bias_equal_return_is_not_a_win():
    stock = pd.Series({2020: 0.10})
    bench = pd.Series({2020: 0.10})
    assert benchmark_bias(stock, bench)["bias_score"] == 0.0


def test_bias_no_wins_gives_nan_outperformance():
    stock = pd.Series({2020: 0.0, 2021: 0.0})
    bench = pd.Series({2020: 0.1, 2021: 0.1})
    result = benchmark_bias(stock, bench)
    assert result["bias_score"] == 0.0
    assert math.isnan(result["avg_outperformance"])


def test_bias_no_overlap_gives_nan():
    result = benchmark_bias(pd.Series({2019: 0.1}), pd.Series({2020: 0.1}))
    assert math.isnan(result["bias_score"])
