import json
import sys
import os
from playwright.sync_api import sync_playwright

os.system('cls' if os.name == 'nt' else 'clear')

def get_direct_link(url):
    try:
        print(f"--- Сканируем: {url} ---")
        found_links = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            page.on("request", lambda r: found_links.append(r.url) if ".m3u8" in r.url and not any(x in r.url for x in ["google", "yandex"]) and r.url not in found_links else None)

            page.goto(url, timeout=45000, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            try:
                player = page.locator("div[id*='player'], .player-container, #video-player").first
                player.click(timeout=5000) if player.is_visible() else page.mouse.click(450, 320)
            except:
                try: page.mouse.click(640, 360)
                except: pass

            page.wait_for_timeout(10000)
            if not found_links: page.screenshot(path="error_screen.png", full_page=True)
            browser.close()

        if found_links:
            return found_links[0].replace("\\", "").strip("'\"")

    except Exception as e:
        print(f"Ошибка парсинга: {e}")
    return None

def main():
    if not os.path.exists('channels.json'):
        print("Ошибка: channels.json не найден")
        sys.exit(1)

    with open('channels.json', 'r', encoding='utf-8') as f:
        channels = json.load(f)

    # Вставка EPG в заголовок плейлиста
    playlist_content = '#EXTM3U x-tvg-url="https://iptvx.one/EPG7"\n'

    if channels:
        ch = channels[0]
        print(f"\n<<< Обработка: {ch.get('name', 'Без названия')} >>>")
        live_link = get_direct_link(ch
