"""Steam Official provider: inventory via Steam Community API, prices via Community Market priceoverview."""

import time
import urllib.parse
from typing import Any

import requests

# Steam Community inventory (no key; works for CS2/730 where GetSchema v2 returns 410 Gone)
INVENTORY_BASE = "https://steamcommunity.com/inventory"
DEFAULT_CONTEXT_ID = 2
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


def _fetch_community_inventory(
    steam_id: str, app_id: int, context_id: int = DEFAULT_CONTEXT_ID
) -> list[str]:
    """
    Fetch inventory via Steam Community API (no key).
    Returns unique market_hash_name for marketable items. Handles pagination.
    """
    url = f"{INVENTORY_BASE}/{steam_id}/{app_id}/{context_id}"
    params: dict[str, str | int] = {"l": "english"}
    seen: set[str] = set()
    result: list[str] = []

    while True:
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
        except (requests.RequestException, ValueError) as e:
            raise RuntimeError(f"Failed to fetch Steam Community inventory: {e}") from e

        if data.get("success") != 1:
            return []

        assets = data.get("assets") or []
        descriptions = data.get("descriptions") or []
        desc_by_key: dict[tuple[str, str], dict[str, Any]] = {}
        for d in descriptions:
            if not isinstance(d, dict):
                continue
            cid = d.get("classid")
            iid = d.get("instanceid", "0")
            if cid is not None:
                desc_by_key[(str(cid), str(iid))] = d

        for asset in assets:
            if not isinstance(asset, dict):
                continue
            cid = asset.get("classid")
            iid = asset.get("instanceid", "0")
            if cid is None:
                continue
            key = (str(cid), str(iid))
            desc = desc_by_key.get(key) or desc_by_key.get((str(cid), "0"))
            if not desc or desc.get("marketable") != 1:
                continue
            name = desc.get("market_hash_name")
            if name and isinstance(name, str) and name not in seen:
                seen.add(name)
                result.append(name)

        if not data.get("more_items"):
            break
        last = data.get("last_assetid")
        if not last:
            break
        params["start_assetid"] = last

    return result


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
    """Provider using Steam Community inventory API and Community Market priceoverview (no paid key)."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key  # kept for config compatibility; inventory uses Community API (no key)

    def get_inventory_market_names(self, steam_id: str, app_id: int) -> list[str]:
        """Return unique market_hash_name list for marketable items in inventory."""
        return _fetch_community_inventory(steam_id, app_id)

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
