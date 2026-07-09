import json
import sys
from playwright.sync_api import sync_playwright

def get_direct_link(url):
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
            # Маскировка: убираем след автоматизации Playwright
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Функция-перехватчик сетевых запросов
            def handle_request(request):
                req_url = request.url
                if ".m3u8" in req_url and "req_url" and "google" not in req_url and "yandex" not in req_url:
                    found_links.append(req_url)

            page.on("request", handle_request)

            # Ждем загрузку DOM структуры страницы
            page.goto(url, timeout=45000, wait_until="domcontentloaded")

            # Даем плееру время подумать и прогрузиться
            page.wait_for_timeout(3000)

            # Пытаемся кликнуть по плееру/видео, чтобы активировать поток
            try:
                page.click("video", timeout=5000)
            except Exception:
                pass

            # Даем еще 7 секунд, чтобы поймать вылетающие ссылки
            page.wait_for_timeout(7000)

            # Если ссылки так и не появились — делаем скриншот внутри блока try
            if not found_links:
                print("Ссылка не найдена, сохраняем скриншот...")
                page.screenshot(path="error_screen.png", full_page=True)

            browser.close()

        if found_links:
            clean_link = found_links[0].replace("\\", "")
            return clean_link

    except Exception as e:
        print(f"Ошибка при перехвате трафика: {e}")
        # На случай непредвиденной ошибки пытаемся сделать скриншот перед выходом
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
