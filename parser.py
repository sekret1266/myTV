import json
import time
from playwright.sync_api import sync_playwright

# Вставь сюда свою ссылку на телепрограмму, если она есть
EPG_URL = "https://iptvx.one/EPG_NOARCH"

def get_m3u8_with_click(url):
    m3u8_link = None
    
    with sync_playwright() as p:
        # Запускаем браузер с эмуляцией реального компьютера
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Перехватчик запросов
        def handle_request(request):
            nonlocal m3u8_link
            req_url = request.url
            if ".m3u8" in req_url or ".mpd" in req_url or "master.txt" in req_url:
                if "google" not in req_url and "yandex" not in req_url and "doubleclick" not in req_url:
                    m3u8_link = req_url

        page.on("request", handle_request)
        
        try:
            print(f"Открываем страницу: {url}")
            page.goto(url, wait_until="networkidle", timeout=40000)
            time.sleep(5) # Ждем первичную загрузку скриптов плеера
            
            # Скроллим к плееру, чтобы он попал в зону видимости (некоторые плееры не запустятся без этого)
            if page.locator("video").is_visible():
                page.locator("video").scroll_into_view_if_needed()
                time.sleep(1)
                
                # Пробуем кликнуть по самому видео
                page.locator("video").click()
                print("Кликнули по тегу video")
            
            # Дополнительно кликаем по координатам, где на smotrettv обычно кнопка
            page.mouse.click(450, 350)
            print("Сделали контрольный клик по центру")
            
            # Ждем 12 секунд, пока поток точно раскочегарится
            time.sleep(12)
            
        except Exception as e:
            print(f"Ошибка при работе с браузером: {e}")
        finally:
            browser.close()
            
    return m3u8_link

def main():
    try:
        with open('channels.json', 'r', encoding='utf-8') as f:
            channels = json.load(f)
    except Exception as e:
        print(f"Не удалось прочитать channels.json: {e}")
        return
        
    playlist = f'#EXTM3U x-tvg-url="{EPG_URL}"\n\n'
    links_found = 0
    
    for ch in channels:
        print(f"\n--- Обработка канала: {ch['name']} ---")
        live_link = get_m3u8_with_click(ch['source_url'])
        
        if live_link:
            print(f"УСПЕХ! Ссылка поймана: {live_link[:80]}...")
            playlist += f'#EXTINF:-1 tvg-id="{ch["tvg_id"]}" tvg-logo="{ch["logo"]}",{ch["name"]}\n'
            playlist += f'{live_link}\n\n'
            links_found += 1
        else:
            print(f"ОШИБКА: Не удалось поймать ссылку для {ch['name']}")
            
    # Записываем файл только если нашли хотя бы одну рабочую ссылку
    if links_found > 0:
        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(playlist)
        print("Файл playlist.m3u успешно перезаписан.")
    else:
        print("Плейлист не создан, так как ни одной ссылки не перехвачено.")

if __name__ == "__main__":
    main()




