"""Load and validate settings from environment."""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


PROVIDER_STEAMAPIS = "steamapis"
PROVIDER_STEAM_OFFICIAL = "steam_official"


@dataclass
class Settings:
    steam_provider: str
    steam_api_key: str
    steam_web_api_key: str
    telegram_bot_token: str
    telegram_chat_id: str
    steam_id: str
    app_id: int
    threshold_percent: float
    poll_interval_minutes: int
    notify_on_drop: bool
    min_price_usd: float

    @classmethod
    def from_env(cls) -> "Settings":
        steam_provider = os.getenv("STEAM_PROVIDER", PROVIDER_STEAMAPIS).strip().lower()
        if steam_provider not in (PROVIDER_STEAMAPIS, PROVIDER_STEAM_OFFICIAL):
            raise ValueError(
                f"STEAM_PROVIDER must be '{PROVIDER_STEAMAPIS}' or '{PROVIDER_STEAM_OFFICIAL}', got: {steam_provider}"
            )

        steam_api_key = os.getenv("STEAM_API_KEY", "").strip()
        steam_web_api_key = os.getenv("STEAM_WEB_API_KEY", "").strip()
        if steam_provider == PROVIDER_STEAMAPIS and not steam_api_key:
            raise ValueError("STEAM_API_KEY is required when STEAM_PROVIDER=steamapis")
        # STEAM_WEB_API_KEY optional for steam_official (inventory uses Community API without key)

        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        steam_id = os.getenv("STEAM_ID", "").strip()
        app_id_str = os.getenv("APP_ID", "730").strip()
        threshold_str = os.getenv("THRESHOLD_PERCENT", "50").strip()
        poll_str = os.getenv("POLL_INTERVAL_MINUTES", "10").strip()
        notify_drop = os.getenv("NOTIFY_ON_DROP", "false").strip().lower() in ("true", "1", "yes")
        min_price_str = os.getenv("MIN_PRICE_USD", "0").strip()
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

        try:
            min_price_usd = float(min_price_str)
        except ValueError:
            raise ValueError(f"MIN_PRICE_USD must be a number, got: {min_price_str}")
        if min_price_usd < 0:
            raise ValueError("MIN_PRICE_USD must be >= 0")

        return cls(
            steam_provider=steam_provider,
            steam_api_key=steam_api_key,
            steam_web_api_key=steam_web_api_key,
            telegram_bot_token=telegram_bot_token,
            telegram_chat_id=telegram_chat_id,
            steam_id=steam_id,
            app_id=app_id,
            threshold_percent=threshold_percent,
            poll_interval_minutes=poll_interval_minutes,
            notify_on_drop=notify_drop,
            min_price_usd=min_price_usd,
        )


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings
