#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LeakHunter v37.1 — Финальная версия с автодополнением в режиме Аниме/персонаж
"""

import time
from typing import List, Dict, Set
from urllib.parse import urlparse, quote
import sys
import os

# Добавляем текущую директорию в путь — это решает проблему Pylance и импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich import box
from rich.prompt import Prompt, IntPrompt, Confirm
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import CompleteStyle






console = Console()
ua = UserAgent()

# Импорт словаря
try:
    from characters_dict import CHARACTERS_MAP as NUDE_MOON_RULE34_GELBOORU_MAP
except ImportError as e:
    console.print("[bold red]Ошибка: Не найден файл characters_dict.py![/]")
    console.print("[yellow]Убедитесь, что файл characters_dict.py лежит в той же папке, что и leakhunter.py[/]")
    console.print("[yellow]И в нём есть переменная CHARACTERS_MAP с словарем персонажей.[/]")
    raise SystemExit from e

HIGH_PRIORITY_DOMAINS = {
    "mega.nz", "gofile.io", "pixeldrain.com", "anonfiles.com",
    "dropbox.com", "drive.google.com", "googleusercontent.com",
    "coomer.su", "coomer.party", "kemono.su", "kemono.party",
    "bunkr.su", "bunkr.is", "cyberdrop.me", "fapello.com",
    "thothub.tv", "simpcity.su", "erothots.co", "nudostar.com",
    "masterfap.net", "leakgallery.com", "dirtyship.com",
    "influencersgonewild.com", "tiava.com",
    "pornhub.com",
    "rule34.xxx", "rule34.paheal.net", "rule34.world", "rule34video.com",
    "nsfwr34.com", "r34.app",
    "gelbooru.com", "danbooru.donmai.us", "safebooru.org",
    "yande.re", "konachan.com",
    "nhentai.net", "allhen.online", "nude-moon.org", "hentai-moon.com",
    "hentai-chan.me",
    "x.com", "twitter.com", "t.co", "t.me",
    "archivebate.com", "bestcam.tv", "camwhores.tv", "camwhoresbay.com",
    "newgrounds.com", "hentai-foundry.com", "deviantart.com", "pixiv.net", "furaffinity.net", "e621.net", "reddit.com", "f95zone.to", "itch.io", "gumroad.com", "patreon.com", "tumblr.com"
}

def is_link_suspicious(url: str) -> bool:
    parsed = urlparse(url.lower())
    blocked = ["adfly", "linkvertise", "ouo.io", "shrinkme.io", "popads.net"]
    for b in blocked:
        if b in parsed.netloc:
            return True
    return False

def get_link_type(url: str) -> str:
    url_lower = url.lower()
    if any(d in url_lower for d in ["mega.nz", "gofile.io", "pixeldrain", "anonfiles", "dropbox", "drive.google"]):
        return "[green]Архив[/]"
    elif any(d in url_lower for d in ["cyberdrop.me", "bunkr.su", "bunkr.is"]):
        return "[magenta]Галерея[/]"
    elif any(d in url_lower for d in ["coomer.su", "coomer.party"]):
        return "[blue]Пак OnlyFans[/]"
    elif any(d in url_lower for d in ["fapello.com", "thothub.tv", "erothots.co", "masterfap.net", "tiava.com", "pornhub.com"]):
        return "[magenta]Видео/Фото[/]"
    elif any(d in url_lower for d in ["archivebate.com", "bestcam.tv", "camwhores.tv", "camwhoresbay.com"]):
        return "[magenta]Webcam архив (бесплатно)[/]"
    elif "rule34video.com" in url_lower or "nsfwr34.com" in url_lower or "r34.app" in url_lower:
        return "[bright_magenta]Rule34 Видео[/]"
    elif "rule34" in url_lower or "gelbooru" in url_lower or "danbooru" in url_lower or "safebooru" in url_lower or "yande.re" in url_lower or "konachan" in url_lower:
        return "[magenta]Rule34 Арт[/]"
    elif "allhen.online" in url_lower:
        return "[bright_magenta]AllHentai — персонаж[/]"
    elif any(d in url_lower for d in ["nhentai", "nude-moon.org", "hentai-moon", "hentai-chan"]):
        return "[bright_magenta]Hentai / Додзинси[/]"
    elif "x.com" in url_lower or "twitter.com" in url_lower:
        if "/search" in url_lower:
            return "[cyan]Все посты на X[/]"
        elif "/media" in url_lower:
            return "[cyan]Медиа на X[/]"
        else:
            return "[bold cyan]Профиль на X[/]"
    elif "t.me" in url_lower:
        if "?search=" in url:
            return "[bright_magenta]Поиск в TG-канале[/]"
        else:
            return "[bright_magenta]Telegram канал[/]"
    elif any(d in url_lower for d in ["newgrounds.com", "hentai-foundry.com", "deviantart.com", "pixiv.net", "furaffinity.net", "e621.net", "reddit.com", "f95zone.to", "itch.io", "gumroad.com", "patreon.com", "tumblr.com","kemono"]):
        return "[magenta]NSFW Artist Контент[/]"
    else:
        return "[yellow]Страница[/]"

def get_priority_color(domain: str) -> str:
    domain = domain.lower()
    if any(d in domain for d in HIGH_PRIORITY_DOMAINS):
        if "x.com" in domain:
            return "cyan"
        if "t.me" in domain:
            return "bright_magenta"
        if "rule34" in domain or "gelbooru" in domain or "danbooru" in domain:
            return "magenta"
        if "nhentai" in domain or "allhen.online" in domain or "nude-moon.org" in domain:
            return "bright_magenta"
        return "green"
    return "yellow"

def generate_variants(name: str) -> dict:
    lower = name.lower()
    with_space = quote(lower)
    underscore = lower.replace(" ", "_")

    return {
        "space": with_space,
        "underscore": underscore,
        "original_lower": lower
    }

def find_x_username(nick: str) -> str | None:
    v = generate_variants(nick)
    search_queries = [f"{v['original_lower']} site:x.com"]
    for q in search_queries:
        urls = duckduckgo_search(q, num_results=12)
        for url in urls:
            if "x.com/" in url and "/status/" not in url and "/search" not in url:
                path = urlparse(url).path.strip("/")
                if path and len(path.split("/")[0]) < 30:
                    return path.split("/")[0].lstrip("@").lower()
    return None

def duckduckgo_search(query: str, num_results: int = 6) -> List[str]:
    urls = []
    headers = {"User-Agent": ua.random}
    search_url = f"https://lite.duckduckgo.com/lite/?q={quote(query)}&num={num_results}"
    try:
        resp = requests.get(search_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.startswith("http") and "uddg=" in href:
                    real_url = requests.utils.unquote(href.split("uddg=")[1].split("&")[0])
                    urls.append(real_url)
    except:
        pass
    return urls[:num_results]

def collect_real_model_links(nick: str) -> List[Dict]:
    all_links: Set[str] = set()
    results: List[Dict] = []

    v = generate_variants(nick)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
        task = progress.add_task("[cyan]Генерация ссылок для реальной модели...", total=70)

        x_username = find_x_username(nick)
        if x_username:
            profile_url = f"https://x.com/{x_username}"
            results.append({"url": profile_url, "title": f"Профиль @{x_username} на X", "domain": "x.com", "type": "[bold cyan]Профиль на X[/]", "priority_color": "cyan"})
            all_links.add(profile_url)
            results.append({"url": f"https://x.com/{x_username}/media", "title": f"Медиа от @{x_username}", "domain": "x.com", "type": "[cyan]Медиа на X[/]", "priority_color": "cyan"})
            all_links.add(f"https://x.com/{x_username}/media")
        results.append({"url": f"https://x.com/search?q={v['space']}", "title": f"Поиск '{nick}' на X", "domain": "x.com", "type": "[cyan]Все посты на X[/]", "priority_color": "cyan"})
        progress.advance(task, 10)

        sites = [
            f"https://fapello.com/search/{v['underscore'].replace('_', '-')}/",
            f"https://coomer.su/onlyfans/user/{v['underscore'].replace('_', '-')}",
            f"https://coomer.st/artists?q={v['underscore']}&service=&sort_by"
            f"https://coomer.party/onlyfans/user/{v['underscore'].replace('_', '-')}",
            f"https://kemono.su/onlyfans/user/{v['underscore'].replace('_', '-')}",
            f"https://simpcity.su/search?search={v['space']}",
            f"https://thothub.tv/search/{v['underscore'].replace('_', '-')}/",
            f"https://nudostar.com/?s={v['space']}",
            f"https://erothots.co/?s={v['space']}",
            f"https://www.tiava.com/search/a/{v['space']}",
            f"https://www.pornhub.com/video/search?search={v['space']}",
            f"https://www.pornhub.com/video/search?search={v['space']}+onlyfans",
            # Бесплатные webcam архивы
            f"https://archivebate.com/profile/{v['underscore']}",
            f"https://bestcam.tv/model/{v['underscore']}",
            f"https://www.camwhores.tv/search/{v['underscore']}/",
            f"https://www.camwhoresbay.com/search/{v['underscore']}/",
        ]
        for url in sites:
            if url not in all_links and not is_link_suspicious(url):
                domain = urlparse(url).netloc.lower().replace("www.", "")
                title = f"Поиск '{nick}' на {domain}"
                if "pornhub.com" in domain:
                    if "+onlyfans" in url:
                        title = f"Видео '{nick}' + OnlyFans на PornHub"
                    else:
                        title = f"Все видео '{nick}' на PornHub 🔥"
                elif "tiava.com" in domain:
                    title = f"Бесплатные видео '{nick}' на Tiava"
                elif "archivebate.com" in domain:
                    title = f"Архив webcam '{nick}' на ArchiveBate 🔥 (бесплатно)"
                elif "bestcam.tv" in domain:
                    title = f"Архив webcam '{nick}' на BestCam 🔥 (бесплатно)"
                elif "camwhores.tv" in domain:
                    title = f"Архив webcam '{nick}' на CamWhores.tv 🔥 (бесплатно)"
                elif "camwhoresbay.com" in domain:
                    title = f"Архив webcam '{nick}' на CamWhoresBay 🔥 (бесплатно)"
                results.append({"url": url, "title": title, "domain": domain, "type": get_link_type(url), "priority_color": get_priority_color(domain)})
                all_links.add(url)
            progress.advance(task, 3)

        tg_channels = [
            "home_pornom", "onlyfans_public", "leaksdropz", "onlyfansleakvip",
            "fullboxx", "dontpay4of", "bestonlyfansleakgroup"
        ]
        for username in tg_channels:
            search_url = f"https://t.me/{username}?search={v['space']}"
            channel_url = f"https://t.me/{username}"
            results.append({"url": search_url, "title": f"Поиск '{nick}' в @{username}", "domain": "t.me", "type": "[bright_magenta]Поиск в TG[/]", "priority_color": "bright_magenta"})
            results.append({"url": channel_url, "title": f"Канал @{username}", "domain": "t.me", "type": "[bright_magenta]Telegram канал[/]", "priority_color": "bright_magenta"})
            progress.advance(task, 4)

    return results

def collect_artist_links(artist: str) -> List[Dict]:
    all_links: Set[str] = set()
    results: List[Dict] = []

    v = generate_variants(artist)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
        task = progress.add_task("[cyan]Генерация ссылок для NSFW artist...", total=70)

        sites = [
            f"https://{v['underscore']}.newgrounds.com/",
            f"https://rule34video.com/models/{v['underscore']}/",
            f"https://www.hentai-foundry.com/user/{v['underscore']}/profile",
            f"https://www.pixiv.net/tags/{v['underscore']}/artworks?s_mode=s_tag",
            f"https://www.furaffinity.net/user/{v['underscore']}/",
            f"https://e621.net/posts?tags={v['underscore']}",
            f"https://www.reddit.com/search?q={v['space']}&type=user",
            f"https://kemono.cr/artists?q={v['space']}&service=&sort_by=favorited&order=",
            f"https://f95zone.to/search/?q={v['space']}",
            f"https://{v['underscore']}.itch.io/",
            f"https://www.patreon.com/{v['underscore']}",
            f"https://x.com/{v['underscore']}",
        ]

        for url in sites:
            if url not in all_links and not is_link_suspicious(url):
                domain = urlparse(url).netloc.lower().replace("www.", "")
                title = f"Профиль/поиск '{artist}' на {domain} 🔥 (бесплатно)"
                results.append({"url": url, "title": title, "domain": domain, "type": get_link_type(url), "priority_color": get_priority_color(domain)})
                all_links.add(url)
            progress.advance(task, 3)

    return results

def collect_anime_character_links(character: str) -> List[Dict]:
    all_links: Set[str] = set()
    results: List[Dict] = []

    v = generate_variants(character)

    char_lower = v['original_lower']

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
        task = progress.add_task("[cyan]Генерация ссылок для аниме-персонажа...", total=70)

        rule34_art = [
            (f"https://rule34.xxx/index.php?page=post&s=list&tags={v['underscore']}", "Rule34.xxx"),
            (f"https://rule34.paheal.net/post/list/{v['underscore']}/1", "Rule34 Paheal"),
        ]

        # Rule34.world — две версии (с источником + без)
        if char_lower in NUDE_MOON_RULE34_GELBOORU_MAP:
            _, rule34_source, _, correct_tag = NUDE_MOON_RULE34_GELBOORU_MAP[char_lower]
            # С источником
            rule34_with_source = f"{correct_tag}_%2528{rule34_source}%2529"
            rule34_art.insert(0, (f"https://rule34.world/{rule34_with_source}", f"Rule34.world — с источником 🔥"))
            # Без источника
            rule34_art.insert(1, (f"https://rule34.world/{correct_tag}", f"Rule34.world — без источника"))

        # Gelbooru — две версии
        if char_lower in NUDE_MOON_RULE34_GELBOORU_MAP:
            _, _, gelbooru_source, correct_tag = NUDE_MOON_RULE34_GELBOORU_MAP[char_lower]
            gelbooru_direct = f"https://gelbooru.com/index.php?page=post&s=list&tags={correct_tag}_({gelbooru_source})+"
            rule34_art.append((gelbooru_direct, f"Gelbooru — правильный порядок 🔥"))
            reverse_tag = "_".join(reversed(correct_tag.split("_")))
            gelbooru_reverse = f"https://gelbooru.com/index.php?page=post&s=list&tags={reverse_tag}_({gelbooru_source})+"
            rule34_art.append((gelbooru_reverse, f"Gelbooru — обратный порядок"))

        rule34_art.append((f"https://gelbooru.com/index.php?page=post&s=list&tags={v['underscore']}", "Gelbooru — поиск по тегу"))

        # Danbooru, Safebooru, Yande.re, Konachan — две версии
        booru_sites = [
            ("https://danbooru.donmai.us/posts?tags=", "Danbooru"),
            ("https://safebooru.org/index.php?page=post&s=list&tags=", "Safebooru"),
            ("https://yande.re/post?tags=", "Yande.re"),
            ("https://konachan.com/post?tags=", "Konachan"),
        ]

        if char_lower in NUDE_MOON_RULE34_GELBOORU_MAP:
            _, _, _, correct_tag = NUDE_MOON_RULE34_GELBOORU_MAP[char_lower]
            source_tag = f"({NUDE_MOON_RULE34_GELBOORU_MAP[char_lower][2]})"
            # Правильная
            for base, name in booru_sites:
                rule34_art.append((f"{base}{correct_tag}_{source_tag}", f"{name} — правильный порядок"))
            # Обратная
            reverse_tag = "_".join(reversed(correct_tag.split("_")))
            for base, name in booru_sites:
                rule34_art.append((f"{base}{reverse_tag}_{source_tag}", f"{name} — обратный порядок"))

        # Резервные обычные поиски
        for base, name in booru_sites:
            rule34_art.append((f"{base}{v['underscore']}", f"{name} — поиск по тегу"))

        # Rule34 видео
        rule34_video = [
            (f"https://rule34video.com/search/{v['space']}/", "Rule34Video.com"),
            (f"https://rule34video.com/tags/{v['underscore']}/", "Rule34Video.com по тегу"),
            (f"https://nsfwr34.com/search/{v['space']}/", "NSFW R34 — 3D видео"),
            (f"https://r34.app/search/{v['space']}/", "R34.app — видео/GIF"),
        ]

        # Hentai
        hentai_sites = [
            (f"https://nhentai.net/search/?q={v['underscore']}", "nHentai"),
            (f"https://20.allhen.online/list/person/{v['underscore']}", "AllHentai.ru — страница персонажа"),
            (f"https://nude-moon.org/?s={v['space']}", "Nude-Moon.org — общий поиск"),
            (f"https://hentai-moon.com/?s={v['space']}", "Hentai-Moon"),
            (f"https://hentai-chan.me/search/?q={v['underscore']}", "Hentai-Chan"),
        ]

        # Прямая серия в Nude-Moon
        if char_lower in NUDE_MOON_RULE34_GELBOORU_MAP:
            nude_moon_slug = NUDE_MOON_RULE34_GELBOORU_MAP[char_lower][0]
            nude_moon_url = f"https://nude-moon.org/seria/{nude_moon_slug}"
            hentai_sites.insert(2, (nude_moon_url, f"Nude-Moon.org — прямая страница серии 🔥"))

        all_sites = rule34_art + rule34_video + hentai_sites
        for url, title in all_sites:
            if url not in all_links and not is_link_suspicious(url):
                domain = urlparse(url).netloc.lower().replace("www.", "")
                results.append({"url": url, "title": title + f" — {character}", "domain": domain, "type": get_link_type(url), "priority_color": get_priority_color(domain)})
                all_links.add(url)
            progress.advance(task)

    return results


def collect_tag_search_links(tags_input: str) -> List[Dict]:
    all_links: Set[str] = set()
    results: List[Dict] = []

    # Обработка ввода: поддержка пробелов и запятых
    tags_raw = [t.strip().lower() for t in tags_input.replace(",", " ").split() if t.strip()]
    final_tags = []

    for tag in tags_raw:
        if tag in NUDE_MOON_RULE34_GELBOORU_MAP:
            char_data = NUDE_MOON_RULE34_GELBOORU_MAP[tag]

            base_name = char_data[3]
            boor_source = char_data[1]
            final_tags.append(f'{base_name}_({boor_source})')
        else:
            final_tags.append(tag)

    encoded_tags = "+".join(quote(t.replace(" ", "_")) for t in final_tags)





    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
        task = progress.add_task("[cyan]Генерация ссылок по тегам...", total=8)

        sites = [
            (f"https://rule34.xxx/index.php?page=post&s=list&tags={encoded_tags}", "Rule34.xxx"),
            (f"https://rule34.world/{encoded_tags}", "Rule34.world"),
            (f"https://gelbooru.com/index.php?page=post&s=list&tags={encoded_tags}", "Gelbooru"),
            (f"https://danbooru.donmai.us/posts?tags={encoded_tags}", "Danbooru"),
            (f"https://safebooru.org/index.php?page=post&s=list&tags={encoded_tags}", "Safebooru"),
            (f"https://yande.re/post?tags={encoded_tags}", "Yande.re"),
            (f"https://konachan.com/post?tags={encoded_tags}", "Konachan"),
            (f"https://rule34.paheal.net/post/list/{encoded_tags}/1", "Rule34 Paheal"),
        ]

        for url, site_name in sites:
            if url not in all_links and not is_link_suspicious(url):
                domain = urlparse(url).netloc.lower().replace("www.", "")
                title = f"{site_name} — поиск по тегам: {' '.join(tags_raw)} 🔥"
                results.append({
                    "url": url,
                    "title": title,
                    "domain": domain,
                    "type": "[magenta]Rule34 Арт[/]",
                    "priority_color": "magenta"
                })
                all_links.add(url)
            progress.advance(task, 1)

    return results



def show_top_10_anime():
    top_10 = [
        ("2B", "Nier: Automata", "2b_(nier:automata)"),
        ("Asuka Langley", "Neon Genesis Evangelion", "asuka_langley"),
        ("Tifa Lockhart", "Final Fantasy VII", "tifa_lockhart"),
        ("Zero Two", "Darling in the Franxx", "zero_two"),
        ("Makima", "Chainsaw Man", "makima_(chainsaw_man)"),
        ("Power", "Chainsaw Man", "power_(chainsaw_man)"),
        ("Himiko Toga", "My Hero Academia", "toga_himiko"),
        ("Marin Kitagawa", "My Dress-Up Darling", "kitagawa_marin"),
        ("Yor Forger", "Spy x Family", "yor_forger"),
        ("Loona", "Helluva Boss", "loona_(helluva_boss)"),
    ]

    table = Table(title="[bold magenta]Топ-10 популярных аниме-персонажей 2025[/]", box=box.ROUNDED)
    table.add_column("№", style="cyan", width=4)
    table.add_column("Персонаж", style="bright_white")
    table.add_column("Аниме/Игра", style="yellow")
    table.add_column("Тег для поиска", style="green")

    for i, (char, source, tag) in enumerate(top_10, 1):
        table.add_row(str(i), char, source, tag)

    console.print(table)
    console.print(Panel(
        "[bold red]ВАЖНО:[/] Если ничего не найдено — попробуйте точное имя как в таблице выше.\n"
        "Теги используют подчёркивание (_). Некоторые персонажи имеют уточнения в скобках.",
        title="Дисклеймер",
        border_style="red"
    ))

def display_results(name: str, results: List[Dict], mode: str):
    if not results:
        console.print(Panel(f"[bold red]Ничего не найдено для {name} 😕[/]\nПопробуйте вариации имени или посмотрите топ выше.", title="Результат", border_style="red"))
        return

    mode_name = "Реальная модель" if mode == "real" else "Аниме/персонаж" if mode == "anime" else "NSFW Artist"
    table = Table(title=f"[bold magenta]{name}[/] — {mode_name} ({len(results)} ссылок)", box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("№", style="dim", width=4)
    table.add_column("Источник", width=30)
    table.add_column("Тип", width=30)
    table.add_column("Ссылка", width=80)
    table.add_column("Приоритет", justify="center")

    for i, res in enumerate(results, 1):
        table.add_row(
            str(i),
            res["domain"],
            res["type"],
            f"[link={res['url']}]{res['title'][:75]}{'...' if len(res['title']) > 75 else ''}[/link]",
            f"[{res['priority_color']}]●[/]"
        )

    console.print(table)
    console.print(Panel(f"[bold]Всего ссылок:[/] {len(results)} 🔥", title="Итог", border_style="bright_blue"))

def save_to_file(results: List[Dict], name: str, mode: str):
    save_dir = 'savelist'
    os.makedirs(save_dir, exist_ok=True)
    filename = f"{mode}_{name.replace(' ', '_')}_{time.strftime('%Y%m%d_%H%M')}.txt"
    file_path = os.path.join(save_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"Результаты для '{name}' — {'Реальная модель' if mode == 'real' else 'Аниме/персонаж' if mode == 'anime' else 'NSFW Artist'} — {time.strftime('%Y-%m-%d %H:%M')}\n\n")
        for res in results:
            f.write(f"{res['type']} | {res['domain']} | {res['url']}\n")
    console.print(f"[green]Сохранено в [bold]{file_path}[/] 🎉[/]")

def main():
    console.print(
        Panel(
            "[bold magenta]🔥 LeakHunter v37.2 — Финал 2025 🔥[/]\n\n"
            "[bold cyan]Автодополнение в режиме «Аниме/персонаж»[/]\n"
            "[cyan]• Вводите первые буквы имени[/]\n"
            "[cyan]• Появится список в рамке[/]\n"
            "[cyan]• Стрелки ↑↓ — выбор | Enter — подтвердить[/]\n\n"
            "[magenta]3 режима поиска • Кликабельные ссылки • Всё бесплатно[/]",
            title="💦 Максимум NSFW-контента",
            border_style="magenta",
            padding=(1, 4),
        )
    )

    # Выбор режима
    console.print("[bold yellow]Выберите режим:[/]")
    console.print("1. Реальная модель")
    console.print("2. Аниме/персонаж")
    console.print("3. NSFW Artist контент")
    console.print("4. Поиск по тегам (Rule34, Gelbooru и др.)")
    mode_choice = Prompt.ask("[bold yellow]Введите номер (1-4)[/]", choices=["1", "2", "3", "4"], default="1")
    mode = "real" if mode_choice == "1" else "anime" if mode_choice == "2" else "artist" if mode_choice == "3" else "tags"

    if mode == "anime":
        show_top_10_anime()

    hint = {
        "real": "ник или имя модели",
        "anime": "имя персонажа",
        "artist": "ник NSFW artist",
        "tags": "теги через пробел или запятую (например: 2b solo female)"
    }[mode]

    # Стиль для красивого меню подсказок
    style = Style.from_dict({
        'completion-menu.completion': 'bg:#008888 #ffffff',
        'completion-menu.completion.current': 'bg:#00aaaa #000000',
        'completion-menu.meta': 'bg:#444444 #ffffff',
        'scrollbar.background': 'bg:#88aaaa',
        'scrollbar.button': 'bg:#222222',
    })

    # Базовая сессия ввода
    session = PromptSession(
        f"{hint} (или 'exit' для выхода): [/]",
        style=style,
        reserve_space_for_menu=10
    )

    # Если anime-режим — добавляем автодополнение с вертикальным списком в рамке
    if mode == "anime":
        anime_names = list(NUDE_MOON_RULE34_GELBOORU_MAP.keys())
        completer = WordCompleter(anime_names, ignore_case=True, sentence=True)
        session = PromptSession(
            f"{hint} (или 'exit' для выхода): [/]",
            completer=completer,
            complete_while_typing=True,
            complete_style=CompleteStyle.COLUMN,  # Вертикальный список в рамке
            reserve_space_for_menu=15,  # Место для большего списка
            style=style
        )
        console.print("[green]Автодополнение активно: вводите буквы — список появится в рамке ниже[/]")

    while True:
        names = []
        try:
            name_input = session.prompt()
        except KeyboardInterrupt:
            console.print("\n[red]Прервано пользователем.[/]")
            break

        if name_input.lower().strip() in {"exit", "выход", "q", "quit"}:
            console.print(Panel("[bold green]Спасибо за использование LeakHunter! До новых встреч 🔥[/]", 
                               title="Выход", border_style="bright_green"))
            break
        if not name_input.strip():
            console.print("[red]Ничего не введено. Попробуйте снова.[/]")
            continue
        
        
        


        if mode == "tags":
            console.print("\n" + "=" * console.width)
            with console.status(f"[bold magenta]Обрабатываем теги: {name_input}...[/]", spinner="dots12"):
                results = collect_tag_search_links(name_input)
            
            display_results(name_input, results, mode)
            
            if results and Confirm.ask("[green]Сохранить результаты?[/]"):
                save_to_file(results, name_input, mode)
        else:
            names = [n.strip() for n in name_input.split(",") if n.strip()]

        
        for name in names:
            console.print("\n" + "═" * console.width)
            with console.status(f"[bold magenta]Обрабатываем: {name}...[/]", spinner="dots12"):
                results = {
                    "real": collect_real_model_links,
                    "anime": collect_anime_character_links,
                    "artist": collect_artist_links
                    
                }[mode](name)

            display_results(name, results, mode)

            if results and Confirm.ask("[green]Сохранить результаты?[/]"):
                save_to_file(results, name, mode)

            time.sleep(1)

        # Меню «Что дальше?»
        while True:
            choice = Prompt.ask(
                "[bold cyan]Что дальше?[/]\n"
                "1 — Ввести ещё имя в этом режиме\n"
                "2 — Сменить режим\n"
                "3 — Выйти",
                choices=["1", "2", "3"],
                default="1"
            )

            if choice == "1":
                break
            elif choice == "3":
                console.print(Panel("[bold green]Спасибо за использование LeakHunter! До свидания 🔥[/]", 
                                   title="Выход", border_style="bright_green"))
                return
            else:  # choice == "2"
                console.print("[bold yellow]Выберите новый режим:[/]")
                console.print("1. Реальная модель")
                console.print("2. Аниме/персонаж")
                console.print("3. NSFW Artist контент")
                console.print("4. Поиск по тегам (Rule34, Gelbooru и др.)")
                new_mode_choice = Prompt.ask("[bold yellow]Введите номер (1-4)[/]", choices=["1", "2", "3", "4"])
                mode = "real" if new_mode_choice == "1" else "anime" if new_mode_choice == "2" else "artist" if new_mode_choice == "3" else "tags"

                if mode == "anime":
                    show_top_10_anime()
                    anime_names = list(NUDE_MOON_RULE34_GELBOORU_MAP.keys())
                    completer = WordCompleter(anime_names, ignore_case=True, sentence=True)
                    session = PromptSession(
                        f"{hint} (или 'exit' для выхода): [/]",
                        completer=completer,
                        complete_while_typing=True,
                        complete_style=CompleteStyle.COLUMN,
                        reserve_space_for_menu=15,
                        style=style
                    )
                    console.print("[green]Автодополнение активно для нового режима[/]")
                else:
                    session = PromptSession(
                        f"{hint} (или 'exit' для выхода): [/]",
                        reserve_space_for_menu=10,
                        style=style
                    )

                console.print(f"[bold green]Режим сменён на: {mode}[/]")
                break

    console.print(Panel("[bold green]Поиск завершён. Спасибо за использование LeakHunter v37.2 🔥[/]", 
                       title="Готово", border_style="bright_green"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]Прервано пользователем.[/]")
    except Exception as e:
        console.print(f"[bold red]Ошибка: {e}[/]")