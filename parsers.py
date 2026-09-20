# parsers.py
import requests
import re   

CDN_DOMAINS = [
    "https://video1.cdnlibs.org/.%D0%B0s/",
    "https://video2.cdnlibs.org",
    "https://cache.hentaicdn.org"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
    "Referer": "https://animelib.org/"
}


def get_kodik_m3u8(iframe_url: str) -> str | None:
    """Извлекает прямую .m3u8 ссылку из iframe Kodik."""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
        "Referer": "https://kodikplayer.com/"
    }

    try:
        # 1. Получаем HTML iframe страницы
        res = requests.get(iframe_url, headers=headers, timeout=5)
        res.raise_for_status()
        html = res.text

        # 2. Извлекаем параметры видео из JS (domain, urlParams, videoType)
        domain_match = re.search(r'var\s+urlParams\s*=\s*\'([^\']+)\'', html)
        video_type_match = re.search(r'var\s+type\s*=\s*\'([^\']+)\'', html)
        video_id_match = re.search(r'var\s+id\s*=\s*\'([^\']+)\'', html)
        hash_match = re.search(r'var\s+hash\s*=\s*\'([^\']+)\'', html)

        if not (domain_match and video_type_match and video_id_match and hash_match):
            return None

        # 3. Делаем POST запрос к API Kodik для получения ссылки на поток
        api_url = f"https://kodikplayer.com/g連続/{video_type_match.group(1)}/{video_id_match.group(1)}/{hash_match.group(1)}"
        
        data = {
            "d": "animelib.org",
            "d_sign": "ex",
            "pd": "animelib.org",
            "pd_sign": "ex",
            "ref": "",
            "ref_sign": "ex",
            "bad_user": "true",
            "type": video_type_match.group(1),
            "hash": hash_match.group(1),
            "id": video_id_match.group(1)
        }

        api_res = requests.post(api_url, data=data, headers=headers, timeout=5)
        api_res.raise_for_status()
        links = api_res.json().get("links", {})

        # Выбираем максимальное доступное качество (720p, 480p, 360p и т.д.)
        for q in ["720", "480", "360"]:
            if q in links:
                m3u8_path = links[q][0]["src"]
                # Расшифровываем rot13 / base64 если ссылка зашифрована
                if not m3u8_path.startswith("http"):
                    import base64
                    # Переворачиваем rot13/base64 если Kodik применяет шифрование
                    m3u8_path = base64.b64decode(m3u8_path.translate(str.maketrans(
                        "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
                        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
                    ))).decode("utf-8")
                
                return f"https:{m3u8_path}" if m3u8_path.startswith("//") else m3u8_path

    except Exception:
        return None

    return None

def extract_best_subtitle(subtitles_list: list) -> str | None:
    """Возвращает URL субтитров (.ass в приоритете, иначе .vtt)."""
    if not subtitles_list:
        return None
    
    ass_sub = next((s.get("src") for s in subtitles_list if s.get("format") == "ass"), None)
    if ass_sub:
        return ass_sub
        
    vtt_sub = next((s.get("src") for s in subtitles_list if s.get("format") == "vtt"), None)
    return vtt_sub




def extract_summary_text(summary_data: dict) -> str:
    """Извлекает чистый текст из структуры JSON summary."""
    if not summary_data or not isinstance(summary_data, dict):
        return ""
    
    text_parts = []
    content_list = summary_data.get("content", [])
    
    for paragraph in content_list:
        if paragraph.get("type") == "paragraph":
            for text_node in paragraph.get("content", []):
                if text_node.get("type") == "text":
                    text_parts.append(text_node.get("text", ""))
                    
    return " ".join(text_parts).strip()

# parsers.py
def parse_players(players_data: list) -> list:
    """Форматирует массив плееров в структуру для UI."""
    parsed = []
    
    for item in players_data:
        player_name = item.get("player", "Unknown")
        team_name = item.get("team", {}).get("name", "Неизвестная команда")
        trans_type = item.get("translation_type", {}).get("label", "Озвучка")
        
        # Извлекаем ссылку на субтитры, если они есть в объекте плеера
        sub_url = extract_best_subtitle(item.get("subtitles", []))
        
        if player_name == "Animelib" and "video" in item:
            qualities = item.get("video", {}).get("quality", [])
            links = {}
            
            for q in qualities:
                href = q.get("href", "")
                quality_label = f"{q.get('quality')}p"
                valid_url = resolve_mp4_url(href)
                if valid_url:
                    links[quality_label] = valid_url

            if links:
                parsed.append({
                    "type": "direct",
                    "player": player_name,
                    "team": team_name,
                    "translation": trans_type,
                    "links": links,
                    "subtitle": sub_url
                })
            
        elif player_name == "Kodik" and "src" in item:
            src = item.get("src", "")
            iframe_url = f"https:{src}" if src.startswith("//") else src
            
            parsed.append({
                "type": "iframe",
                "player": player_name,
                "team": team_name,
                "translation": trans_type,
                "url": iframe_url,
                "subtitle": sub_url
            })

    return parsed

def resolve_mp4_url(href: str) -> str | None:
    """Проверяет CDN-домены по порядку и возвращает первый рабочий URL."""
    if href.startswith("http://") or href.startswith("https://"):
        return href

    # Нормализация двойных слэшей в пути
    clean_href = "/" + href.lstrip("/")

    for domain in CDN_DOMAINS:
        full_url = f"{domain}{clean_href}"
        try:
            # Выполняем HEAD-запрос для проверки статуса 200/206 без скачивания файла
            res = requests.head(full_url, headers=HEADERS, timeout=3, allow_redirects=True)
            if res.status_code in (200, 206):
                return full_url
        except requests.RequestException:
            continue

    # Запасной вариант, если HEAD-запросы блокируются
    return f"{CDN_DOMAINS[0]}{clean_href}"


def parse_players(players_data: list) -> list:
    """Форматирует массив плееров и извлекает ссылки на субтитры."""
    parsed = []
    
    for item in players_data:
        player_name = item.get("player", "Unknown")
        team_name = item.get("team", {}).get("name", "Неизвестная команда")
        trans_type = item.get("translation_type", {}).get("label", "Озвучка")
        # Пропускаем всё, кроме Animelib
        if player_name != "Animelib" or "video" not in item:
            continue
        
        # Извлечение субтитров (если есть)
        sub_url = None
        subtitles_list = item.get("subtitles", [])
        if subtitles_list:
            # Ищем сначала .ass, затем .vtt
            ass_sub = next((s.get("src") for s in subtitles_list if s.get("format") == "ass"), None)
            vtt_sub = next((s.get("src") for s in subtitles_list if s.get("format") == "vtt"), None)
            sub_url = ass_sub or vtt_sub

        if player_name == "Animelib" and "video" in item:
            qualities = item.get("video", {}).get("quality", [])
            links = {}
            
            for q in qualities:
                href = q.get("href", "")
                quality_label = f"{q.get('quality')}p"
                valid_url = resolve_mp4_url(href)
                if valid_url:
                    links[quality_label] = valid_url

            if links:
                parsed.append({
                    "type": "direct",
                    "player": player_name,
                    "team": team_name,
                    "translation": trans_type,
                    "links": links,
                    "sub_url": sub_url
                })
            
        # parsers.py (обновление ветки Kodik)
        elif player_name == "Kodik" and "src" in item:
            src = item.get("src", "")
            iframe_url = f"https:{src}" if src.startswith("//") else src
            
            parsed.append({
                "type": "kodik",
                "player": player_name,
                "team": team_name,
                "translation": trans_type,
                "url": iframe_url,
                "sub_url": sub_url
            })

    return parsed