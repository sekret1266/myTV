import json
import time
import os
from playwright.sync_api import sync_playwright

EPG_URL = "https://iptvx.one/EPG_NOARCH"

def get_m3u8_with_click(url):
    m3u8_link = None
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        
        def handle_request(request):
            nonlocal m3u8_link
            req_url = request.url
            # Ловим вообще любые упоминания m3u8 или потоков
            if ".m3u8" in req_url or "playlist" in req_url or "stream" in req_url:
                if "google" not in req_url and "yandex" not in req_url and "doubleclick" not in req_url:
                    m3u8_link = req_url

        page.on("request", handle_request)
        
        try:
            print(f"Открываем страницу: {url}")
            page.goto(url, wait_until="load", timeout=40000)
            time.sleep(5)
            
            # Делаем первый клик по центру страницы, чтобы активировать окно
            page.mouse.click(640, 360)
            print("Сделали клик по центру экрана")
            time.sleep(3)
            
            # Пробуем кликнуть по кнопке "Плеер 1" если она есть
            if page.locator("text=Плеер 1").is_visible():
                page.locator("text=Плеер 1").click()
                print("Нажали на вкладку Плеер 1")
                time.sleep(2)

            # Перебираем все возможные элементы плеера для клика
            for selector in ["video", "object", "embed", ".play-btn", "[class*='player']"]:
                if page.locator(selector).first.is_visible():
                    page.locator(selector).first.click()
                    print(f"Кликнули по селектору плеера: {selector}")
                    time.sleep(2)

            time.sleep(10)
            
            # Если ссылку так и не нашли — делаем скриншот для истории
            if not m3u8_link:
                print("Ссылка не найдена, сохраняем скриншот страницы...")
                page.screenshot(path="error_screen.png")
                
        except Exception as e:
            print(f"Ошибка в браузере: {e}")
        finally:
            browser.close()
            
    return m3u8_link

def main():
    with open('channels.json', 'r', encoding='utf-8') as f:
        channels = json.load(f)
        
    playlist = f'#EXTM3U x-tvg-url="{EPG_URL}"\n\n'
    links_found = 0
    
    for ch in channels:
        print(f"\n--- Тест канала: {ch['name']} ---")
        live_link = get_m3u8_with_click(ch['source_url'])
        
        if live_link:
            print(f"УСПЕХ! Ссылка: {live_link[:60]}...")
            playlist += f'#EXTINF:-1 tvg-id="{ch["tvg_id"]}" tvg-logo="{ch["logo"]}",{ch["name"]}\n'
            playlist += f'{live_link}\n\n'
            links_found += 1
            
    if links_found > 0:
        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(playlist)
    else:
        # Специально создаем пустой маркер ошибки для логов GitHub
        with open('error_marker.txt', 'w') as f:
            f.write('No links found')

if __name__ == "__main__":
    main()




