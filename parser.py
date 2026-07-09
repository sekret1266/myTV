import json
import sys
import re
from playwright.sync_api import sync_playwright

def get_direct_link(url):
    page = None
    browser = None
    try:
        print(f"Сканируем страницу и ловим сетевые запросы: {url}")
        found_links = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            def handle_request(request):
                req_url = request.url
                if (".m3u8" in req_url or ".mpd" in req_url) and "google" not in req_url and "yandex" not in req_url:
                    if req_url not in found_links:
                        found_links.append(req_url)

            page.on("request", handle_request)

            page.goto(url, timeout=45000, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            # Кликер по плееру
            try:
                video_element = page.locator("video").first
                if video_element.is_visible():
                    video_element.click(timeout=5000)
                else:
                    player_container = page.locator("div[id*='player'], div[class*='player'], #video-player, .player").first
                    if player_container.is_visible():
                        player_container.click(timeout=5000)
                    else:
                        page.mouse.click(450, 320)
            except Exception:
                try:
                    page.mouse.click(640, 360)
                except:
                    pass

            page.wait_for_timeout(10000)

            if not found_links:
                page.screenshot(path="error_screen.png", full_page=True)

            browser.close()

        if found_links:
            raw_link = found_links[0]
            # Жесткая очистка ссылки от любых экранирующих бэкслешей (\), которые ломают плееры
            clean_link = raw_link.replace("\\", "")
            # Убираем возможные кавычки по краям, если ссылка выдернулась из JS-переменной
            clean_link = clean_link.strip("'\"")
            return clean_link

    except Exception as e:
        print(f"Ошибка при перехвате трафика: {e}")
        try:
            if page: page.screenshot(path="error_screen.png", full_page=True)
        except: pass
        try:
            if browser: browser.close()
        except: pass
            
    return None

def main():
    with open('channels.json', 'r', encoding='utf-8') as f:
        channels = json.load(f)

    # Заголовок M3U (без лишних пробелов и переносов)
    playlist = "#EXTM3U\n"
    links_found = 0

    for ch in channels:
        print(f"\n--- Сканирование канала: {ch['name']} ---")
        live_link = get_direct_link(ch['source_url'])

        if live_link:
            print(f"УСПЕХ! Ссылка найдена: {live_link}")
            # Формируем строку строго по стандарту M3U без лишних кавычек внутри параметров, если они не нужны
            tvg_id = ch.get('tvg_id', '')
            logo = ch.get('logo', '')
            name = ch.get('name', 'Unknown Channel')
            
            playlist += f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}",{name}\n'
            playlist += f'{live_link}\n'
            links_found += 1
        else:
            print(f"ОШИБКА: Поток для {ch['name']} не обнаружен")

    if links_found > 0:
        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(playlist.strip() + "\n") # .strip() убирает случайные пустые строки в конце
        print("Файл playlist.m3u успешно сохранен и очищен.")
    else:
        print("Ссылки не найдены, файл не перезаписан.")
        sys.exit(1)

if __name__ == "__main__":
    main()
