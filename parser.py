import json
import time
from playwright.sync_api import sync_playwright

# Ссылка на твою телепрограмму (вставь сюда свою ссылку)
EPG_URL = "https://твоя-ссылка-на-epg.xml.gz"

def get_m3u8_with_click(url):
    m3u8_link = None
    
    with sync_playwright() as p:
        # Запускаем скрытый браузер
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Перехватываем все запросы, которые делает сайт
        def handle_request(request):
            nonlocal m3u8_link
            if ".m3u8" in request.url:
                m3u8_link = request.url

        page.on("request", handle_request)
        
        try:
            print(f"Открываем страницу: {url}")
            page.goto(url, wait_until="networkidle", timeout=20000)
            
            # Ищем кнопку Плей. Скрипт попытается найти её по тексту или иконке.
            # Если кнопка не нажмется, мы скорректируем этот момент.
            play_buttons = [
                "button:has-text('Play')", "button:has-text('Смотреть')", 
                "div[class*='play']", "button[class*='play']", ".play-btn", "video"
            ]
            
            clicked = False
            for selector in play_buttons:
                if page.locator(selector).first.is_visible():
                    page.locator(selector).first.click()
                    print(f"Нажали на кнопку Плей через селектор: {selector}")
                    clicked = True
                    break
            
            if not clicked:
                # Если явную кнопку не нашли, просто кликаем в центр экрана (по плееру)
                page.mouse.click(400, 300)
                print("Кликнули по центру экрана")

            # Ждем 8 секунд, пока видео загрузится и ссылка промелькнет в сети
            time.sleep(8)
            
        except Exception as e:
            print(f"Ошибка при обработке страницы: {e}")
        finally:
            browser.close()
            
    return m3u8_link

def main():
    with open('channels.json', 'r', encoding='utf-8') as f:
        channels = json.load(f)
        
    playlist = f'#EXTM3U x-tvg-url="{EPG_URL}"\n\n'
    
    for ch in channels:
        print(f"\n--- Обработка канала: {ch['name']} ---")
        live_link = get_m3u8_with_click(ch['source_url'])
        
        if live_link:
            print(f"Успешно поймали ссылку: {live_link[:60]}...")
            playlist += f'#EXTINF:-1 tvg-id="{ch["tvg_id"]}" tvg-logo="{ch["logo"]}",{ch["name"]}\n'
            playlist += f'{live_link}\n\n'
        else:
            print(f"Хьюстон, проблема! Не удалось поймать .m3u8 для {ch['name']}")
            
    with open('playlist.m3u', 'w', encoding='utf-8') as f:
        f.write(playlist)

if __name__ == "__main__":
    main()


