"""SteamApis provider: inventory and market data via api.steamapis.com."""

from steam.inventory import fetch_inventory
from steam.market import fetch_market_prices


class SteamApisProvider:
    """Provider using SteamApis (single request for all prices; item_names ignored)."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def get_inventory_market_names(self, steam_id: str, app_id: int) -> list[str]:
        """Return unique market_hash_name list for marketable items in inventory."""
        return fetch_inventory(steam_id, app_id, self._api_key)

    def get_market_prices(
        self,
        app_id: int,
        item_names: list[str] | None,
        use_cache: bool,
    ) -> dict[str, float]:
        """Return market_hash_name -> latest price (USD) for all items of the app. item_names ignored."""
        del item_names, use_cache  # bulk API: one request returns all items
        return fetch_market_prices(app_id, self._api_key)
