"""Shared Zenserp API client with DuckDuckGo fallback."""

import requests
from config import ZENSERP_API_KEY

ZENSERP_BASE = "https://app.zenserp.com/api/v2/search"
_zenserp_exhausted = False


def zenserp_search(query: str, tbm: str | None = None, num: int = 10) -> dict | None:
    """Call Zenserp API. Returns parsed JSON or None on failure.

    Args:
        query: Search query string.
        tbm: Search type — None for web, 'shop' for shopping, 'nws' for news.
        num: Number of results (max ~100 per page).

    Returns:
        Parsed JSON dict, or None if the API call failed or quota exhausted.
    """
    global _zenserp_exhausted
    if not ZENSERP_API_KEY or _zenserp_exhausted:
        return None

    params = {"q": query}
    if tbm:
        params["tbm"] = tbm

    try:
        resp = requests.get(
            ZENSERP_BASE,
            params=params,
            headers={"apikey": ZENSERP_API_KEY},
            timeout=15,
        )
        if resp.status_code == 403:
            # Quota exhausted or invalid key — stop trying for this session
            _zenserp_exhausted = True
            return None
        resp.raise_for_status()
        result = resp.json()
        # Ensure we always return a dict (some endpoints may return a list)
        if isinstance(result, dict):
            return result
        return None
    except Exception:
        return None
