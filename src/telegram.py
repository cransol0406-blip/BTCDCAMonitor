"""Telegram Bot API client."""

from __future__ import annotations

import logging

import requests

from .config import Config


LOGGER = logging.getLogger(__name__)


class TelegramError(RuntimeError):
    """Raised when Telegram message sending fails."""


def send_telegram_message(text: str, config: Config) -> None:
    url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
    response = requests.post(
        url,
        json={"chat_id": config.telegram_chat_id, "text": text},
        timeout=12,
    )
    if not response.ok:
        raise TelegramError(f"Telegram发送失败: HTTP {response.status_code} {response.text[:200]}")
    LOGGER.info("Telegram消息发送成功")
