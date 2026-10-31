"""Transform API responses into values used by the terminal UI."""

from typing import Any
from urllib.parse import urljoin

import requests

CDN_DOMAINS = (
    "https://video1.cdnlibs.org/.%D0%B0s/",
    "https://video2.cdnlibs.org/",
    "https://cache.hentaicdn.org/",
)
VIDEO_HEADERS = {"User-Agent": "CLii/1.0", "Referer": "https://animelib.org/"}


def extract_best_subtitle(subtitles: list[dict[str, Any]]) -> str | None:
    """Choose ASS subtitles when available, otherwise VTT."""
    for preferred in ("ass", "vtt"):
        for subtitle in subtitles or []:
            if subtitle.get("format") == preferred and subtitle.get("src"):
                return subtitle["src"]
    return None


def extract_summary_text(summary_data: Any) -> str:
    """Extract plain text from the API's paragraph-based summary format."""
    if not isinstance(summary_data, dict):
        return ""
    parts: list[str] = []
    for block in summary_data.get("content", []):
        if not isinstance(block, dict):
            continue
        for node in block.get("content", []):
            if isinstance(node, dict) and node.get("type") == "text":
                value = node.get("text")
                if isinstance(value, str):
                    parts.append(value)
    return " ".join(part.strip() for part in parts if part.strip())


def resolve_mp4_url(href: str) -> str | None:
    """Resolve a relative CDN path, preferring a host that answers HEAD."""
    if not href:
        return None
    if href.startswith(("http://", "https://")):
        return href

    candidates = [urljoin(domain, href.lstrip("/")) for domain in CDN_DOMAINS]
    for url in candidates:
        try:
            response = requests.head(url, headers=VIDEO_HEADERS, timeout=3, allow_redirects=True)
            if response.status_code in (200, 206):
                return url
        except requests.RequestException:
            continue
    # Some hosts reject HEAD while still serving the media to mpv.
    return candidates[0]


def parse_players(players_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize Animelib and Kodik player records for the UI."""
    parsed: list[dict[str, Any]] = []
    for item in players_data or []:
        if not isinstance(item, dict):
            continue
        player_name = item.get("player", "Unknown")
        team = item.get("team") or {}
        translation = item.get("translation_type") or {}
        common = {
            "player": player_name,
            "team": team.get("name", "Неизвестная команда") if isinstance(team, dict) else "Неизвестная команда",
            "translation": translation.get("label", "Озвучка") if isinstance(translation, dict) else "Озвучка",
            "sub_url": extract_best_subtitle(item.get("subtitles", [])),
        }

        if player_name == "Animelib" and isinstance(item.get("video"), dict):
            links: dict[str, str] = {}
            for quality in item["video"].get("quality", []):
                if not isinstance(quality, dict):
                    continue
                url = resolve_mp4_url(str(quality.get("href", "")))
                if url:
                    label = str(quality.get("quality", "?"))
                    links[f"{label}p"] = url
            if links:
                parsed.append({**common, "type": "direct", "links": links})

        elif player_name == "Kodik" and item.get("src"):
            src = str(item["src"])
            iframe_url = f"https:{src}" if src.startswith("//") else src
            parsed.append({**common, "type": "kodik", "url": iframe_url})

    return parsed
