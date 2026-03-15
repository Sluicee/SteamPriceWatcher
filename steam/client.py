"""Facade over steam inventory and market APIs."""

from typing import Optional

from config.settings import PROVIDER_STEAMAPIS, PROVIDER_STEAM_OFFICIAL, Settings
from steam.providers import SteamApisProvider, SteamOfficialProvider
from steam.providers.base import SteamProvider


def _create_provider(settings: Settings) -> SteamProvider:
    """Create the configured Steam data provider."""
    if settings.steam_provider == PROVIDER_STEAMAPIS:
        return SteamApisProvider(api_key=settings.steam_api_key)
    if settings.steam_provider == PROVIDER_STEAM_OFFICIAL:
        return SteamOfficialProvider(api_key=settings.steam_web_api_key)
    raise ValueError(f"Unknown STEAM_PROVIDER: {settings.steam_provider}")


class SteamClient:
    """Thin wrapper over the configured Steam provider; caches market prices by app_id."""

    def __init__(self, settings: Settings) -> None:
        self._provider = _create_provider(settings)
        self._market_cache: Optional[dict[str, float]] = None
        self._market_cache_app_id: Optional[int] = None

    def get_inventory_market_names(
        self,
        steam_id: str,
        app_id: int,
    ) -> list[str]:
        """Return unique market_hash_name list for marketable items in inventory."""
        return self._provider.get_inventory_market_names(steam_id, app_id)

    def get_market_prices(
        self,
        app_id: int,
        item_names: list[str] | None = None,
        use_cache: bool = True,
    ) -> dict[str, float]:
        """
        Return market_hash_name -> latest price (USD).
        item_names: optional list to fetch only those (used by steam_official); ignored by steamapis.
        If use_cache is True and app_id matches previous call, returns cached result.
        """
        if use_cache and self._market_cache is not None and self._market_cache_app_id == app_id:
            return self._market_cache
        prices = self._provider.get_market_prices(
            app_id, item_names=item_names, use_cache=False
        )
        if use_cache:
            self._market_cache = prices
            self._market_cache_app_id = app_id
        return prices
