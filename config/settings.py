"""Load and validate settings from environment."""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    steam_api_key: str
    telegram_bot_token: str
    telegram_chat_id: str
    steam_id: str
    app_id: int
    threshold_percent: float
    poll_interval_minutes: int
    notify_on_drop: bool

    @classmethod
    def from_env(cls) -> "Settings":
        steam_api_key = os.getenv("STEAM_API_KEY", "").strip()
        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        steam_id = os.getenv("STEAM_ID", "").strip()
        app_id_str = os.getenv("APP_ID", "730").strip()
        threshold_str = os.getenv("THRESHOLD_PERCENT", "50").strip()
        poll_str = os.getenv("POLL_INTERVAL_MINUTES", "10").strip()
        notify_drop = os.getenv("NOTIFY_ON_DROP", "false").strip().lower() in ("true", "1", "yes")

        if not steam_api_key:
            raise ValueError("STEAM_API_KEY is required")
        if not telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not telegram_chat_id:
            raise ValueError("TELEGRAM_CHAT_ID is required")
        if not steam_id:
            raise ValueError("STEAM_ID is required")

        try:
            app_id = int(app_id_str)
        except ValueError:
            raise ValueError(f"APP_ID must be an integer, got: {app_id_str}")

        try:
            threshold_percent = float(threshold_str)
        except ValueError:
            raise ValueError(f"THRESHOLD_PERCENT must be a number, got: {threshold_str}")
        if threshold_percent <= 0:
            raise ValueError("THRESHOLD_PERCENT must be positive")

        try:
            poll_interval_minutes = int(poll_str)
        except ValueError:
            raise ValueError(f"POLL_INTERVAL_MINUTES must be an integer, got: {poll_str}")
        if poll_interval_minutes < 1:
            raise ValueError("POLL_INTERVAL_MINUTES must be >= 1")

        return cls(
            steam_api_key=steam_api_key,
            telegram_bot_token=telegram_bot_token,
            telegram_chat_id=telegram_chat_id,
            steam_id=steam_id,
            app_id=app_id,
            threshold_percent=threshold_percent,
            poll_interval_minutes=poll_interval_minutes,
            notify_on_drop=notify_drop,
        )


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings
