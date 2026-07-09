import json
import sys
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
            # Убираем след автоматизации Playwright
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Перехватчик сетевых запросов
            def handle_request(request):
                req_url = request.url
                if (".m3u8" in req_url or ".mpd" in req_url) and "google" not in req_url and "yandex" not in req_url:
                    if req_url not in found_links:
                        found_links.append(req_url)

            page.on("request", handle_request)

            # Используем domcontentloaded, чтобы не зависать на бесконечной рекламе
            page.goto(url, timeout=45000, wait_until="domcontentloaded")
            
            # Даем сайту 5 секунд чисто «подышать» и прогрузить плеер на уровне JS
            page.wait_for_timeout(5000)

            # --- ТОЧНЫЙ КЛИК ПО ПЛЕЕРУ ---
            try:
                video_element = page.locator("video").first
                if video_element.is_visible():
                    video_element.click(timeout=5000)
                    print("УСПЕХ: Кликнули точно по элементу <video>.")
                else:
                    player_container = page.locator("div[id*='player'], div[class*='player'], #video-player, .player").first
                    if player_container.is_visible():
                        player_container.click(timeout=5000)
                        print("Элемент video скрыт, кликнули по контейнеру плеера.")
                    else:
                        # Запасной клик по координатам плеера (он обычно в левой верхней части контента)
                        page.mouse.click(450, 320)
                        print("Плеер не найден по селекторам, сделан клик по координатам плеера (450, 320)")
            except Exception as click_err:
                print(f"Ошибка при попытке кликнуть: {click_err}")
                # Самый последний шанс — кликнуть в стандартный центр плеера
                try:
                    page.mouse.click(640, 360)
                except:
                    pass

            # Ждем 10 секунд, пока поток начнет воспроизводиться и мы поймаем ссылку
            page.wait_for_timeout(10000)

            # Если ссылки нет — сохраняем скриншот для отладки
            if not found_links:
                print("Ссылка не найдена, сохраняем скриншот...")
                page.screenshot(path="error_screen.png", full_page=True)

            browser.close()

        if found_links:
            clean_link = found_links[0].replace("\\", "")
            return clean_link

    except Exception as e:
        print(f"Ошибка при перехвате трафика: {e}")
        # Если что-то упало внутри, аварийно пытаемся сохранить скриншот экрана
        try:
            if page:
                page.screenshot(path="error_screen.png", full_page=True)
        except:
            pass
        try:
            if browser:
                browser.close()
        except:
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
        sys.exit(1)

if __name__ == "__main__":
    main()
