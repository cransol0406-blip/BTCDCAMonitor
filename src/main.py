"""Main entry point for BTC DCA indicator monitor."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .cache import Cache
from .config import ConfigError, load_config
from .data_sources import DataSourceError, get_btc_daily_history, get_btc_price_usd, get_glassnode_latest_metric, get_market_cap_and_mvrv_history
from .indicators import IndicatorError, calculate_200wma, calculate_ahr999, calculate_gma200, calculate_mvrv_zscore, estimate_ahr999_growth_price
from .message import DisplayMetric, build_message
from .status import get_200wma_status, get_action_suggestion, get_ahr999_status, get_mvrv_status, get_mvrv_zscore_status
from .telegram import send_telegram_message


LOGGER = logging.getLogger(__name__)


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")


def _timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        LOGGER.warning("TIMEZONE 无效，回退到 Asia/Shanghai: %s", name)
        return ZoneInfo("Asia/Shanghai")


def _metric(value: float | None, used_cache: bool = False, is_money: bool = False) -> DisplayMetric:
    return DisplayMetric(value=value, used_cache=used_cache, is_money=is_money)


def run() -> None:
    setup_logging()
    LOGGER.info("开始运行 BTC DCA 指标监控")

    try:
        config = load_config(validate_telegram=True)
    except ConfigError:
        LOGGER.exception("配置校验失败")
        raise

    tz = _timezone(config.timezone)
    now = datetime.now(tz)
    cache = Cache()

    values: dict[str, float | None] = {
        "btc_price": None,
        "ahr999": None,
        "mvrv_zscore": None,
        "mvrv": None,
        "ma_200w": None,
    }
    used_cache = {key: False for key in values}

    try:
        result = get_btc_price_usd(config.coingecko_api_key)
        values["btc_price"] = float(result.value)
        LOGGER.info("BTC价格来源: %s", result.source)
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("BTC价格获取失败: %s", exc)

    daily_prices: list[float] | None = None
    if cache.is_fresh("btc_daily_prices", timedelta(hours=24), now):
        cached_prices = cache.get_data("btc_daily_prices")
        if isinstance(cached_prices, list):
            daily_prices = [float(price) for price in cached_prices]
            LOGGER.info("使用缓存 BTC 日线历史")
    if daily_prices is None:
        try:
            result = get_btc_daily_history(config.coingecko_api_key)
            daily_prices = [float(price) for price in result.value]
            cache.set_data("btc_daily_prices", daily_prices, now)
            LOGGER.info("BTC日线历史来源: %s", result.source)
        except Exception as exc:  # noqa: BLE001
            cached_prices, ok = cache.fallback_data("btc_daily_prices")
            if ok and isinstance(cached_prices, list):
                daily_prices = [float(price) for price in cached_prices]
                LOGGER.warning("BTC日线历史获取失败，使用缓存: %s", exc)
            else:
                LOGGER.warning("BTC日线历史获取失败且无缓存: %s", exc)

    if daily_prices:
        try:
            values["ma_200w"] = calculate_200wma(daily_prices)
            cache.set_value("ma_200w", values["ma_200w"], now)
            if values["btc_price"] is not None:
                gma200 = calculate_gma200(daily_prices)
                estimated_price = estimate_ahr999_growth_price(now.date())
                values["ahr999"] = calculate_ahr999(values["btc_price"], gma200, estimated_price)
                cache.set_value("ahr999", values["ahr999"], now)
        except IndicatorError as exc:
            LOGGER.warning("日线衍生指标计算失败: %s", exc)
    else:
        for key in ("ma_200w", "ahr999"):
            cached_value, ok = cache.fallback_value(key)
            if ok:
                values[key] = float(cached_value)
                used_cache[key] = True
                LOGGER.warning("%s 使用缓存", key)

    history: list[dict[str, float | str]] | None = None
    if cache.is_fresh("market_cap_mvrv_history", timedelta(hours=24), now):
        cached_history = cache.get_data("market_cap_mvrv_history")
        if isinstance(cached_history, list):
            history = cached_history
            LOGGER.info("使用缓存市值/MVRV历史")
    if history is None:
        try:
            result = get_market_cap_and_mvrv_history()
            history = result.value
            cache.set_data("market_cap_mvrv_history", history, now)
            LOGGER.info("市值/MVRV历史来源: %s", result.source)
        except Exception as exc:  # noqa: BLE001
            cached_history, ok = cache.fallback_data("market_cap_mvrv_history")
            if ok and isinstance(cached_history, list):
                history = cached_history
                used_cache["mvrv"] = True
                used_cache["mvrv_zscore"] = True
                LOGGER.warning("市值/MVRV历史获取失败，使用缓存: %s", exc)
            else:
                LOGGER.warning("市值/MVRV历史获取失败且无缓存: %s", exc)

    if config.glassnode_api_key:
        try:
            values["mvrv"] = float(get_glassnode_latest_metric("market/mvrv", config.glassnode_api_key).value)
            LOGGER.info("MVRV 使用 Glassnode")
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Glassnode MVRV 获取失败，回退 Coin Metrics 口径: %s", exc)
        try:
            values["mvrv_zscore"] = float(get_glassnode_latest_metric("market/mvrv_z_score", config.glassnode_api_key).value)
            LOGGER.info("MVRV Z-Score 使用 Glassnode")
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Glassnode MVRV Z-Score 获取失败，回退 Coin Metrics 口径: %s", exc)

    if history and (values["mvrv"] is None or values["mvrv_zscore"] is None):
        try:
            market_caps = [float(row["market_cap"]) for row in history]
            latest = history[-1]
            latest_mvrv = float(latest["mvrv"])
            latest_market_cap = float(latest["market_cap"])
            if values["mvrv"] is None:
                values["mvrv"] = latest_mvrv
                cache.set_value("mvrv", values["mvrv"], now)
            if values["mvrv_zscore"] is None:
                realized_cap = latest_market_cap / latest_mvrv
                values["mvrv_zscore"] = calculate_mvrv_zscore(market_caps, realized_cap)
                cache.set_value("mvrv_zscore", values["mvrv_zscore"], now)
        except (IndicatorError, KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            LOGGER.warning("MVRV/MVRV Z-Score 计算失败: %s", exc)

    for key in ("mvrv", "mvrv_zscore"):
        if values[key] is None:
            cached_value, ok = cache.fallback_value(key)
            if ok:
                values[key] = float(cached_value)
                used_cache[key] = True
                LOGGER.warning("%s 使用缓存", key)

    cache.save()

    statuses = {
        "ahr999": get_ahr999_status(values["ahr999"]),
        "mvrv_zscore": get_mvrv_zscore_status(values["mvrv_zscore"]),
        "mvrv": get_mvrv_status(values["mvrv"]),
        "ma_200w": get_200wma_status(values["btc_price"], values["ma_200w"]),
    }
    suggestion = get_action_suggestion(values, statuses)
    message = build_message(
        monitor_time=now.strftime("%Y-%m-%d %H:%M:%S"),
        metrics={
            "btc_price": _metric(values["btc_price"], used_cache["btc_price"], True),
            "ahr999": _metric(values["ahr999"], used_cache["ahr999"], False),
            "mvrv_zscore": _metric(values["mvrv_zscore"], used_cache["mvrv_zscore"], False),
            "mvrv": _metric(values["mvrv"], used_cache["mvrv"], False),
            "ma_200w": _metric(values["ma_200w"], used_cache["ma_200w"], True),
        },
        statuses=statuses,
        suggestion=suggestion,
    )
    LOGGER.info("消息生成成功")
    send_telegram_message(message, config)
    LOGGER.info("程序结束")


if __name__ == "__main__":
    run()
