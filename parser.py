import json
import urllib.request
import re

EPG_URL = "https://example.com/epg.xml.gz"

def get_direct_link(url):
    try:
        print(f"Сканируем страницу: {url}")
        # Маскируемся под обычный браузер
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            html = response.read().decode('utf-8')
        
        # Ищем любые ссылки, заканчивающиеся на .m3u8 внутри кода страницы
        links = re.findall(r'(https?://[^\s\'"<>]+?\.m3u8[^\s\'"<>]*?)', html)
        
        # Если нашли, убираем мусорные ссылки (метрики, яндекс и т.д.)
        for link in links:
            clean_link = link.replace('\\', '') # убираем экранирование, если оно есть
            if "google" not in clean_link and "yandex" not in clean_link:
                return clean_link
                
        # Хитрый поиск: ищем ссылки на потоки в плеере clappr / hls
        match = re.search(r'source:\s*["\'](https?://[^"\']+)["\']', html)
        if match:
            return match.group(1)
            
    except Exception as e:
        print(f"Ошибка при чтении страницы: {e}")
    return None

def main():
    with open('channels.json', 'r', encoding='utf-8') as f:
        channels = json.load(f)
        
    playlist = f'#EXTM3U x-tvg-url="{EPG_URL}"\n\n'
    links_found = 0
    
    for ch in channels:
        print(f"\n--- Сканирование канала: {ch['name']} ---")
        live_link = get_direct_link(ch['source_url'])
        
        if live_link:
            print(f"УСПЕХ! Ссылка найдена!")
            playlist += f'#EXTINF:-1 tvg-id="{ch["tvg_id"]}" tvg-logo="{ch["logo"]}",{ch["name"]}\n'
            playlist += f'{live_link}\n\n'
            links_found += 1
        else:
            print(f"ОШИБКА: Поток для {ch['name']} не обнаружен")
            
    if links_found > 0:
        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(playlist)
        print("Файл playlist.m3u успешно сохранен.")
    else:
        print("Ссылки не найдены, файл не перезаписан.")

if __name__ == "__main__":
    main()




