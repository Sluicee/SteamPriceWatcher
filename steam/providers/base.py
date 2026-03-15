"""Abstract interface for Steam inventory and market data providers."""

from typing import Protocol


class SteamProvider(Protocol):
    """Provider of Steam inventory and market prices."""

    def get_inventory_market_names(self, steam_id: str, app_id: int) -> list[str]:
        """Return unique market_hash_name list for marketable items in inventory."""
        ...

    def get_market_prices(
        self,
        app_id: int,
        item_names: list[str] | None,
        use_cache: bool,
    ) -> dict[str, float]:
        """
        Return market_hash_name -> price (USD).
        item_names: if provided, only these items may be fetched (provider may ignore for bulk APIs).
        use_cache: use provider/client cache when True.
        """
        ...
