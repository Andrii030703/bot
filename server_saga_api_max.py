import time
import requests
from playwright.sync_api import sync_playwright

# =========================
# CONFIG
# =========================

TOKEN = "8548267283:AAEFAN5LxgjkLcUltKPpfQ85M_2REZ6NsEU"
CHAT_IDS = ["8002075187", "7813659703"]

MAX_PRICE = 950
ROOMS = ["2", "2.5", "3", "3.5", "4"]

seen = set()

# =========================
# RATING
# =========================

def rate(price):
    try:
        p = int(price)
        if p <= 750:
            return "🔥 ТОП"
        elif p <= 900:
            return "👍 НОРМ"
        else:
            return "⚠️ ДОРОГО"
    except:
        return "❓"

# =========================
# FILTER
# =========================

def is_valid(price, rooms):
    try:
        if price and int(price) > MAX_PRICE:
            return False

        if rooms:
            r = str(rooms).replace(",", ".")
            if r not in ROOMS:
                return False

        return True
    except:
        return False

# =========================
# TELEGRAM
# =========================

def send(link, price, rooms):
    rating = rate(price)

    msg = f"""🚨 {rating} SAGA

💶 {price} €
🛏 {rooms} Zimmer

🔥 ПОДАВАЙ ЗАРАЗ
"""

    for chat_id in CHAT_IDS:
        # основне повідомлення
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

        # 🔔 другий сигнал
        time.sleep(1)
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "🚨🚨 НОВА КВАРТИРА 🚨🚨",
            },
        )

# =========================
# MAIN
# =========================

def run():
    print("🔥 SAGA API MAX STARTED")

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

                if isinstance(data, dict):
                    items = data.get("items") or data.get("data") or []
                else:
                    items = data

                for item in items:
                    try:
                        link = item.get("url") or item.get("link")

                        if not link or link in seen:
                            continue

                        price = item.get("price") or item.get("rent")
                        rooms = item.get("rooms")

                        if not is_valid(price, rooms):
                            continue

                        seen.add(link)

                        send(link, price, rooms)

                    except:
                        continue

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
# START
# =========================

if __name__ == "__main__":
    run()
