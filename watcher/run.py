"""Watcher loop: fetch inventory, get prices, compare with storage, notify on threshold."""

import html
import time

from config import get_settings
from notifier.base import Notifier
from steam import SteamClient
from storage import PriceStore


def log_inventory_snapshot(
    steam_client: SteamClient,
    steam_id: str,
    app_id: int,
) -> None:
    """Print to console at startup: each item with price and total sum."""
    def out(msg: str) -> None:
        print(msg, flush=True)

    try:
        names = steam_client.get_inventory_market_names(steam_id, app_id)
    except Exception as e:
        print(f"Ошибка загрузки инвентаря: {e}", flush=True)
        return

    if not names:
        out("Инвентарь пуст или недоступен (Steam ID: {}, App ID: {}).".format(steam_id, app_id))
        return

    try:
        prices = steam_client.get_market_prices(app_id, use_cache=False)
    except Exception as e:
        print(f"Ошибка загрузки цен: {e}", flush=True)
        return

    total = 0.0
    out("--- Инвентарь (старт) ---")
    for name in sorted(names):
        price = prices.get(name, 0.0)
        total += price
        out(f"  {name}: ${price:.2f}")
    out("  ---")
    out(f"  Итого: ${total:.2f}")
    out("------------------------")


def _percent_change(old: float, new: float) -> float:
    if old <= 0:
        return 100.0 if new > 0 else 0.0
    return ((new - old) / old) * 100.0


def _format_message(item: str, old_price: float, new_price: float, percent: float) -> str:
    direction = "📈" if percent >= 0 else "📉"
    return (
        f"{direction} <b>{html.escape(item)}</b>\n"
        f"Было: ${old_price:.2f} → стало: ${new_price:.2f} ({percent:+.1f}%)"
    )


def run_once(
    steam_client: SteamClient,
    store: PriceStore,
    notifier: Notifier,
    steam_id: str,
    app_id: int,
    threshold_percent: float,
    notify_on_drop: bool,
    min_price_usd: float = 0.0,
) -> None:
    """
    Single iteration: load inventory, get prices, compare with reference, notify when needed.
    Референсная цена обновляется только при первом визите предмета и после уведомления.
    """
    names = steam_client.get_inventory_market_names(steam_id, app_id)
    if not names:
        return
    prices = steam_client.get_market_prices(app_id, use_cache=True)
    for name in names:
        new_price = prices.get(name, 0.0)
        if new_price <= 0:
            continue
        old_price = store.get_last_price(name, app_id)
        if old_price is None:
            store.set_last_price(name, app_id, new_price)
            continue
        percent = _percent_change(old_price, new_price)
        if new_price < min_price_usd:
            # Дешёвые предметы не уведомляем и референс не обновляем
            continue
        if percent >= threshold_percent:
            message = _format_message(name, old_price, new_price, percent)
            notifier.notify(message, name, old_price, new_price, percent)
            store.set_last_price(name, app_id, new_price)
        elif notify_on_drop and percent <= -threshold_percent:
            message = _format_message(name, old_price, new_price, percent)
            notifier.notify(message, name, old_price, new_price, percent)
            store.set_last_price(name, app_id, new_price)
        # else: порог не достигнут — референс не обновляем, сравниваем с той же ценой в следующий раз


def run_loop(
    steam_client: SteamClient,
    store: PriceStore,
    notifier: Notifier,
    steam_id: str,
    app_id: int,
    threshold_percent: float,
    notify_on_drop: bool,
    interval_minutes: int,
    min_price_usd: float = 0.0,
) -> None:
    """Run watcher every interval_minutes until interrupted."""
    interval_seconds = interval_minutes * 60
    while True:
        print("[Watcher] Проверка инвентаря...", flush=True)
        run_once(
            steam_client=steam_client,
            store=store,
            notifier=notifier,
            steam_id=steam_id,
            app_id=app_id,
            threshold_percent=threshold_percent,
            notify_on_drop=notify_on_drop,
            min_price_usd=min_price_usd,
        )
        print("[Watcher] Следующая проверка через {} мин.".format(interval_minutes), flush=True)
        time.sleep(interval_seconds)
