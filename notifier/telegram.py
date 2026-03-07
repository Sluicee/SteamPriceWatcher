"""Send notifications via Telegram bot."""

import asyncio
import html

from aiogram import Bot
from aiogram.enums import ParseMode

from notifier.base import Notifier


class TelegramNotifier(Notifier):
    """Send messages to a Telegram chat using Bot API."""

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._bot = Bot(token=bot_token)
        self._chat_id = chat_id

    def notify(
        self,
        message: str,
        item: str,
        old_price: float,
        new_price: float,
        percent: float,
    ) -> None:
        # Prefer preformatted message (HTML); send with HTML parse mode
        if message:
            asyncio.run(self._send(message, parse_mode=ParseMode.HTML))
        else:
            direction = "📈" if percent >= 0 else "📉"
            text = (
                f"{direction} <b>{html.escape(item)}</b>\n"
                f"Было: ${old_price:.2f} → стало: ${new_price:.2f} ({percent:+.1f}%)"
            )
            asyncio.run(self._send(text, parse_mode=ParseMode.HTML))

    async def _send(self, text: str, parse_mode: ParseMode | None = ParseMode.HTML) -> None:
        kwargs: dict = {"chat_id": self._chat_id, "text": text}
        if parse_mode is not None:
            kwargs["parse_mode"] = parse_mode
        await self._bot.send_message(**kwargs)
