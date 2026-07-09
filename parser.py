import json
import sys
from playwright.sync_api import sync_playwright

def get_direct_link(url):
    try:
        print(f"Сканируем страницу и ловим сетевые запросы: {url}")
        found_links = []

        with sync_playwright() as p:
            # Запускаем браузер с эмуляцией реального экрана
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            
            page = context.new_page()
            # Убираем след автоматизации Playwright
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Расширенный перехват: ловим запросы со всей страницы (включая iframe)
            def handle_request(request):
                req_url = request.url
                # Ищем файлы плейлистов (.m3u8 или .mpd), игнорируя рекламу и метрики
                if (".m3u8" in req_url or ".mpd" in req_url) and "google" not in req_url and "yandex" not in req_url:
                    if req_url not in found_links:
                        found_links.append(req_url)

            page.on("request", handle_request)

            # Переходим на сайт и ждем полной загрузки сети
            page.goto(url, timeout=60000, wait_until="networkidle")
            page.wait_for_timeout(3000)

            # --- ЭМУЛЯЦИЯ КЛИКА ПО ПЛЕЕРУ ---
            try:
                # Кликаем мышкой точно по центру экрана (где находится плеер)
                page.mouse.click(640, 360)
                print("Сделан клик мышью по центру экрана для запуска плеера...")
            except Exception as click_err:
                print(f"Не удалось кликнуть по координатам: {click_err}")

            # На всякий случай кликаем по тегам элементов
            for selector in ["video", "div[class*='player']", "div[id*='player']", "iframe"]:
                try:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).first.click(timeout=2000)
                except Exception:
                    pass

            # Даем 10 секунд при запущенном плеере, чтобы поймать ссылку на поток
            page.wait_for_timeout(10000)

            # Если ссылки нет — делаем свежий скриншот
            if not found_links:
                print("Ссылка не найдена, сохраняем скриншот...")
                page.screenshot(path="error_screen.png", full_page=True)

            browser.close()

        if found_links:
            clean_link = found_links[0].replace("\\", "")
            return clean_link

    except Exception as e:
        print(f"Ошибка при перехвате трафика: {e}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url)
                page.screenshot(path="error_screen.png", full_page=True)
                browser.close()
        except Exception:
            pass
            
    return None

def main():
    with open('channels.json', 'r', encoding='utf-8') as f:
        channels = json.load(f)

    playlist = "#EXTM3U x-tvg-url=\"(EPG_URL)\"\n"
    links_found = 0

    for ch in channels:
        print(f"\n--- Сканирование канала: {ch['name']} ---")
        live_link = get_direct_link(ch['source_url'])

        if live_link:
            print("УСПЕХ! Прямая ссылка найдена!")
            playlist += f"#EXTINF:-1 tvg-id=\"{ch['tvg_id']}\" tvg-logo=\"{ch['logo']}\",{ch['name']}\n"
            playlist += f"{live_link}\n"
            links_found += 1
        else:
            print(f"ОШИБКА: Поток для {ch['name']} не обнаружен")

    if links_found > 0:
        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(playlist)
        print("Файл playlist.m3u успешно сохранен и обновлен.")
    else:
        print("Ссылки не найдены, файл не перезаписан.")
        # Завершаем работу с кодом 1, чтобы GitHub Actions понял, что произошла ошибка
        sys.exit(1)

if __name__ == "__main__":
    main()
