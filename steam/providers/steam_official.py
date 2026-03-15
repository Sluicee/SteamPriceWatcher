"""Steam Official provider: inventory via Steam Web API, prices via Community Market priceoverview."""

import time
import urllib.parse
from typing import Any

import requests

# Steam Web API (inventory + schema)
STEAM_API_BASE = "https://api.steampowered.com"
# Community Market (no key)
MARKET_PRICE_BASE = "https://steamcommunity.com/market/priceoverview/"
# Delay between price requests to reduce 429 risk (seconds)
PRICE_REQUEST_DELAY = 1.2
# Retry delay after 429 (seconds)
RETRY_AFTER_429 = 30


def _parse_price_string(s: str) -> float:
    """Parse price string like '$1.23' or '$1,234.56' to float."""
    if not s or not isinstance(s, str):
        return 0.0
    s = s.replace("$", "").replace(",", "").replace(" ", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def _fetch_schema(app_id: int, api_key: str) -> dict[str, dict[str, Any]]:
    """Fetch item schema; return dict classid -> {market_hash_name, marketable}."""
    url = f"{STEAM_API_BASE}/IEconItems_{app_id}/GetSchema/v2/"
    params = {"key": api_key}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()
    result = data.get("result") or {}
    items = result.get("items") or []
    out: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        classid = item.get("classid") or item.get("id")
        if not classid:
            continue
        name = (
            item.get("market_hash_name")
            or item.get("item_name")
            or item.get("name")
            or ""
        )
        if not name or not isinstance(name, str):
            continue
        marketable = item.get("marketable") == 1 or item.get("marketable") is True
        out[str(classid)] = {"market_hash_name": name, "marketable": marketable}
    return out


def _fetch_player_items(
    app_id: int, steam_id: str, api_key: str
) -> list[dict[str, Any]]:
    """Fetch player inventory items; return list of item dicts with classid."""
    url = f"{STEAM_API_BASE}/IEconItems_{app_id}/GetPlayerItems/v1/"
    params = {"key": api_key, "steamid": steam_id}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()
    result = data.get("result") or {}
    items = result.get("items") or []
    return items if isinstance(items, list) else []


def _inventory_names_from_schema_and_items(
    schema: dict[str, dict[str, Any]], raw_items: list[Any]
) -> list[str]:
    """Map raw player items to unique market_hash_names (marketable only)."""
    seen: set[str] = set()
    names: list[str] = []
    for it in raw_items:
        if not isinstance(it, dict):
            continue
        classid = it.get("classid") or it.get("id")
        if not classid:
            continue
        info = schema.get(str(classid))
        if not info or not info.get("marketable"):
            continue
        name = info.get("market_hash_name")
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def _fetch_price_for_item(
    app_id: int, market_hash_name: str, session: requests.Session
) -> float:
    """One priceoverview request; return price in USD or 0.0."""
    params = {
        "appid": app_id,
        "currency": 1,
        "market_hash_name": market_hash_name,
    }
    url = MARKET_PRICE_BASE + "?" + urllib.parse.urlencode(params)
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 429:
            return -1.0  # signal to retry later
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            return 0.0
        # Prefer lowest_price; fallback to median_price
        price_str = data.get("lowest_price") or data.get("median_price")
        return _parse_price_string(price_str or "")
    except (requests.RequestException, ValueError):
        return 0.0


def _fetch_prices_for_items(
    app_id: int,
    item_names: list[str],
    delay: float = PRICE_REQUEST_DELAY,
    retry_delay: float = RETRY_AFTER_429,
) -> dict[str, float]:
    """Fetch prices for given market_hash_names via priceoverview; throttle and retry on 429."""
    result: dict[str, float] = {}
    session = requests.Session()
    session.headers.setdefault(
        "User-Agent",
        "Mozilla/5.0 (compatible; SteamPriceWatcher/1.0)",
    )
    for i, name in enumerate(item_names):
        if i > 0:
            time.sleep(delay)
        price = _fetch_price_for_item(app_id, name, session)
        if price < 0:
            time.sleep(retry_delay)
            price = _fetch_price_for_item(app_id, name, session)
        result[name] = max(0.0, price)
    return result


class SteamOfficialProvider:
    """Provider using Steam Web API (inventory + schema) and Community Market priceoverview."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._schema_cache: dict[int, dict[str, dict[str, Any]]] = {}

    def get_inventory_market_names(self, steam_id: str, app_id: int) -> list[str]:
        """Return unique market_hash_name list for marketable items in inventory."""
        if app_id not in self._schema_cache:
            self._schema_cache[app_id] = _fetch_schema(app_id, self._api_key)
        schema = self._schema_cache[app_id]
        raw_items = _fetch_player_items(app_id, steam_id, self._api_key)
        return _inventory_names_from_schema_and_items(schema, raw_items)

    def get_market_prices(
        self,
        app_id: int,
        item_names: list[str] | None,
        use_cache: bool,
    ) -> dict[str, float]:
        """Return market_hash_name -> price (USD). Fetches only item_names; throttled."""
        del use_cache  # caching done by SteamClient
        if not item_names:
            return {}
        return _fetch_prices_for_items(app_id, item_names)
