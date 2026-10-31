"""Small HTTP client for the HentaiCDN API."""

from typing import Any
from urllib.parse import quote

import requests
from rich.console import Console

from config import API_ROOT, BASE_URL, HEADERS, REQUEST_TIMEOUT

console = Console()


def _request(url: str, *, params: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("API returned an unexpected response format")
        return payload
    except (requests.RequestException, ValueError) as exc:
        console.print(f"[bold red]API request failed:[/bold red] {exc}")
        return {}


def search_anime(query: str) -> list[dict[str, Any]]:
    """Search for anime by title."""
    payload = _request(BASE_URL, params={"q": query, "fields[0]": "rate_avg", "fields[1]": "rate", "fields[2]": "releaseDate"})
    data = payload.get("data", [])
    return data if isinstance(data, list) else []


def get_anime_details(slug_url: str) -> dict[str, Any]:
    """Fetch details for an anime slug."""
    fields = ("genres", "tags", "releaseDate", "summary", "episodes_count", "episodes", "time", "teams", "shiki_rate")
    params = {f"fields[{idx}]": field for idx, field in enumerate(fields)}
    payload = _request(f"{BASE_URL}/{quote(str(slug_url), safe='')}", params=params)
    data = payload.get("data", {})
    return data if isinstance(data, dict) else {}


def get_anime_episodes(anime_id: int | str) -> list[dict[str, Any]]:
    """Fetch episodes for an anime ID."""
    payload = _request(f"{API_ROOT}/episodes", params={"anime_id": str(anime_id)})
    data = payload.get("data", [])
    return data if isinstance(data, list) else []


def get_episode_details(episode_id: int | str) -> dict[str, Any]:
    """Fetch available players for an episode."""
    payload = _request(f"{API_ROOT}/episodes/{quote(str(episode_id), safe='')}")
    data = payload.get("data", {})
    return data if isinstance(data, dict) else {}
