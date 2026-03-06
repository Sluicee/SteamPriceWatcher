"""SQLite implementation of PriceStore."""

import sqlite3
import time
from pathlib import Path
from typing import Optional

from storage.store import PriceStore, get_price_key

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "prices.db"


class SQLitePriceStore(PriceStore):
    """Store last price and updated_at per (app_id, market_hash_name)."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._path = db_path or DEFAULT_DB_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS price_history (
                    item_key TEXT PRIMARY KEY,
                    app_id INTEGER NOT NULL,
                    market_hash_name TEXT NOT NULL,
                    last_price REAL NOT NULL,
                    updated_at INTEGER NOT NULL
                )
                """
            )

    def get_last_price(self, market_hash_name: str, app_id: int) -> Optional[float]:
        row = None
        with sqlite3.connect(self._path) as conn:
            cur = conn.execute(
                "SELECT last_price FROM price_history WHERE item_key = ?",
                (get_price_key(market_hash_name, app_id),),
            )
            row = cur.fetchone()
        return float(row[0]) if row else None

    def set_last_price(
        self,
        market_hash_name: str,
        app_id: int,
        price: float,
    ) -> None:
        key = get_price_key(market_hash_name, app_id)
        now = int(time.time())
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                """
                INSERT INTO price_history (item_key, app_id, market_hash_name, last_price, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(item_key) DO UPDATE SET
                    last_price = excluded.last_price,
                    updated_at = excluded.updated_at
                """,
                (key, app_id, market_hash_name, price, now),
            )
