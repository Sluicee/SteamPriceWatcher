"""Entry point: parse args, load config, run watcher once or in loop."""

import argparse
import sys

from config import get_settings
from notifier import TelegramNotifier
from steam import SteamClient
from storage import SQLitePriceStore
from watcher import log_inventory_snapshot, run_once, run_loop


def main() -> None:
    parser = argparse.ArgumentParser(description="Steam Price Watcher — уведомления при изменении цен")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Выполнить один проход и выйти",
    )
    args = parser.parse_args()

    try:
        settings = get_settings()
    except ValueError as e:
        print(f"Ошибка конфигурации: {e}", file=sys.stderr)
        sys.exit(1)

    steam_client = SteamClient(api_key=settings.steam_api_key)
    store = SQLitePriceStore()
    notifier = TelegramNotifier(
        bot_token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
    )

    print("Steam Price Watcher запущен (Steam ID: {}, App ID: {})".format(settings.steam_id, settings.app_id), flush=True)
    log_inventory_snapshot(steam_client, settings.steam_id, settings.app_id)

    if args.once:
        run_once(
            steam_client=steam_client,
            store=store,
            notifier=notifier,
            steam_id=settings.steam_id,
            app_id=settings.app_id,
            threshold_percent=settings.threshold_percent,
            notify_on_drop=settings.notify_on_drop,
        )
    else:
        run_loop(
            steam_client=steam_client,
            store=store,
            notifier=notifier,
            steam_id=settings.steam_id,
            app_id=settings.app_id,
            threshold_percent=settings.threshold_percent,
            notify_on_drop=settings.notify_on_drop,
            interval_minutes=settings.poll_interval_minutes,
        )


if __name__ == "__main__":
    main()
