"""Telegram message rendering."""

from __future__ import annotations

from dataclasses import dataclass


FAIL_TEXT = "获取失败"


@dataclass(frozen=True)
class DisplayMetric:
    value: float | None
    used_cache: bool = False
    is_money: bool = False


def format_number(value: float | None, used_cache: bool = False) -> str:
    if value is None:
        return FAIL_TEXT
    suffix = "（使用缓存）" if used_cache else ""
    return f"{value:,.2f}{suffix}"


def format_money(value: float | None, used_cache: bool = False) -> str:
    if value is None:
        return FAIL_TEXT
    suffix = "（使用缓存）" if used_cache else ""
    return f"${value:,.2f}{suffix}"


def _line(label: str, metric: DisplayMetric) -> str:
    formatted = format_money(metric.value, metric.used_cache) if metric.is_money else format_number(metric.value, metric.used_cache)
    return f"{label}：{formatted}"


def build_message(
    monitor_time: str,
    metrics: dict[str, DisplayMetric],
    statuses: dict[str, str],
    suggestion: str,
) -> str:
    return "\n".join(
        [
            "【BTC定投指标监控】",
            "",
            f"时间：{monitor_time}",
            _line("BTC价格", metrics["btc_price"]),
            _line("AHR999指数", metrics["ahr999"]),
            _line("MVRV Z-Score", metrics["mvrv_zscore"]),
            _line("MVRV", metrics["mvrv"]),
            _line("200周均线", metrics["ma_200w"]),
            "",
            "指标状态：",
            f"AHR999：{statuses['ahr999']}",
            f"MVRV Z-Score：{statuses['mvrv_zscore']}",
            f"MVRV：{statuses['mvrv']}",
            f"200周均线：{statuses['ma_200w']}",
            "",
            "操作建议：",
            suggestion,
        ]
    )
