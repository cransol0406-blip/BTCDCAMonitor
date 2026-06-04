"""Small JSON cache used by local runs and GitHub Actions cache."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


LOGGER = logging.getLogger(__name__)


class Cache:
    def __init__(self, path: str | Path = "data/cache.json") -> None:
        self.path = Path(path)
        self._data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            LOGGER.info("缓存文件不存在，将使用空缓存")
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            LOGGER.warning("缓存文件读取失败，将使用空缓存: %s", exc)
            return {}
        if not isinstance(raw, dict):
            LOGGER.warning("缓存文件格式不是 JSON object，将使用空缓存")
            return {}
        return raw

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def get_entry(self, key: str) -> dict[str, Any] | None:
        entry = self._data.get(key)
        return entry if isinstance(entry, dict) else None

    def get_value(self, key: str) -> Any:
        entry = self.get_entry(key)
        if not entry:
            return None
        return entry.get("value")

    def get_data(self, key: str) -> Any:
        entry = self.get_entry(key)
        if not entry:
            return None
        return entry.get("data")

    def set_value(self, key: str, value: Any, now: datetime) -> None:
        self._data[key] = {"updated_at": now.isoformat(), "value": value}

    def set_data(self, key: str, data: Any, now: datetime) -> None:
        self._data[key] = {"updated_at": now.isoformat(), "data": data}

    def is_fresh(self, key: str, max_age: timedelta, now: datetime) -> bool:
        entry = self.get_entry(key)
        if not entry:
            return False
        updated_at = entry.get("updated_at")
        if not isinstance(updated_at, str):
            return False
        try:
            updated = datetime.fromisoformat(updated_at)
        except ValueError:
            return False
        if updated.tzinfo is None and now.tzinfo is not None:
            updated = updated.replace(tzinfo=now.tzinfo)
        return now - updated <= max_age

    def fallback_value(self, key: str) -> tuple[Any, bool]:
        value = self.get_value(key)
        return value, value is not None

    def fallback_data(self, key: str) -> tuple[Any, bool]:
        data = self.get_data(key)
        return data, data is not None
