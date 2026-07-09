import json
import traceback
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth

def get_direct_link(url):
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
            stealth(page)
            
            def handle_request(request):
                req_url = request.url
                if ".m3u8" in req_url and "google" not in req_url and "yandex" not in req_url:
                    found_links.append(req_url)
            
            page.on("request", handle_request)
            
            print("Открываем сайт...")
            # Ставим таймаут поменьше и обрабатываем сбой загрузки страницы
            try:
                page.goto(url, timeout=20000, wait_until="load")
            except Exception as e:
                print(f"Предупреждение: Страница не загрузилась полностью: {e}")
            
            page.wait_for_timeout(4000) 
            
            print("Пробуем кликнуть по координатам плеера...")
            try:
                page.mouse.click(640, 360)
                print("Клик выполнен успешно.")
            except Exception as e:
                print(f"Не удалось кликнуть: {e}")
            
            page.wait_for_timeout(6000)
            
            # Делаем скриншот в любом случае для диагностики
            print("Сохраняем скриншот экрана...")
            page.screenshot(path="error_screen.png", full_page=True)
            
            browser.close()
            
        if found_links:
            clean_link = found_links[0].replace("\\", "")
            return clean_link
            
    except Exception as e:
        print(f"Критическая ошибка внутри get_direct_link: {e}")
        traceback.print_exc()
        if browser:
            try:
                browser.close()
            except:
                pass
    return None

def main():
    with open('channels.json', 'r', encoding='utf-8') as f:
        channels = json.load(f)
        
    playlist = '#EXTM3U x-tvg-url="(EPG_URL)"\n\n'
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

if __name__ == "__main__":
    main()
