from datetime import datetime, timedelta, timezone

from src.cache import Cache


def test_cache_missing_file(tmp_path):
    cache = Cache(tmp_path / "missing.json")
    assert cache.get_value("x") is None


def test_cache_corrupt_file(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text("{bad", encoding="utf-8")
    cache = Cache(path)
    assert cache.get_value("x") is None


def test_cache_read_write_value(tmp_path):
    path = tmp_path / "cache.json"
    now = datetime(2026, 6, 4, tzinfo=timezone.utc)
    cache = Cache(path)
    cache.set_value("mvrv", 1.82, now)
    cache.save()

    reloaded = Cache(path)
    assert reloaded.get_value("mvrv") == 1.82


def test_cache_read_write_data(tmp_path):
    path = tmp_path / "cache.json"
    now = datetime(2026, 6, 4, tzinfo=timezone.utc)
    cache = Cache(path)
    cache.set_data("prices", [1, 2, 3], now)
    cache.save()

    reloaded = Cache(path)
    assert reloaded.get_data("prices") == [1, 2, 3]


def test_cache_freshness(tmp_path):
    path = tmp_path / "cache.json"
    now = datetime(2026, 6, 4, tzinfo=timezone.utc)
    cache = Cache(path)
    cache.set_value("x", 1, now)
    assert cache.is_fresh("x", timedelta(hours=1), now + timedelta(minutes=30))
    assert not cache.is_fresh("x", timedelta(hours=1), now + timedelta(hours=2))


def test_cache_fallback(tmp_path):
    cache = Cache(tmp_path / "cache.json")
    cache.set_value("x", 1.2, datetime(2026, 6, 4, tzinfo=timezone.utc))
    assert cache.fallback_value("x") == (1.2, True)
    assert cache.fallback_value("missing") == (None, False)
