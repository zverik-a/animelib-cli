# main.py
import sys
import subprocess
from api import search_anime, get_anime_details, get_anime_episodes, get_episode_details
from ui import console, select_anime, display_details_table, post_details_menu, select_episode, select_player_stream
from parsers import parse_players

def main():
    query = sys.argv[1] if len(sys.argv) > 1 else input("Введите название для поиска: ")
    
    console.print(f"[bold blue]Поиск:[bold blue] {query}...")
    results = search_anime(query)
    
    if not results:
        console.print("[yellow]Ничего не найдено.[/yellow]")
        return

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
            episodes = get_anime_episodes(slug_url)
            
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
                    subprocess.run(cmd)
            break

if __name__ == "__main__":
    main()