"""Notifiers: abstract base and Telegram implementation."""

from notifier.base import Notifier
from notifier.telegram import TelegramNotifier

__all__ = ["Notifier", "TelegramNotifier"]
