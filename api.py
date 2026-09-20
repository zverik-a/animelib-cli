import requests
from config import BASE_URL, HEADERS

def search_anime(query: str) -> list:
    params = {
        "q": query,
        "fields[0]": "rate_avg",
        "fields[1]": "rate",
        "fields[2]": "releaseDate"
    }

    try:
        response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.RequestException:
        return []

def get_anime_details(slug_url: str) -> dict:
    url = f"{BASE_URL}/{slug_url}"
    params = {
        "fields[0]": "genres",
        "fields[1]": "tags",
        "fields[2]": "releaseDate",
        "fields[3]": "summary",
        "fields[4]": "episodes_count",
        "fields[5]": "episodes",
        "fields[6]": "time",
        "fields[7]": "teams",      # Добавлено
        "fields[8]": "shiki_rate"  # Добавлено
    }

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get("data", {})
    except requests.RequestException:
        return {}

# api.py
def get_anime_episodes(slug_url: str) -> list:
    """Запрос списка эпизодов тайтла."""
    url = "https://hapi.hentaicdn.org/api/episodes"
    params = {
        "anime_id": slug_url
    }

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.RequestException as e:
        print(f"[bold red]Ошибка получения эпизодов:[bold red] {e}")
        return []

# api.py
def get_episode_details(episode_id: int | str) -> dict:
    """Запрос плееров и ссылок на видео для конкретного эпизода."""
    url = f"https://hapi.hentaicdn.org/api/episodes/{episode_id}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get("data", {})
    except requests.RequestException as e:
        print(f"[bold red]Ошибка загрузки плееров:[bold red] {e}")
        return {}