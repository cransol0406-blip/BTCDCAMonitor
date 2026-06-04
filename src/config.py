"""Environment configuration for the BTC DCA indicator monitor."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


DEFAULT_TIMEZONE = "Asia/Shanghai"


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    telegram_chat_id: str
    coingecko_api_key: str | None
    coinmetrics_api_key: str | None
    glassnode_api_key: str | None
    timezone: str


class ConfigError(RuntimeError):
    """Raised when required runtime configuration is missing."""


def load_config(validate_telegram: bool = True) -> Config:
    load_dotenv()

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if validate_telegram and (not telegram_bot_token or not telegram_chat_id):
        raise ConfigError("缺少 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID")

    return Config(
        telegram_bot_token=telegram_bot_token,
        telegram_chat_id=telegram_chat_id,
        coingecko_api_key=os.getenv("COINGECKO_API_KEY", "").strip() or None,
        coinmetrics_api_key=os.getenv("COINMETRICS_API_KEY", "").strip() or None,
        glassnode_api_key=os.getenv("GLASSNODE_API_KEY", "").strip() or None,
        timezone=os.getenv("TIMEZONE", DEFAULT_TIMEZONE).strip() or DEFAULT_TIMEZONE,
    )
