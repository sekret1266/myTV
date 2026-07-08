import json
import time
import os
from playwright.sync_api import sync_playwright

EPG_URL = "https://iptvx.one/EPG_NOARCH"

def get_m3u8_with_click(url):
    m3u8_link = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        
        def handle_request(request):
            nonlocal m3u8_link
            req_url = request.url
            if ".m3u8" in req_url or "playlist" in req_url or "stream" in req_url:
                if "google" not in req_url and "yandex" not in req_url and "doubleclick" not in req_url:
                    m3u8_link = req_url

        page.on("request", handle_request)
        try:
            print(f"Открываем страницу: {url}")
            page.goto(url, wait_until="load", timeout=40000)
            time.sleep(5)
            page.mouse.click(640, 360)
            time.sleep(3)
            if page.locator("text=Плеер 1").is_visible():
                page.locator("text=Плеер 1").click()
                time.sleep(2)
            for selector in ["video", "object", "embed", ".play-btn", "[class*='player']"]:
                if page.locator(selector).first.is_visible():
                    page.locator(selector).first.click()
                    time.sleep(2)
            time.sleep(10)
            if not m3u8_link:
                page.screenshot(path="error_screen.png")
        except Exception as e:
            print(f"Ошибка в браузере: {e}")
        finally:
            browser.close()
    return m3u8_link



