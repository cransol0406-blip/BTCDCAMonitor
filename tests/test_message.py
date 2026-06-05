from src.message import DisplayMetric, build_message, format_money, format_number


def _sample_metrics():
    return {
        "btc_price": DisplayMetric(68500.0, is_money=True),
        "ahr999": DisplayMetric(0.92345, decimals=4),
        "mvrv_zscore": DisplayMetric(1.15),
        "mvrv": DisplayMetric(1.82),
        "ma_200w": DisplayMetric(43200.0, is_money=True),
    }


def _sample_statuses():
    return {
        "ahr999": "定投区（0.45 - 1.2）",
        "mvrv_zscore": "中性偏低（0 - 1.5）",
        "mvrv": "中性区（1.5 - 3）",
        "ma_200w": "价格高于200周均线，未进入极端低估区",
    }


def test_format_money():
    assert format_money(68500.0) == "$68,500.00"
    assert format_money(43200.0, used_cache=True) == "$43,200.00（使用缓存）"
    assert format_money(None) == "获取失败"


def test_format_number():
    assert format_number(1.15) == "1.15"
    assert format_number(0.92345, decimals=4) == "0.9235"
    assert format_number(-0.15) == "-0.15"
    assert format_number(None) == "获取失败"


def test_build_message_standard_format():
    message = build_message("2026-06-04 18:30:00", _sample_metrics(), _sample_statuses(), "普通定投，不触发加倍；等待 AHR999 < 0.45、MVRV < 1 或价格接近200周均线时再提高定投金额。")
    assert message.startswith("【BTC定投指标监控】\n\n")
    assert "时间：2026-06-04 18:30:00" in message
    assert "BTC价格：$68,500.00" in message
    assert "AHR999指数：0.9235" in message
    assert "MVRV Z-Score：1.15" in message
    assert "MVRV：1.82" in message
    assert "200周均线：$43,200.00" in message
    assert "指标状态：" in message
    assert "操作建议：" in message


def test_build_message_failure_and_cache_text():
    metrics = _sample_metrics()
    metrics["ahr999"] = DisplayMetric(None)
    metrics["mvrv_zscore"] = DisplayMetric(1.15, used_cache=True)
    metrics["ma_200w"] = DisplayMetric(43200.0, used_cache=True, is_money=True)
    statuses = _sample_statuses()
    statuses["ahr999"] = "无法判断"
    message = build_message("2026-06-04 18:30:00", metrics, statuses, "部分关键指标获取失败，暂不调整定投策略，建议等待下一次监控结果。")
    assert "AHR999指数：获取失败" in message
    assert "MVRV Z-Score：1.15（使用缓存）" in message
    assert "200周均线：$43,200.00（使用缓存）" in message
    assert "AHR999：无法判断" in message
