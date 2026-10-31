# main.py
import argparse
import subprocess
from api import search_anime, get_anime_details, get_anime_episodes, get_episode_details
from ui import console, select_anime, display_details_table, post_details_menu, select_episode, select_player_stream
from parsers import parse_players

def main() -> int:
    parser = argparse.ArgumentParser(description="Search anime and play selected episodes with mpv.")
    parser.add_argument("query", nargs="?", help="anime title to search for")
    args = parser.parse_args()
    query = (args.query or input("Введите название для поиска: ")).strip()
    if not query:
        console.print("[yellow]Введите название для поиска.[/yellow]")
        return 2
    
    console.print(f"[bold blue]Поиск:[bold blue] {query}...")
    results = search_anime(query)
    
    if not results:
        console.print("[yellow]Ничего не найдено.[/yellow]")
        return 0

    while True:
        selected_item = select_anime(results)
        
        if not selected_item:
            break

        slug_url = selected_item.get("slug_url")
        if not slug_url:
            console.print("[red]У выбранного тайтла отсутствует slug_url.[/red]")
            continue

        console.print(f"\n[bold green]Загрузка деталей для:[bold green] {slug_url}...")
        details = get_anime_details(slug_url)
        display_details_table(details)

        action = post_details_menu()

        if action == "back":
            continue
        elif action == "next":
            console.print(f"\n[bold green]Загрузка эпизодов...[/bold green]")
            anime_id = selected_item.get("id")
            if anime_id is None:
                console.print("[red]У выбранного тайтла отсутствует ID для загрузки эпизодов.[/red]")
                continue
            episodes = get_anime_episodes(anime_id)
            
            selected_ep = select_episode(episodes)
            if selected_ep:
                ep_id = selected_ep.get("id")
                console.print(f"\n[bold green]Загрузка источников для эпизода {ep_id}...[/bold green]")
                
                ep_details = get_episode_details(ep_id)
                raw_players = ep_details.get("players", [])
                
                parsed_players = parse_players(raw_players)
                stream_url, player_type, sub_url = select_player_stream(parsed_players)
                
                if stream_url:
                    console.print(f"\n[bold green]Запуск mpv...[/bold green]")
                    
                    cmd = ["mpv"]

                    # Устанавливаем Referer в зависимости от провайдера
                    if player_type == "kodik":
                        cmd.append("--http-header-fields=Referer: https://kodikplayer.com/")
                        # Дополнительно передаем ytdl-raw-options для yt-dlp
                        cmd.append("--ytdl-raw-options=referer=https://kodikplayer.com/")
                    else:
                        cmd.append("--http-header-fields=Referer: https://animelib.org/")

                    if sub_url:
                        console.print(f"[bold cyan]Подключение субтитров:[bold cyan] {sub_url}")
                        cmd.append(f"--sub-file={sub_url}")

                    cmd.append(stream_url)
                    try:
                        subprocess.run(cmd, check=False)
                    except FileNotFoundError:
                        console.print("[bold red]mpv не найден. Установите mpv и повторите попытку.[/bold red]")
                        return 1
            break
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Отменено.[/yellow]")
        raise SystemExit(130)
