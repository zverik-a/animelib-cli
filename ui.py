import questionary
from rich.console import Console
from rich.table import Table
from parsers import extract_summary_text

console = Console()

def select_anime(results: list) -> dict | None:
    if not results:
        console.print("[yellow]Ничего не найдено.[/yellow]")
        return None

    choices = []
    for idx, item in enumerate(results, 1):
        rus_name = item.get("rus_name") or item.get("name", "N/A")
        release_date = item.get("releaseDate", "N/A")[:4] if item.get("releaseDate") else "N/A"
        anime_type = item.get("type", {}).get("label", "N/A")
        
        choices.append({
            "name": f"{idx}. {rus_name} ({release_date}) [{anime_type}]",
            "value": item
        })

    return questionary.select("Выберите тайтл:", choices=choices).ask()

def display_details_table(details: dict):
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

    teams = details.get("teams", [])
    teams_list = ", ".join([t.get("name") for t in teams if t.get("name")]) or "Не указаны"

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

    table.add_row("Команды озвучки/перевода", teams_list)

    console.print(table)    

def post_details_menu() -> str:
    """Отображает кнопки управления после просмотра информации."""
    action = questionary.select(
        "Выберите действие:",
        choices=[
            {"name": "1. Далее", "value": "next"},
            {"name": "2. Назад", "value": "back"}
        ]
    ).ask()
    return action


# ui.py
def select_episode(episodes: list) -> dict | None:
    """Отображает список эпизодов и предоставляет выбор."""
    if not episodes:
        console.print("[yellow]Список эпизодов пуст.[/yellow]")
        return None

    table = Table(title="Список эпизодов", show_lines=True)
    table.add_column("№", style="cyan", justify="right")
    table.add_column("ID", style="dim")
    table.add_column("Номер", style="bold green")
    table.add_column("Название", style="bold white")
    table.add_column("Статус", style="yellow")

    choices = []
    for idx, ep in enumerate(episodes, 1):
        ep_id = str(ep.get("id", "N/A"))
        number = str(ep.get("number", "N/A"))
        name = ep.get("name") or "Без названия"
        status = ep.get("status", {}).get("label", "N/A")

        table.add_row(
            str(idx),
            ep_id,
            f"Серия {number}",
            name,
            status
        )

        choices.append({
            "name": f"Серия {number}: {name}",
            "value": ep
        })

    console.print(table)

    return questionary.select(
        "Выберите эпизод:",
        choices=choices
    ).ask()


# ui.py
def select_player_stream(parsed_players: list) -> tuple[str | None, str | None, str | None]:
    """
    Возвращает кортеж: (stream_url, player_type, sub_url)
    player_type: 'direct' | 'kodik'
    """
    if not parsed_players:
        console.print("[yellow]Доступных плееров не найдено.[/yellow]")
        return None, None, None

    choices = []
    for idx, p in enumerate(parsed_players, 1):
        has_sub_flag = " [SUB]" if p.get("sub_url") else ""
        label = f"{idx}. [{p['player']}] {p['team']} ({p['translation']}){has_sub_flag}"
        choices.append({
            "name": label,
            "value": p
        })

    selected = questionary.select("Выберите источник видео:", choices=choices).ask()
    if not selected:
        return None, None, None

    sub_url = selected.get("sub_url")
    player_type = selected.get("type")

    if player_type == "direct":
        links = selected["links"]
        q_choices = [{"name": q, "value": url} for q, url in links.items()]
        chosen_stream = questionary.select("Выберите качество:", choices=q_choices).ask()
        return chosen_stream, player_type, sub_url
    
    elif player_type == "kodik":
        return selected["url"], player_type, sub_url

    return None, None, None