import time, requests, re, os, random
from playwright.sync_api import sync_playwright

TOKEN = os.getenv("TOKEN")
CHAT_IDS = os.getenv("CHAT_IDS").split(",")

SOURCES = [
    ("SAGA", "https://www.saga.hamburg/immobiliensuche", "https://www.saga.hamburg"),
    ("SCOUT", "https://www.immobilienscout24.de/Suche/de/hamburg/hamburg/wohnung-mieten", "https://www.immobilienscout24.de"),
    ("WG", "https://www.wg-gesucht.de/wohnungen-in-Hamburg.55.2.1.0.html", "https://www.wg-gesucht.de"),
]

MAX_PRICE = 950
ROOMS = ["2","2.5","3","3.5","4"]

GOOD = ["saga","genossenschaft","wohnungsbau","öffentlich","sozial"]
BAD = ["makler","gmbh","agentur","immobilien"]

seen = set()

def send(source, link, price, rooms):
    for chat_id in CHAT_IDS:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
            "chat_id": chat_id,
            "text": f"🔥 {source} КВАРТИРА\n💶 {price}€\n🛏 {rooms} Zimmer\n\n{link}",
            "reply_markup": {
                "inline_keyboard": [
                    [{"text": "⚡ ПОДАТИ ЗАРАЗ", "url": link}]
                ]
            }
        })

def is_good(text):
    text = text.lower()
    score = 0
    for g in GOOD:
        if g in text:
            score += 2
    for b in BAD:
        if b in text:
            score -= 2
    return score >= 2

def parse_price(text):
    m = re.search(r"(\d{2,4})", text)
    return int(m.group(1)) if m else None

def parse_rooms(text):
    m = re.search(r"(\d+(?:[.,]\d+)?)", text)
    return m.group(1) if m else None

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🔥 FULL PRO BOT STARTED")

        while True:
            try:
                for name, url, base in SOURCES:
                    page.goto(url)
                    time.sleep(2)

                    for a in page.locator("a").all():
                        try:
                            href = a.get_attribute("href")
                            text = a.inner_text()

                            if not href or not text:
                                continue

                            if not is_good(text):
                                continue

                            price = parse_price(text)
                            rooms = parse_rooms(text)

                            if price and price > MAX_PRICE:
                                continue

                            if rooms and rooms not in ROOMS:
                                continue

                            link = href if href.startswith("http") else base + href

                            if link in seen:
                                continue

                            seen.add(link)

                            send(name, link, price or "?", rooms or "?")

                        except:
                            continue

                time.sleep(5 + random.uniform(0,3))

            except Exception as e:
                print("ERROR:", e)
                time.sleep(10)

run()
