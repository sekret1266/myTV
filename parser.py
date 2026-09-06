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
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        
        page = context.new_page()

        # Глобальный перехватчик сетевых запросов
        def handle_request(request):
            url = request.url
            if any(ext in url for ext in ['.m3u8', '.mpd', 'stream', 'playlist']) and 'google' not in url:
                if url not in captured_streams:
                    print(f"[+] Найден поток: {url}")
                    captured_streams.append(url)

        page.on("request", handle_request)

        print(f"Открываем {target_url}...")
        try:
            page.goto(target_url, timeout=30000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось открыть страницу: {e}")
            browser.close()
            return

        page.wait_for_timeout(3000)

        # Безопасный перебор каналов стрелками без зависаний
        for index, ch in enumerate(channels):
            print(f"Обработка канала: {ch['name']}")
            try:
                if index > 0:
                    page.keyboard.press("ArrowDown")
                    page.wait_for_timeout(800)
                
                page.keyboard.press("Enter")
                page.wait_for_timeout(2500) # Ожидание подгрузки потока
            except Exception as ex:
                print(f"[!] Ошибка при переключении: {ex}")

        browser.close()

    print(f"Всего поймано потоков: {len(captured_streams)}")

    results = []
    for index, ch in enumerate(channels):
        stream_url = captured_streams[index] if index < len(captured_streams) else ""
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
            playlist_content += f'#EXTINF:-1 tvg-id="{item["tvg_id"]}" group-title="{item["group"]}" tvg-logo="{item["logo"]}",{item["name"]}\n'
            playlist_content += f'{item["url"]}\n'

        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(playlist_content)
        print("[УСПЕХ] Плейлист обновлен.")
    else:
        print("[ОШИБКА] Не удалось сформировать плейлист.")

if __name__ == "__main__":
    run_parser()

