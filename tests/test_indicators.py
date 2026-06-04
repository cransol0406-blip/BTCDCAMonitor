from datetime import date

import pytest

from src.indicators import (
    IndicatorError,
    calculate_200wma,
    calculate_ahr999,
    calculate_gma200,
    calculate_mvrv,
    calculate_mvrv_from_realized_price,
    calculate_mvrv_zscore,
    estimate_ahr999_growth_price,
)


def test_calculate_200wma_uses_latest_1400_prices():
    prices = list(range(1, 1501))
    assert calculate_200wma(prices) == pytest.approx(sum(range(101, 1501)) / 1400)


def test_calculate_200wma_rejects_short_history():
    with pytest.raises(IndicatorError):
        calculate_200wma([1.0] * 1399)


def test_calculate_gma200():
    assert calculate_gma200([4.0] * 200) == pytest.approx(4.0)


def test_calculate_gma200_rejects_non_positive_price():
    with pytest.raises(IndicatorError):
        calculate_gma200([1.0] * 199 + [0.0])


def test_calculate_mvrv():
    assert calculate_mvrv(200.0, 100.0) == pytest.approx(2.0)


def test_calculate_mvrv_rejects_zero_realized_cap():
    with pytest.raises(IndicatorError):
        calculate_mvrv(200.0, 0.0)


def test_calculate_mvrv_from_realized_price():
    assert calculate_mvrv_from_realized_price(60000.0, 30000.0) == pytest.approx(2.0)


def test_calculate_mvrv_zscore():
    caps = [100.0, 120.0, 140.0, 160.0]
    assert calculate_mvrv_zscore(caps, 100.0) > 0


def test_calculate_mvrv_zscore_rejects_empty_input():
    with pytest.raises(IndicatorError):
        calculate_mvrv_zscore([], 100.0)


def test_calculate_ahr999():
    assert calculate_ahr999(100.0, 50.0, 200.0) == pytest.approx(1.0)


def test_estimate_ahr999_growth_price_is_positive():
    assert estimate_ahr999_growth_price(date(2026, 6, 4)) > 0
