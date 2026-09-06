import json
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
        print("Запуск браузера...")
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--autoplay-policy=no-user-gesture-required"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        # Перехватчик сетевых запросов с фиксацией любых потоков
        def handle_request(request):
            url = request.url
            if (".m3u8" in url or ".mpd" in url) and "google" not in url and "yandex" not in url:
                if url not in captured_streams:
                    print(f"[+] Найден поток: {url}")
                    captured_streams.append(url)

        page.on("request", handle_request)

        print(f"Открываем {target_url}...")
        page.goto(target_url, timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(5000)

        # Клик для активации интерфейса плеера
        page.mouse.click(640, 360)
        page.wait_for_timeout(3000)

        # Проходим по списку каналов для вызова потоков
        for index, ch in enumerate(channels):
            print(f"Обработка канала: {ch['name']}")
            if index > 0:
                page.keyboard.press("ArrowDown")
                page.wait_for_timeout(800)
            
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000) # Ожидание подгрузки потока

        browser.close()

    print(f"Всего поймано потоков: {len(captured_streams)}")

    results = []
    for index, ch in enumerate(channels):
        # Подставляем пойманный поток или оставляем заглушку, если поток не найден
        stream_url = captured_streams[index] if index < len(captured_streams) else (captured_streams[0] if captured_streams else "http://invalid.link/stream.m3u8")
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
        print(f"[УСПЕХ] Плейлист обновлен, каналов: {len(results)}")
    else:
        print("[ОШИБКА] Не удалось сформировать плейлист.")

if __name__ == "__main__":
    run_parser()

