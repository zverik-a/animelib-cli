import sys
import requests
import questionary
from rich.console import Console
from rich.table import Table

BASE_URL = "https://hapi.hentaicdn.org/api/anime"
BEARER_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiNmQ5NTQzOThmNTBmNGQ5ZTA2NmIzMTU3YTNlZjE3MDgwY2IyOWU3YjEwMTI5MTdkMDlmYmVmMzU1YzE5ZTU1ODgyZWI5ODcxOTBhZjM1NTkiLCJpYXQiOjE3ODg0NDQ2MjcuMzcyODMxLCJuYmYiOjE3ODg0NDQ2MjcuMzcyODMzLCJleHAiOjE3OTEwMzY2MjcuMzcwNDY0LCJzdWIiOiI5NTIxODgwIiwic2NvcGVzIjpbXX0.F5W1qqECoZRCCgnDibTT8m4wm4x4sr9gBHC38kiUkaIVmlckUGeM19ll7_6SRd7SMF7x-FEhVw4pQKD-KMj9utUNxeEiHylK6NxrZcjEPfSx_VVkcztboLgUM1GancVfQ0x3N0K3OMdAb5fDgmX7bT7K38EzNd_2uJEi4Em4pm4ab9mZEHWJwa1ULtx3HM1I-IplHj8ajd5G8GV1Y_sjkw_af1j9_QJlNLW9CXUnQAj1AE8Vdj6sH9sCDDLxG5x2CQBR4SOP5rKtpce05akNVdk4aTg3vH1NMyz7QlD1479PoyLgajhGrVrvU0QsPhQXTeLqgk-lqH8cZI9ZMCZTgsG7O7dmDL0lSNYQoYVii6YmXj8Su2g5QoXdzdwk7RBmL2-mrWneHmCWfFDqTnXEUmyClrm6wgdGJJR0dU8XiTjqPlnKzdtA0ly9XDDwAOOOkRmxKUt6fPrqueJYM-0OEEg-W2h5nmNdEz8olsPK_j3aR5G1toH3fmI83LyD2aOZHcS6URxdBBMpMh0KbIBcmDG5gOG8cVeUIkLAB3iidO9f-fP1u5HUVz79im8vwPnXv1tw5g3YcelTCkSe0WHC-jBCu-iUhbFM-CU3LIy6TCvcHNeapV1F449L7Dp2LpAO59pudI4tQ1K7Qburux2aCD2JKrU1Mmfcs244-ptZ62g"

console = Console()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Referer": "https://hentaicdn.org/",
    "Origin": "https://hentaicdn.org"
}

if BEARER_TOKEN:
    HEADERS["Authorization"] = f"Bearer {BEARER_TOKEN}"

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

def search_anime(query: str) -> list:
    """Первичный поиск списка аниме."""
    params = {
        "q": query,
        "fields[0]": "rate_avg",
        "fields[1]": "rate",
        "fields[2]": "releaseDate"
    }

    try:
        response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except requests.RequestException as e:
        console.print(f"[bold red]Ошибка поиска:[bold red] {e}")
        return []

def get_anime_details(slug_url: str) -> dict:
    """Запрос полных данных тайтла со всеми нужными полями."""
    url = f"{BASE_URL}/{slug_url}"
    params = {
        "fields[0]": "genres",
        "fields[1]": "tags",
        "fields[2]": "releaseDate",
        "fields[3]": "summary",
        "fields[4]": "episodes_count",
        "fields[5]": "episodes",
        "fields[6]": "time"
    }

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {})
    except requests.RequestException as e:
        console.print(f"[bold red]Ошибка получения деталей:[bold red] {e}")
        return {}

def display_details_table(details: dict):
    """Формирует и выводит таблицу с детальной информацией."""
    if not details:
        console.print("[yellow]Нет данных для отображения.[/yellow]")
        return

    table = Table(title=f"Информация: {details.get('rus_name') or details.get('name')}", show_lines=True)
    table.add_column("Поле", style="cyan", justify="right")
    table.add_column("Значение", style="bold white")

    rus_name = details.get("rus_name", "N/A")
    eng_name = details.get("eng_name", "N/A")
    anime_type = details.get("type", {}).get("label", "N/A")
    status = details.get("status", {}).get("label", "N/A")
    age_rating = details.get("ageRestriction", {}).get("label", "N/A")
    
    release_date = details.get("releaseDateString") or details.get("releaseDate", "N/A")
    
    episodes_uploaded = details.get("items_count", {}).get("uploaded", 0)
    episodes_total = details.get("items_count", {}).get("total", 0)
    episodes_info = f"{episodes_uploaded} / {episodes_total}"
    
    duration = details.get("time", {}).get("formated", "N/A")
    shiki_rate = str(details.get("shiki_rate", "N/A"))
    
    genres = ", ".join([g.get("name") for g in details.get("genres", []) if g.get("name")]) or "N/A"
    tags = ", ".join([t.get("name") for t in details.get("tags", []) if t.get("name")]) or "N/A"
    
    summary_text = extract_summary_text(details.get("summary")) or "Отсутствует"

    table.add_row("ID", str(details.get("id", "N/A")))
    table.add_row("Название (RU)", rus_name)
    table.add_row("Название (EN)", eng_name)
    table.add_row("Тип", anime_type)
    table.add_row("Статус", status)
    table.add_row("Возрастной рейтинг", age_rating)
    table.add_row("Дата выхода", release_date)
    table.add_row("Эпизоды", episodes_info)
    table.add_row("Длительность", duration)
    table.add_row("Рейтинг Shikimori", f"★ {shiki_rate}")
    table.add_row("Жанры", genres)
    table.add_row("Теги", tags)
    table.add_row("Описание", summary_text)

    console.print(table)

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else input("Введите название для поиска: ")
    
    console.print(f"[bold blue]Поиск:[bold blue] {query}...")
    results = search_anime(query)
    
    if not results:
        console.print("[yellow]Ничего не найдено.[/yellow]")
        sys.exit(0)

    choices = []
    for idx, item in enumerate(results, 1):
        rus_name = item.get("rus_name") or item.get("name", "N/A")
        release_date = item.get("releaseDate", "N/A")[:4] if item.get("releaseDate") else "N/A"
        anime_type = item.get("type", {}).get("label", "N/A")
        
        choices.append({
            "name": f"{idx}. {rus_name} ({release_date}) [{anime_type}]",
            "value": item
        })

    selected_item = questionary.select(
        "Выберите тайтл:",
        choices=choices
    ).ask()

    if selected_item and selected_item.get("slug_url"):
        slug_url = selected_item["slug_url"]
        console.print(f"\n[bold green]Загрузка деталей для:[bold green] {slug_url}...")
        
        details = get_anime_details(slug_url)
        display_details_table(details)