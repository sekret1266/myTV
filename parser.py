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
    results = []

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

        print(f"Открываем {target_url}...")
        try:
            page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось открыть страницу: {e}")
            browser.close()
            return

        page.wait_for_timeout(5000)

        # Проходим по каждому каналу из нашего списка
        for index, ch in enumerate(channels):
            channel_name = ch['name']
            print(f"Обработка канала: {channel_name}")
            
            captured_stream = None

            # Перехватываем запрос, который уходит при клике на конкретный канал
            def handle_request(request):
                nonlocal captured_stream
                url = request.url
                if any(ext in url for ext in ['.m3u8', '.mpd', 'stream']) and 'google' not in url:
                    captured_stream = url

            # Включаем прослушку сети на момент клика
            page.on("request", handle_request)

            try:
                # Пытаемся найти элемент канала на странице по названию или тексту и кликнуть по нему
                # Если сайт использует другую верстку, здесь может понадобиться точный селектор
                channel_element = page.locator(f"text={channel_name}").first
                if channel_element.count() > 0:
                    channel_element.click()
                else:
                    # Запасной вариант: клик по координатам или навигация стрелками, если текст не найден
                    page.keyboard.press("ArrowDown")
                    page.keyboard.press("Enter")
                
                # Ждем, пока пойдет сетевой запрос потока
                page.wait_for_timeout(3000)
            except Exception as e:
                print(f"[!] Ошибка при клике на канал {channel_name}: {e}")

            # Отключаем обработчик, чтобы не перепутать потоки
            page.remove_listener("request", handle_request)

            if captured_stream:
                print(f"[+] Пойман поток для {channel_name}: {captured_stream}")
            else:
                print(f"[-] Не удалось поймать поток для {channel_name}")
                captured_stream = ""

            results.append({
                "name": channel_name,
                "tvg_id": ch.get("tvg_id", ""),
                "group": ch.get("group", "Общественные"),
                "logo": ch.get("logo", ""),
                "url": captured_stream
            })

        browser.close()

    valid_results = [r for r in results if r["url"]]
    print(f"Всего успешно поймано потоков: {len(valid_results)} из {len(channels)}")

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
