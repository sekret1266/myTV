import json
import os
import sys
from playwright.sync_api import sync_playwright

def run_parser():
    try:
        with open('channels.json', 'r', encoding='utf-8') as f:
            channels = json.load(f)
    except Exception as e:
        print(f"[ОШИБКА] Не удалось прочитать channels.json: {e}")
        return

    target_url = "http://ott.drm-play.com"
    captured_streams = set()

    with sync_playwright() as p:
        print("Запуск браузера Chromium...")
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        # Глобальный перехватчик любых потоков (.m3u8 или .mpd) во время работы страницы
        def handle_request(request):
            req_url = request.url
            if any(ext in req_url for ext in [".m3u8", ".mpd", "playlist", "stream"]):
                if "google" not in req_url and "yandex" not in req_url and req_url not in captured_streams:
                    print(f"[+] Найден поток: {req_url[:80]}...")
                    captured_streams.add(req_url)

        page.on("request", handle_request)

        print(f"Открываем страницу {target_url}...")
        page.goto(target_url, timeout=60000, wait_until="networkidle")
        
        # Даем время плееру прогрузить плейлист и фоновые потоки
        print("Ожидание инициализации потоков плеера...")
        page.wait_for_timeout(10000)

        # Кликаем по центру для активации контента
        page.mouse.click(640, 360)
        page.wait_for_timeout(5000)

        browser.close()

    # Собираем уникальные потоки
    streams_list = list(captured_streams)
    print(f"Всего перехвачено уникальных потоков: {len(streams_list)}")

    results = []
    # Сопоставляем каналы из channels.json с найденными потоками
    for index, ch in enumerate(channels):
        stream_url = ""
        if index < len(streams_list):
            stream_url = streams_list[index]
        elif streams_list:
            stream_url = streams_list[0] # Запасной вариант, если потоков меньше чем каналов

        results.append({
            "name": ch["name"],
            "tvg_id": ch.get("tvg_id", ""),
            "group": ch.get("group", "Общественные"),
            "logo": ch.get("logo", ""),
            "url": stream_url
        })

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

