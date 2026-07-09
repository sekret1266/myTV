import json
import sys
import os
from playwright.sync_api import sync_playwright

# Очистка консоли перед запуском (для удобства чтения логов в GitHub Actions)
os.system('cls' if os.name == 'nt' else 'clear')

def get_direct_link(url):
    page = None
    browser = None
    try:
        print(f"--- Сканируем страницу: {url} ---")
        found_links = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Перехватчик
            def handle_request(request):
                req_url = request.url
                # Ищем .m3u8, игнорируя рекламу
                if ".m3u8" in req_url and "google" not in req_url and "yandex" not in req_url:
                    if req_url not in found_links:
                        found_links.append(req_url)

            page.on("request", handle_request)

            # Быстрая загрузка и пауза для инициализации плеера
            page.goto(url, timeout=45000, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            # Точный клик по плееру
            try:
                # Пытаемся найти контейнер плеера по селекторам сайта smotrettv
                player_container = page.locator("div[id*='player'], .player-container, #video-player").first
                if player_container.is_visible():
                    player_container.click(timeout=5000)
                    print("Кликнули по контейнеру плеера.")
                else:
                    # Если селекторы не сработали, кликаем по координатам плеера
                    page.mouse.click(450, 320)
                    print("Плеер не найден по селекторам, клик по координатам (450, 320)")
            except Exception:
                try:
                    # Самый крайний случай - клик в центр
                    page.mouse.click(640, 360)
                except:
                    pass

            # Ждем 10 секунд, пока поймаем поток
            page.wait_for_timeout(10000)

            if not found_links:
                page.screenshot(path="error_screen.png", full_page=True)

