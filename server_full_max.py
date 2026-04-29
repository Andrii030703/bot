import time
import requests
import threading
from playwright.sync_api import sync_playwright
import re

# =========================
# CONFIG
# =========================

TOKEN = "ТУТ_TOKEN"
CHAT_IDS = ["ТВОЄ_ID", "ID_ДРУЖИНИ"]

MAX_PRICE = 950
ROOMS = ["2", "2.5", "3", "3.5", "4"]

seen = set()

# =========================
# HELPERS
# =========================

def parse_price(text):
    m = re.search(r"(\d{2,4})\s?€", text)
    return int(m.group(1)) if m else None

def parse_rooms(text):
    m = re.search(r"(\d+(?:[.,]\d+)?)\s?Zimmer", text)
    return m.group(1).replace(",", ".") if m else None

def is_valid(price, rooms):
    try:
        if price and int(price) > MAX_PRICE:
            return False

        if rooms and str(rooms) not in ROOMS:
            return False

        return True
    except:
        return False

def rate(price):
    try:
        p = int(price)
        if p <= 750:
            return "🔥 ТОП"
        elif p <= 900:
            return "👍 НОРМ"
        else:
            return "⚠️"
    except:
        return "❓"

# =========================
# TELEGRAM
# =========================

def send(link, price, rooms):
    rating = rate(price)

    msg = f"""🚨 {rating}

💶 {price if price else "?"} €
🛏 {rooms if rooms else "?"} Zimmer

🔥 ПОДАВАЙ ЗАРАЗ
"""

    for chat_id in CHAT_IDS:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": msg,
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": "⚡ ПОДАТИ", "url": link}]
                    ]
                },
            },
        )

        # 🔔 сигнал
        time.sleep(1)
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "🚨 НОВА КВАРТИРА 🚨",
            },
        )

# =========================
# SAGA API
# =========================

def saga_worker():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def handle_response(response):
            try:
                if "immobilien" not in response.url.lower():
                    return

                if "json" not in response.headers.get("content-type", ""):
                    return

                data = response.json()

                items = data.get("items") if isinstance(data, dict) else data

                for item in items:
                    link = item.get("url")
                    if not link or link in seen:
                        continue

                    price = item.get("price")
                    rooms = item.get("rooms")

                    if not is_valid(price, rooms):
                        continue

                    seen.add(link)
                    send(link, price, rooms)

            except:
                pass

        page.on("response", handle_response)
        page.goto("https://www.saga.hamburg/immobiliensuche")

        while True:
            try:
                page.reload()
                time.sleep(3)
            except:
                time.sleep(5)

# =========================
# IMMOSCOUT
# =========================

def immoscout_worker():
    URL = "https://www.immobilienscout24.de/Suche/de/hamburg/hamburg/wohnung-mieten"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        while True:
            try:
                page.goto(URL)
                page.wait_for_timeout(4000)

                cards = page.locator("article").all()

                for card in cards:
                    text = card.inner_text()

                    if "Zimmer" not in text:
                        continue

                    href = card.locator("a").first.get_attribute("href")
                    if not href:
                        continue

                    link = "https://www.immobilienscout24.de" + href

                    if link in seen:
                        continue

                    price = parse_price(text)
                    rooms = parse_rooms(text)

                    if not is_valid(price, rooms):
                        continue

                    seen.add(link)
                    send(link, price, rooms)

            except:
                pass

            time.sleep(6)

# =========================
# COOPERATIVES
# =========================

GEN_URLS = [
    "https://www.bauverein-der-elbgemeinden.de",
    "https://www.bgfg.de",
    "https://www.hamburgerwohnen.de",
]

def gen_worker():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        while True:
            for url in GEN_URLS:
                try:
                    page.goto(url)
                    page.wait_for_timeout(4000)

                    for a in page.locator("a").all():
                        href = a.get_attribute("href")

                        if not href:
                            continue

                        if "wohnung" not in href.lower():
                            continue

                        link = href if href.startswith("http") else url + href

                        if link in seen:
                            continue

                        seen.add(link)
                        send(link, None, None)

                except:
                    continue

            time.sleep(8)

# =========================
# START
# =========================

if __name__ == "__main__":
    print("🔥 FULL MAX BOT STARTED")

    threading.Thread(target=saga_worker, daemon=True).start()
    threading.Thread(target=immoscout_worker, daemon=True).start()
    threading.Thread(target=gen_worker, daemon=True).start()

    while True:
        time.sleep(10)
