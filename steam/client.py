"""Facade over steam inventory and market APIs."""

from typing import Optional

from steam.inventory import fetch_inventory
from steam.market import fetch_market_prices


class SteamClient:
    """Single provider for inventory and market data (SteamApis)."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._market_cache: Optional[dict[str, float]] = None
        self._market_cache_app_id: Optional[int] = None

    def get_inventory_market_names(
        self,
        steam_id: str,
        app_id: int,
    ) -> list[str]:
        """Return unique market_hash_name list for marketable items in inventory."""
        return fetch_inventory(steam_id, app_id, self._api_key)

    def get_market_prices(self, app_id: int, use_cache: bool = True) -> dict[str, float]:
        """
        Return market_hash_name -> latest price (USD) for all items of the app.
        If use_cache is True and app_id matches previous call, returns cached result.
        """
        if use_cache and self._market_cache is not None and self._market_cache_app_id == app_id:
            return self._market_cache
        prices = fetch_market_prices(app_id, self._api_key)
        if use_cache:
            self._market_cache = prices
            self._market_cache_app_id = app_id
        return prices
