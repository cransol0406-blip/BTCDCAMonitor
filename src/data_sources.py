"""External data sources with fallbacks and normalized return values."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests


LOGGER = logging.getLogger(__name__)
TIMEOUT_SECONDS = 12
COINMETRICS_BASE_URL = "https://community-api.coinmetrics.io/v4"


@dataclass(frozen=True)
class SourceResult:
    value: Any
    source: str


class DataSourceError(RuntimeError):
    """Raised when all data sources for one metric fail."""


def _get_json(url: str, *, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def _coingecko_headers(api_key: str | None) -> dict[str, str]:
    if not api_key:
        return {}
    return {"x-cg-demo-api-key": api_key}


def get_btc_price_usd(coingecko_api_key: str | None = None) -> SourceResult:
    errors: list[str] = []

    try:
        data = _get_json("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"})
        price = float(data["price"])
        if price <= 0:
            raise ValueError("price <= 0")
        LOGGER.info("BTC价格获取成功: Binance")
        return SourceResult(price, "Binance")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Binance: {exc}")
        LOGGER.warning("BTC价格 Binance 获取失败: %s", exc)

    try:
        data = _get_json(
            "https://api.coingecko.com/api/v3/simple/price",
            headers=_coingecko_headers(coingecko_api_key),
            params={"ids": "bitcoin", "vs_currencies": "usd"},
        )
        price = float(data["bitcoin"]["usd"])
        if price <= 0:
            raise ValueError("price <= 0")
        LOGGER.info("BTC价格获取成功: CoinGecko")
        return SourceResult(price, "CoinGecko")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"CoinGecko: {exc}")
        LOGGER.warning("BTC价格 CoinGecko 获取失败: %s", exc)

    try:
        data = _get_json("https://api.coinbase.com/v2/exchange-rates", params={"currency": "BTC"})
        price = float(data["data"]["rates"]["USD"])
        if price <= 0:
            raise ValueError("price <= 0")
        LOGGER.info("BTC价格获取成功: Coinbase")
        return SourceResult(price, "Coinbase")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Coinbase: {exc}")
        LOGGER.warning("BTC价格 Coinbase 获取失败: %s", exc)

    raise DataSourceError("; ".join(errors))


def get_coinmetrics_asset_metrics(metrics: list[str]) -> list[dict[str, Any]]:
    metric_param = ",".join(metrics)
    data = _get_json(
        f"{COINMETRICS_BASE_URL}/timeseries/asset-metrics",
        params={
            "assets": "btc",
            "metrics": metric_param,
            "frequency": "1d",
            "page_size": "10000",
        },
    )
    rows = data.get("data")
    if not isinstance(rows, list) or not rows:
        raise DataSourceError("Coin Metrics 返回空数据")
    return rows


def get_btc_daily_history(coingecko_api_key: str | None = None) -> SourceResult:
    errors: list[str] = []

    try:
        rows = get_coinmetrics_asset_metrics(["PriceUSD"])
        prices = [float(row["PriceUSD"]) for row in rows if row.get("PriceUSD") is not None]
        if len(prices) < 1400:
            raise ValueError("日线价格少于 1400 个")
        LOGGER.info("BTC日线历史获取成功: Coin Metrics")
        return SourceResult(prices, "Coin Metrics")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Coin Metrics: {exc}")
        LOGGER.warning("BTC日线历史 Coin Metrics 获取失败: %s", exc)

    try:
        data = _get_json(
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            headers=_coingecko_headers(coingecko_api_key),
            params={"vs_currency": "usd", "days": "max", "interval": "daily"},
        )
        prices = [float(point[1]) for point in data.get("prices", []) if len(point) >= 2]
        if len(prices) < 1400:
            raise ValueError("日线价格少于 1400 个")
        LOGGER.info("BTC日线历史获取成功: CoinGecko")
        return SourceResult(prices, "CoinGecko")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"CoinGecko: {exc}")
        LOGGER.warning("BTC日线历史 CoinGecko 获取失败: %s", exc)

    raise DataSourceError("; ".join(errors))


def get_market_cap_and_mvrv_history() -> SourceResult:
    rows = get_coinmetrics_asset_metrics(["CapMrktCurUSD", "CapMVRVCur"])
    normalized: list[dict[str, float | str]] = []
    for row in rows:
        if row.get("CapMrktCurUSD") is None or row.get("CapMVRVCur") is None:
            continue
        normalized.append(
            {
                "time": row["time"],
                "market_cap": float(row["CapMrktCurUSD"]),
                "mvrv": float(row["CapMVRVCur"]),
            }
        )
    if len(normalized) < 2:
        raise DataSourceError("Coin Metrics 市值/MVRV 历史数据不足")
    LOGGER.info("MVRV与市值历史获取成功: Coin Metrics")
    return SourceResult(normalized, "Coin Metrics")


def get_glassnode_latest_metric(metric_path: str, api_key: str | None) -> SourceResult:
    if not api_key:
        raise DataSourceError("未配置 GLASSNODE_API_KEY")
    data = _get_json(
        f"https://api.glassnode.com/v1/metrics/{metric_path}",
        params={"a": "BTC", "api_key": api_key, "i": "24h"},
    )
    if not isinstance(data, list) or not data:
        raise DataSourceError("Glassnode 返回空数据")
    value = data[-1].get("v")
    if value is None:
        raise DataSourceError("Glassnode 指标值为空")
    return SourceResult(float(value), "Glassnode")
