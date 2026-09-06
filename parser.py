import json
import os
import sys
from playwright.sync_api import sync_playwright

def run_parser():
    # Загрузка списка каналов из файла channels.json
    try:
        with open('channels.json', 'r', encoding='utf-8') as f:
            channels = json.load(f)
    except Exception as e:
        print(f"[ОШИБКА] Не удалось прочитать channels.json: {e}")
        return

    # Исправленный адрес сайта (drm-play.com)
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

        # Функция перехвата сетевых запросов
        def handle_request(request):
            req_url = request.url
            if (".m3u8" in req_url or ".mpd" in req_url) and "google" not in req_url and "yandex" not in req_url:
                if not captured_streams or captured_streams[-1] != req_url:
                    print(f"[+] Перехвачен поток: {req_url[:80]}...")
                    captured_streams.append(req_url)

        page.on("request", handle_request)

        print(f"Открываем страницу {target_url}...")
        page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        # Закрытие модального окна "Подтверждение Ссылок" (кнопка Продолжить)
        try:
            confirm_btn = page.locator("text='Продолжить'")
            if confirm_btn.is_visible():
                confirm_btn.click()
                print("Закрыто стартовое предупреждение.")
                page.wait_for_timeout(2000)
        except Exception:
            pass

        print("Активируем интерфейс (клик по центру)...")
        page.mouse.click(640, 360)
        page.wait_for_timeout(2000)

        results = []

        # Цикл прохода по каналам из channels.json
        for index, ch in enumerate(channels):
            print(f"Переключение на канал #{index + 1}: {ch['name']}")
            if index > 0:
                page.keyboard.press("ArrowDown")
                page.wait_for_timeout(500)

            start_count = len(captured_streams)
            page.keyboard.press("Enter")

            for _ in range(10):
                if len(captured_streams) > start_count:
                    break
                page.wait_for_timeout(500)

            stream_url = captured_streams[-1] if len(captured_streams) > start_count else ""
            if stream_url:
                results.append({
                    "name": ch["name"],
                    "tvg_id": ch.get("tvg_id", ""),
                    "group": ch.get("group", "Общественные"),
                    "logo": ch.get("logo", ""),
                    "url": stream_url
                })
            else:
                print(f"[-] Не удалось перехватить ссылку для {ch['name']}")

        browser.close()

    # Формирование итогового плейлиста M3U
    if results:
        playlist_content = '#EXTM3U url-tvg="https://epg.iptvx.one/epg.xml.gz"\n'
        for item in results:
            playlist_content += f'#EXTINF:-1 tvg-id="{item["tvg_id"]}" tvg-logo="{item["logo"]}" group-title="{item["group"]}",{item["name"]}\n'
            playlist_content += f'{item["url"]}\n'

        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write(playlist_content)
        print(f"[УСПЕХ] Сформирован плейлист playlist.m3u с {len(results)} каналами.")
    else:
        print("[ОШИБКА] Ссылки на потоки не были перехвачены.")

if __name__ == "__main__":
    run_parser()
