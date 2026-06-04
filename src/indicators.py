"""Indicator calculations and validation."""

from __future__ import annotations

import math
from datetime import date
from statistics import pstdev
from typing import Iterable


BTC_GENESIS_DATE = date(2009, 1, 3)


class IndicatorError(ValueError):
    """Raised when an indicator cannot be calculated from provided data."""


def _to_float_list(values: Iterable[float]) -> list[float]:
    converted = [float(value) for value in values]
    if not converted:
        raise IndicatorError("输入数据为空")
    return converted


def calculate_200wma(daily_prices: Iterable[float]) -> float:
    prices = _to_float_list(daily_prices)
    if len(prices) < 1400:
        raise IndicatorError("200周均线至少需要 1400 个日线收盘价")
    recent = prices[-1400:]
    return sum(recent) / len(recent)


def calculate_gma200(daily_prices: Iterable[float]) -> float:
    prices = _to_float_list(daily_prices)
    if len(prices) < 200:
        raise IndicatorError("GMA200 至少需要 200 个日线收盘价")
    recent = prices[-200:]
    if any(price <= 0 for price in recent):
        raise IndicatorError("GMA200 输入价格必须为正数")
    return math.exp(sum(math.log(price) for price in recent) / len(recent))


def calculate_mvrv(market_cap: float, realized_cap: float) -> float:
    if market_cap is None or realized_cap is None:
        raise IndicatorError("Market Cap 和 Realized Cap 不能为空")
    if realized_cap <= 0:
        raise IndicatorError("Realized Cap 必须大于 0")
    return float(market_cap) / float(realized_cap)


def calculate_mvrv_from_realized_price(price: float, realized_price: float) -> float:
    if price is None or realized_price is None:
        raise IndicatorError("BTC 价格和 Realized Price 不能为空")
    if realized_price <= 0:
        raise IndicatorError("Realized Price 必须大于 0")
    return float(price) / float(realized_price)


def calculate_mvrv_zscore(market_caps: Iterable[float], realized_cap: float) -> float:
    caps = _to_float_list(market_caps)
    if len(caps) < 2:
        raise IndicatorError("MVRV Z-Score 至少需要两个历史市值数据点")
    if realized_cap is None or realized_cap <= 0:
        raise IndicatorError("Realized Cap 必须大于 0")
    std = pstdev(caps)
    if std <= 0:
        raise IndicatorError("历史市值标准差必须大于 0")
    return (caps[-1] - float(realized_cap)) / std


def calculate_ahr999(price: float, gma200: float, estimated_price: float) -> float:
    if price is None or gma200 is None or estimated_price is None:
        raise IndicatorError("AHR999 输入不能为空")
    if price <= 0 or gma200 <= 0 or estimated_price <= 0:
        raise IndicatorError("AHR999 输入必须大于 0")
    return (float(price) / float(gma200)) * (float(price) / float(estimated_price))


def estimate_ahr999_growth_price(as_of: date | None = None) -> float:
    """Estimate BTC long-term growth price for AHR999-like calculation.

    This uses the commonly referenced power-law approximation:
    10 ** (5.84 * log10(days_since_genesis) - 17.01). It is not an official
    AHR999 source and is documented as an approximation in README.
    """

    current_date = as_of or date.today()
    days = (current_date - BTC_GENESIS_DATE).days
    if days <= 0:
        raise IndicatorError("估值日期必须晚于 BTC 创世日期")
    return 10 ** (5.84 * math.log10(days) - 17.01)
