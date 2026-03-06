"""Storage interface: get/set last price by (market_hash_name + app_id)."""

from abc import ABC, abstractmethod
from typing import Optional


def get_price_key(market_hash_name: str, app_id: int) -> str:
    """Unique key for an item: app_id + market_hash_name."""
    return f"{app_id}\t{market_hash_name}"


class PriceStore(ABC):
    """Abstract store for last known price and optional metadata."""

    @abstractmethod
    def get_last_price(self, market_hash_name: str, app_id: int) -> Optional[float]:
        """Return last stored price or None if never seen."""
        ...

    @abstractmethod
    def set_last_price(
        self,
        market_hash_name: str,
        app_id: int,
        price: float,
    ) -> None:
        """Store last price and update timestamp."""
        ...
