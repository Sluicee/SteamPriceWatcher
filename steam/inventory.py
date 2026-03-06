"""Fetch Steam inventory by Steam ID and App ID (SteamApis)."""

import requests
from typing import Any

# SteamApis base URL
BASE_URL = "https://api.steamapis.com"
# Context ID for CS2 and most games
DEFAULT_CONTEXT_ID = 2


def fetch_inventory(
    steam_id: str,
    app_id: int,
    api_key: str,
    context_id: int = DEFAULT_CONTEXT_ID,
) -> list[str]:
    """
    Fetch inventory and return list of unique market_hash_name for marketable items.

    Returns empty list on error or if inventory is private/empty.
    """
    url = f"{BASE_URL}/steam/inventory/{steam_id}/{app_id}/{context_id}"
    params = {"api_key": api_key}
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
    except (requests.RequestException, ValueError) as e:
        raise RuntimeError(f"Failed to fetch inventory: {e}") from e

    if data.get("success") != 1:
        return []

    descriptions = data.get("descriptions") or []
    seen: set[str] = set()
    result: list[str] = []
    for desc in descriptions:
        if not isinstance(desc, dict):
            continue
        # Only include marketable items
        if desc.get("marketable") != 1:
            continue
        name = desc.get("market_hash_name")
        if name and isinstance(name, str) and name not in seen:
            seen.add(name)
            result.append(name)
    return result
