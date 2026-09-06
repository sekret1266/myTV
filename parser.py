import json
import os
import sys
from playwright.sync_api import sync_playwright

def run_parser():
    # Файл с названиями и метаданными каналов в порядке их следования в списке
    channels = [
        {"name": "Первый канал Время", "tvg_id": "1channel_vremya", "logo": "https://epg.iptvx.one/picons/1channel.png"},
        {"name": "Первый канал HD", "tvg_id": "1channel", "logo": "https://epg.iptvx.one/picons/1channel.png"},
        {"name": "Россия 1 HD", "tvg_id": "rossiya1", "logo": "https://epg.iptvx.one/picons/rossiya1.png"},
        {"name": "Россия 1", "tvg_id": "rossiya1_sd", "logo": "https://epg.iptvx.one/picons/rossiya1.png"},
        {"name": "Россия 24 HD", "tvg_id": "rossiya24", "logo": "https://epg.iptvx.one/picons/rossiya24.png"},
        {"name": "Россия 24", "tvg_id": "rossiya24_sd", "logo": "https://epg.iptvx.one/picons/rossiya24.png"},
        {"name": "Россия Культура HD", "tvg_id": "rossiyak", "logo": "https://epg.iptvx.one/picons/rossiya-k.png"},
        {"name": "Россия Культура", "tvg_id": "rossiyak_sd", "logo": "https://epg.iptvx.one/picons/rossiya-k.png"},
        {"name": "НТВ HD", "tvg_id": "ntv", "logo": "https://epg.iptvx.one/picons/ntv.png"},
        {"name": "НТВ", "tvg_id": "ntv_sd", "logo": "https://epg.iptvx.one/picons/ntv.png"}
    ]

    target_url = "http://ott.drm-play.com"
    captured_streams = []

    with sync_playwright() as p:
        print("Запуск браузера Chromium...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        # Обход встроенных проверок на автоматизацию
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Функция перехвата сетевых запросов
        def handle_request(request):
            req_url = request.url
            if (".m3u8" in req_url or ".mpd" in req_url) and "google" not in req_url and "yandex" not in req_url:
                if not captured_streams or captured_streams[-1] != req_url:
                    print(f"  [+] Перехвачен поток: {req_url[:80]}...")
                    captured_streams.append(req_url)

        page.on("request", handle_request)

        print(f"Открываем страницу {target_url}...")
        page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        # Закрытие стартовых модальных окон
        try:
            confirm_btn = page.locator("text=Продолжить")
            if confirm_btn.is_visible():
                confirm_btn.click()
                print("Закрыто стартовое предупреждение.")
                page.wait_for_timeout(2000)
        except Exception:
            pass

        # 1. Клик по центру экрана для снятия фокуса и вызова списка каналов
        print("Активируем интерфейс (клик по центру)...")
        page.mouse.click(640, 360)
        page.wait_for_timeout(2000)

        results = []

        # 2. Цикл прохода по каналам с помощью клавиш клавиатуры
        for index, ch in enumerate(channels):
            print(f"\nПереключение на канал #{index + 1}: {ch['name']}")

            # Если это не первый канал, нажимаем ArrowDown для перехода к следующей строчке
            if index > 0:
                page.keyboard.press("ArrowDown")
                page.wait_for_timeout(500)

            # Нажимаем Enter для выбора и запуска потока
            start_count = len(captured_streams)
            page.keyboard.press("Enter")

            # Ожидаем появления нового перехваченного .m3u8 файла
            for _ in range(10):
                if len(captured_streams) > start_count:
                    break
                page.wait_for_timeout(500)

            # Сохраняем найденную ссылку
            stream_url = captured_streams[-1] if captured_streams else ""
            if stream_url:
                results.append({
                    "name": ch["name"],
                    "tvg_id": ch["tvg_id"],
                    "logo": ch["logo"],
                    "url": stream_url
                })
            else:
                print(f"  [-] Не удалось перехватить ссылку для {ch['name']}")

        # Делаем скриншот финального состояния для проверки
        page.screenshot(path="final_screen.png")
        browser.close()

    # 3. Формирование итогового плейлиста M3U8
    if results:
        playlist_content = "#EXTM3U\n"
        for item in results:
            playlist_content += f'#EXTINF:-1 tvg-id="{item["tvg_id"]}" tvg-logo="{item["logo"]}",{item["name"]}\n'
            playlist_content += '#EXTVLCOPT:http-user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"\n'
            playlist_content += f'{item["url"]}\n'

        with open("playlist.m3u8", "w", encoding="utf-8") as f:
            f.write(playlist_content)
        print(f"\n[УСПЕХ] Сформирован плейлист playlist.m3u8 с {len(results)} каналами.")
    else:
        print("\n[ОШИБКА] Ссылки на потоки не были перехвачены.")

if __name__ == "__main__":
    run_parser()
import json
import os
import sys
from playwright.sync_api import sync_playwright

def run_parser():
    # Файл с названиями и метаданными каналов в порядке их следования в списке
    channels = [
        {"name": "Первый канал Время", "tvg_id": "1channel_vremya", "logo": "https://epg.iptvx.one/picons/1channel.png"},
        {"name": "Первый канал HD", "tvg_id": "1channel", "logo": "https://epg.iptvx.one/picons/1channel.png"},
        {"name": "Россия 1 HD", "tvg_id": "rossiya1", "logo": "https://epg.iptvx.one/picons/rossiya1.png"},
        {"name": "Россия 1", "tvg_id": "rossiya1_sd", "logo": "https://epg.iptvx.one/picons/rossiya1.png"},
        {"name": "Россия 24 HD", "tvg_id": "rossiya24", "logo": "https://epg.iptvx.one/picons/rossiya24.png"},
        {"name": "Россия 24", "tvg_id": "rossiya24_sd", "logo": "https://epg.iptvx.one/picons/rossiya24.png"},
        {"name": "Россия Культура HD", "tvg_id": "rossiyak", "logo": "https://epg.iptvx.one/picons/rossiya-k.png"},
        {"name": "Россия Культура", "tvg_id": "rossiyak_sd", "logo": "https://epg.iptvx.one/picons/rossiya-k.png"},
        {"name": "НТВ HD", "tvg_id": "ntv", "logo": "https://epg.iptvx.one/picons/ntv.png"},
        {"name": "НТВ", "tvg_id": "ntv_sd", "logo": "https://epg.iptvx.one/picons/ntv.png"}
    ]

    target_url = "http://ott.drm-play.com"
    captured_streams = []

    with sync_playwright() as p:
        print("Запуск браузера Chromium...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        # Обход встроенных проверок на автоматизацию
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Функция перехвата сетевых запросов
        def handle_request(request):
            req_url = request.url
            if (".m3u8" in req_url or ".mpd" in req_url) and "google" not in req_url and "yandex" not in req_url:
                if not captured_streams or captured_streams[-1] != req_url:
                    print(f"  [+] Перехвачен поток: {req_url[:80]}...")
                    captured_streams.append(req_url)

        page.on("request", handle_request)

        print(f"Открываем страницу {target_url}...")
        page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        # Закрытие стартовых модальных окон
        try:
            confirm_btn = page.locator("text=Продолжить")
            if confirm_btn.is_visible():
                confirm_btn.click()
                print("Закрыто стартовое предупреждение.")
                page.wait_for_timeout(2000)
        except Exception:
            pass

        # 1. Клик по центру экрана для снятия фокуса и вызова списка каналов
        print("Активируем интерфейс (клик по центру)...")
        page.mouse.click(640, 360)
        page.wait_for_timeout(2000)

        results = []

        # 2. Цикл прохода по каналам с помощью клавиш клавиатуры
        for index, ch in enumerate(channels):
            print(f"\nПереключение на канал #{index + 1}: {ch['name']}")

            # Если это не первый канал, нажимаем ArrowDown для перехода к следующей строчке
            if index > 0:
                page.keyboard.press("ArrowDown")
                page.wait_for_timeout(500)

            # Нажимаем Enter для выбора и запуска потока
            start_count = len(captured_streams)
            page.keyboard.press("Enter")

            # Ожидаем появления нового перехваченного .m3u8 файла
            for _ in range(10):
                if len(captured_streams) > start_count:
                    break
                page.wait_for_timeout(500)

            # Сохраняем найденную ссылку
            stream_url = captured_streams[-1] if captured_streams else ""
            if stream_url:
                results.append({
                    "name": ch["name"],
                    "tvg_id": ch["tvg_id"],
                    "logo": ch["logo"],
                    "url": stream_url
                })
            else:
                print(f"  [-] Не удалось перехватить ссылку для {ch['name']}")

        # Делаем скриншот финального состояния для проверки
        page.screenshot(path="final_screen.png")
        browser.close()

    # 3. Формирование итогового плейлиста M3U8
    if results:
        playlist_content = "#EXTM3U\n"
        for item in results:
            playlist_content += f'#EXTINF:-1 tvg-id="{item["tvg_id"]}" tvg-logo="{item["logo"]}",{item["name"]}\n'
            playlist_content += '#EXTVLCOPT:http-user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"\n'
            playlist_content += f'{item["url"]}\n'

        with open("playlist.m3u8", "w", encoding="utf-8") as f:
            f.write(playlist_content)
        print(f"\n[УСПЕХ] Сформирован плейлист playlist.m3u8 с {len(results)} каналами.")
    else:
        print("\n[ОШИБКА] Ссылки на потоки не были перехвачены.")

if __name__ == "__main__":
    run_parser()

