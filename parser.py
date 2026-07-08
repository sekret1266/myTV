import json
import time
from playwright.sync_api import sync_playwright

# Вставь сюда свою ссылку на телепрограмму, если она есть
EPG_URL = "https://iptvx.one/EPG_NOARCH"

def get_m3u8_with_click(url):
    m3u8_link = None
    
    with sync_playwright() as p:
        # Запускаем браузер
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Ловим ссылки .m3u8 в сетевых запросах
        def handle_request(request):
            nonlocal m3u8_link
            if ".m3u8" in request.url and "playlist" in request.url.lower() or ".m3u8" in request.url:
                # Игнорируем второстепенные рекламные ссылки, если они будут
                if "google" not in request.url and "yandex" not in request.url:
                    m3u8_link = request.url

        page.on("request", handle_request)
        
        try:
            print(f"Открываем страницу: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3) # Даем плееру отрисоваться
            
            # Кликаем точно по иконке Плей по центру экрана
            # На сайтах вроде smotrettv клик по тегу video или кнопке запускает поток
            if page.locator("video").is_visible():
                page.locator("video").click()
                print("Кликнули по плееру (тег video)")
            else:
                page.mouse.click(500, 400)
                print("Плеер не найден, кликнули в координаты центра")

            # Ждем 10 секунд, чтобы поток успел запуститься и ссылка отобразилась в сети
            time.sleep(10)
            
        except Exception as e:
            print(f"Ошибка при работе с браузером: {e}")
        finally:
            browser.close()
            
    return m3u8_link



