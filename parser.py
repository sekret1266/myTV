import json
import sys
import os
from playwright.sync_api import sync_playwright

# Очистка консоли перед запуском (для удобства чтения логов в GitHub Actions)
os.system('cls' if os.name == 'nt' else 'clear')

def get_direct_link(url):
    page = None
    browser = None
    try:
        print(f"--- Сканируем страницу: {url} ---")
        found_links = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Перехватчик
            def handle_request(request):
                req_url = request.url
                # Ищем .m3u8, игнорируя рекламу
                if ".m3u8" in req_url and "google" not in req_url and "yandex" not in req_url:
                    if req_url not in found_links:
                        found_links.append(req_url)

            page.on("request", handle_request)

            # Быстрая загрузка и пауза для инициализации плеера
            page.goto(url, timeout=45000, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            # Точный клик по плееру
            try:
                # Пытаемся найти контейнер плеера по селекторам сайта smotrettv
                player_container = page.locator("div[id*='player'], .player-container, #video-player").first
                if player_container.is_visible():
                    player_container.click(timeout=5000)
                    print("Кликнули по контейнеру плеера.")
                else:
                    # Если селекторы не сработали, кликаем по координатам плеера
                    page.mouse.click(450, 320)
                    print("Плеер не найден по селекторам, клик по координатам (450, 320)")
            except Exception:
                try:
                    # Самый крайний случай - клик в центр
                    page.mouse.click(640, 360)
                except:
                    pass

            # Ждем 10 секунд, пока поймаем поток
            page.wait_for_timeout(10000)

            if not found_links:
                page.screenshot(path="error_screen.png", full_page=True)
                print("Ссылка не найдена, сделан скриншот.")

            browser.close()

        if found_links:
            # Очистка ссылки
            clean_link = found_links[0].replace("\\", "").strip("'\"")
            return clean_link

    except Exception as e:
        print(f"Ошибка при парсинге: {e}")
        try:
            if page: page.screenshot(path="error_screen.png", full_page=True)
        except: pass
        try:
            if browser: browser.close()
        except: pass
            
    return None

def main():
    # Проверяем наличие файла channels.json
    if not os.path.exists('channels.json'):
        print("ОШИБКА: Файл channels.json не найден!")
        sys.exit(1)

    with open('channels.json', 'r', encoding='utf-8') as f:
        try:
            channels = json.load(f)
        except json.JSONDecodeError:
            print("ОШИБКА: channels.json содержит невалидный JSON!")
            sys.exit(1)

    # Стандартный заголовок плейлиста
    playlist_content = "#EXTM3U\n"
    links_found = 0

    # Обрабатываем наш один канал
    if channels and len(channels) > 0:
        ch = channels[0] # Берем первый (и единственный) канал из списка
        
        print(f"\n<<< Обработка канала: {ch.get('name', 'Без названия')} >>>")
        live_link = get_direct_link(ch['source_url'])

        if live_link:
            print(f"УСПЕХ! Нашли рабочую ссылку.")
            
            # Собираем данные EPG и Логотипа
            tvg_id = ch.get('tvg_id', '')
            logo = ch.get('logo', '')
            name = ch.get('name', 'Unknown')

            # ЧИСТАЯ ФОРМИРОВКА СТРОКИ M3U (без лишних слешей и пустых мест)
            inf_line = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}",{name}\n'
            
            # Добавляем в плейлист
            playlist_content += inf_line
            playlist_content += f'{live_link}\n'
            links_found += 1
        else:
            print(f"ОШИБКА: Не удалось получить поток для канала.")

    # Сохраняем результат
    if links_found > 0:
        # Убираем возможные лишние пробелы/переносы в конце всего текста
        final_playlist = playlist_content.strip() + "\n"
        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(final_playlist)
        print("\nФайл playlist.m3u успешно сохранен и содержит 1 канал.")
    else:
        print("\nСсылки не найдены, файл не перезаписан.")
        # GitHub Actions упадет, чтобы вы знали, что автообновление не сработало
        sys.exit(1)

if __name__ == "__main__":
    main()
