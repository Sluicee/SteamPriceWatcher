"""Abstract notifier interface."""

from abc import ABC, abstractmethod


class Notifier(ABC):
    """Notify when price change exceeds threshold."""

    @abstractmethod
    def notify(
        self,
        message: str,
        item: str,
        old_price: float,
        new_price: float,
        percent: float,
    ) -> None:
        """
        Send notification.
        message: preformatted text to send
        item: market_hash_name
        old_price, new_price: in USD
        percent: absolute change in percent (e.g. 50 for +50% or -30 for -30%)
        """
        ...
