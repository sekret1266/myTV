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
    captured_streams = []

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

        def handle_request(request):
            req_url = request.url
            # Строгий фильтр: ищем только реальные потоки m3u8/mpd, исключая статику и GitHub
            if any(ext in req_url for ext in [".m3u8", ".mpd"]) and "github" not in req_url and "ipetv" not in req_url:
                if req_url not in captured_streams:
                    print(f"[+] Найден видеопоток: {req_url[:80]}...")
                    captured_streams.append(req_url)

        page.on("request", handle_request)

        print(f"Открываем страницу {target_url}...")
        page.goto(target_url, timeout=60000, wait_until="networkidle")
        
        # Ожидание загрузки плеера
        page.wait_for_timeout(8000)
        page.mouse.click(640, 360)
        page.wait_for_timeout(5000)

        browser.close()

    results = []
    for index, ch in enumerate(channels):
        stream_url = captured_streams[index] if index < len(captured_streams) else (captured_streams[0] if captured_streams else "")
        results.append({
            "name": ch["name"],
            "tvg_id": ch.get("tvg_id", ""),
            "group": ch.get("group", "Общественные"),
            "logo": ch.get("logo", ""),
            "url": stream_url
        })

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

