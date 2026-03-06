"""Fetch Steam market prices by App ID (SteamApis)."""

import requests
from typing import Any

BASE_URL = "https://api.steamapis.com"


def fetch_market_prices(app_id: int, api_key: str) -> dict[str, float]:
    """
    Fetch current market prices for all items of the app.
    Returns dict: market_hash_name -> latest price in USD (0 if no data).
    """
    url = f"{BASE_URL}/market/items/{app_id}"
    params = {"api_key": api_key}
    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
    except (requests.RequestException, ValueError) as e:
        raise RuntimeError(f"Failed to fetch market prices: {e}") from e

    result: dict[str, float] = {}
    items = data.get("data") or []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("market_hash_name")
        if not name or not isinstance(name, str):
            continue
        prices = item.get("prices")
        if isinstance(prices, dict) and "latest" in prices:
            try:
                result[name] = float(prices["latest"])
            except (TypeError, ValueError):
                result[name] = 0.0
        else:
            result[name] = 0.0
    return result
