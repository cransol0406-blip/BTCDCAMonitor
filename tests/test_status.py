from src.status import (
    UNAVAILABLE_STATUS,
    get_200wma_status,
    get_action_suggestion,
    get_ahr999_status,
    get_mvrv_status,
    get_mvrv_zscore_status,
)


def test_ahr999_boundaries():
    assert get_ahr999_status(None) == UNAVAILABLE_STATUS
    assert get_ahr999_status(0.44) == "低估区（< 0.45）"
    assert get_ahr999_status(0.45) == "定投区（0.45 - 1.2）"
    assert get_ahr999_status(1.2) == "定投区（0.45 - 1.2）"
    assert get_ahr999_status(1.21) == "偏高区（> 1.2）"


def test_mvrv_zscore_boundaries():
    assert get_mvrv_zscore_status(None) == UNAVAILABLE_STATUS
    assert get_mvrv_zscore_status(-0.01) == "低估区（< 0）"
    assert get_mvrv_zscore_status(0.0) == "中性偏低（0 - 1.5）"
    assert get_mvrv_zscore_status(1.5) == "中性偏高（1.5 - 4）"
    assert get_mvrv_zscore_status(4.0) == "高估区（>= 4）"


def test_mvrv_boundaries():
    assert get_mvrv_status(None) == UNAVAILABLE_STATUS
    assert get_mvrv_status(0.99) == "低估区（< 1）"
    assert get_mvrv_status(1.0) == "偏低估区（1 - 1.5）"
    assert get_mvrv_status(1.5) == "中性区（1.5 - 3）"
    assert get_mvrv_status(3.0) == "偏高区（>= 3）"


def test_200wma_boundaries():
    assert get_200wma_status(None, 100.0) == UNAVAILABLE_STATUS
    assert get_200wma_status(99.0, 100.0) == "价格低于200周均线，进入长期低估观察区"
    assert get_200wma_status(100.0, 100.0) == "价格接近200周均线，处于低位观察区"
    assert get_200wma_status(119.99, 100.0) == "价格接近200周均线，处于低位观察区"
    assert get_200wma_status(120.0, 100.0) == "价格高于200周均线，未进入极端低估区"


def test_action_suggestion_extreme_low():
    data = {"btc_price": 90.0, "ahr999": 0.4, "mvrv_zscore": -0.1, "mvrv": 0.9, "ma_200w": 100.0}
    statuses = {"ahr999": "低估区（< 0.45）", "mvrv_zscore": "低估区（< 0）", "mvrv": "低估区（< 1）", "ma_200w": "价格低于200周均线，进入长期低估观察区"}
    assert "战略加仓区" in get_action_suggestion(data, statuses)


def test_action_suggestion_incomplete_data():
    data = {"btc_price": 100.0, "ahr999": None, "mvrv_zscore": None, "mvrv": 1.5, "ma_200w": 90.0}
    statuses = {"ahr999": UNAVAILABLE_STATUS, "mvrv_zscore": UNAVAILABLE_STATUS, "mvrv": "中性区（1.5 - 3）", "ma_200w": "价格接近200周均线，处于低位观察区"}
    assert "部分关键指标获取失败" in get_action_suggestion(data, statuses)


def test_action_suggestion_no_price():
    data = {"btc_price": None, "ahr999": 1.0, "mvrv_zscore": 1.0, "mvrv": 1.5, "ma_200w": 90.0}
    statuses = {"ahr999": "定投区（0.45 - 1.2）", "mvrv_zscore": "中性偏低（0 - 1.5）", "mvrv": "中性区（1.5 - 3）", "ma_200w": UNAVAILABLE_STATUS}
    assert "BTC价格获取失败" in get_action_suggestion(data, statuses)
