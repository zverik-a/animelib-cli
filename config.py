"""Application configuration loaded from the environment."""

import os

BASE_URL = os.getenv("ANIMELIB_API_URL", "https://hapi.hentaicdn.org/api/anime").rstrip("/")
API_ROOT = BASE_URL.removesuffix("/anime")
BEARER_TOKEN = os.getenv("ANIMELIB_BEARER_TOKEN", "").strip()

HEADERS = {
    "User-Agent": "CLii/1.0",
    "Referer": "https://hentaicdn.org/",
    "Origin": "https://hentaicdn.org",
}
if BEARER_TOKEN:
    HEADERS["Authorization"] = f"Bearer {BEARER_TOKEN}"

REQUEST_TIMEOUT = 15
