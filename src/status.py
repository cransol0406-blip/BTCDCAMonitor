"""Indicator status and action suggestion rules."""

from __future__ import annotations

from dataclasses import dataclass


UNAVAILABLE_STATUS = "无法判断"


@dataclass(frozen=True)
class Thresholds:
    ahr999_low: float = 0.45
    ahr999_dca_high: float = 1.2
    mvrv_z_low: float = 0.0
    mvrv_z_neutral_low_high: float = 1.5
    mvrv_z_high: float = 4.0
    mvrv_low: float = 1.0
    mvrv_low_high: float = 1.5
    mvrv_neutral_high: float = 3.0
    wma_near_ratio: float = 1.2


THRESHOLDS = Thresholds()


def _is_missing(value: float | None) -> bool:
    return value is None


def get_ahr999_status(value: float | None) -> str:
    if _is_missing(value):
        return UNAVAILABLE_STATUS
    if value < THRESHOLDS.ahr999_low:
        return "低估区（< 0.45）"
    if value <= THRESHOLDS.ahr999_dca_high:
        return "定投区（0.45 - 1.2）"
    return "偏高区（> 1.2）"


def get_mvrv_zscore_status(value: float | None) -> str:
    if _is_missing(value):
        return UNAVAILABLE_STATUS
    if value < THRESHOLDS.mvrv_z_low:
        return "低估区（< 0）"
    if value < THRESHOLDS.mvrv_z_neutral_low_high:
        return "中性偏低（0 - 1.5）"
    if value < THRESHOLDS.mvrv_z_high:
        return "中性偏高（1.5 - 4）"
    return "高估区（>= 4）"


def get_mvrv_status(value: float | None) -> str:
    if _is_missing(value):
        return UNAVAILABLE_STATUS
    if value < THRESHOLDS.mvrv_low:
        return "低估区（< 1）"
    if value < THRESHOLDS.mvrv_low_high:
        return "偏低估区（1 - 1.5）"
    if value < THRESHOLDS.mvrv_neutral_high:
        return "中性区（1.5 - 3）"
    return "偏高区（>= 3）"


def get_200wma_status(price: float | None, ma_200w: float | None) -> str:
    if _is_missing(price) or _is_missing(ma_200w) or ma_200w <= 0:
        return UNAVAILABLE_STATUS
    ratio = price / ma_200w
    if ratio < 1:
        return "价格低于200周均线，进入长期低估观察区"
    if ratio < THRESHOLDS.wma_near_ratio:
        return "价格接近200周均线，处于低位观察区"
    return "价格高于200周均线，未进入极端低估区"


def get_action_suggestion(data: dict[str, float | None], statuses: dict[str, str]) -> str:
    price = data.get("btc_price")
    ahr999 = data.get("ahr999")
    mvrv_zscore = data.get("mvrv_zscore")
    mvrv = data.get("mvrv")
    ma_200w = data.get("ma_200w")

    if price is None:
        return "BTC价格获取失败，本次不生成操作建议，请检查数据源或等待下一次运行。"

    key_statuses = [
        statuses.get("ahr999"),
        statuses.get("mvrv_zscore"),
        statuses.get("mvrv"),
        statuses.get("ma_200w"),
    ]
    if sum(status == UNAVAILABLE_STATUS for status in key_statuses) >= 2:
        return "部分关键指标获取失败，暂不调整定投策略，建议等待下一次监控结果。"

    extreme_signals = 0
    if ahr999 is not None and ahr999 < THRESHOLDS.ahr999_low:
        extreme_signals += 1
    if mvrv_zscore is not None and mvrv_zscore < THRESHOLDS.mvrv_z_low:
        extreme_signals += 1
    if mvrv is not None and mvrv < THRESHOLDS.mvrv_low:
        extreme_signals += 1
    if ma_200w is not None and ma_200w > 0 and price <= ma_200w:
        extreme_signals += 1
    if extreme_signals >= 3:
        return "多个低估信号同时触发，可进入战略加仓区，适合分批提高定投金额，但不建议一次性满仓。"

    enhanced_signals = 0
    if ahr999 is not None and ahr999 <= THRESHOLDS.ahr999_dca_high:
        enhanced_signals += 1
    if mvrv_zscore is not None and mvrv_zscore < THRESHOLDS.mvrv_z_neutral_low_high:
        enhanced_signals += 1
    if mvrv is not None and mvrv < THRESHOLDS.mvrv_low_high:
        enhanced_signals += 1
    if ma_200w is not None and ma_200w > 0 and price / ma_200w < THRESHOLDS.wma_near_ratio:
        enhanced_signals += 1
    if enhanced_signals >= 2:
        return "部分低估信号出现，可适当提高定投金额，建议继续分批执行。"

    price_far_above_200wma = ma_200w is not None and ma_200w > 0 and price / ma_200w >= THRESHOLDS.wma_near_ratio
    if (
        ahr999 is not None
        and ahr999 > THRESHOLDS.ahr999_dca_high
        and ((mvrv is not None and mvrv >= THRESHOLDS.mvrv_neutral_high) or (mvrv_zscore is not None and mvrv_zscore >= THRESHOLDS.mvrv_z_high))
        and price_far_above_200wma
    ):
        return "当前未出现低估信号，可降低定投强度或仅观察，不建议追高加仓。"

    return "普通定投，不触发加倍；等待 AHR999 < 0.45、MVRV < 1 或价格接近200周均线时再提高定投金额。"
