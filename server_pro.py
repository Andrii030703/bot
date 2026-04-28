import time, requests, re, json, os
from playwright.sync_api import sync_playwright

TOKEN = os.getenv("TOKEN")
CHAT_IDS = os.getenv("CHAT_IDS").split(",")

URLS = [
    ("https://www.saga.hamburg/immobiliensuche", "https://www.saga.hamburg"),
    ("https://www.immobilienscout24.de/Suche/de/hamburg/hamburg/wohnung-mieten", "https://www.immobilienscout24.de"),
]

CHECK_INTERVAL = 12
MAX_PRICE = 950
ROOMS = ["2", "2.5", "3", "3.5", "4"]

SEEN_FILE = "seen.json"

# ===== ЗБЕРЕЖЕННЯ =====
if os.path.exists(SEEN_FILE):
    seen = set(json.load(open(SEEN_FILE)))
else:
    seen = set()

def save_seen():
    json.dump(list(seen), open(SEEN_FILE, "w"))

# ===== TELEGRAM =====
def send(title, link, price, rooms):
    for chat_id in CHAT_IDS:
        try:
            text = f"🏠 НОВА КВАРТИРА\n\n💶 {price}€\n🛏 {rooms} кімнати\n\n{link}"

            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
                "chat_id": chat_id,
                "text": text,
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": "🔎 ВІДКРИТИ", "url": link}]
                    ]
                }
            })
        except:
            pass

# ===== ПАРСИНГ =====
def parse_price(text):
    m = re.search(r"(\d{2,4})\s?€", text)
    return int(m.group(1)) if m else None

def parse_rooms(text):
    m = re.search(r"(\d+(?:[.,]\d+)?)\s?-?\s?Zimmer", text)
    return m.group(1).replace(",", ".") if m else None

# ===== РОЗУМНИЙ ФІЛЬТР =====
def is_good(text):
    text = text.lower()

    good = ["saga", "genossenschaft", "wohnungsbau", "öffentlich"]
    bad = ["gmbh", "makler", "immobilien", "agentur"]

    score = 0

    for g in good:
        if g in text:
            score += 2

    for b in bad:
        if b in text:
            score -= 2

    return score >= 2

def match(text):
    if not is_good(text):
        return False

    price = parse_price(text)
    rooms = parse_rooms(text)

    if price and price > MAX_PRICE:
        return False

    if rooms and rooms not in ROOMS:
        return False

    return True

# ===== ОСНОВА =====
def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🚀 PRO BOT STARTED")

        while True:
            try:
                for url, base in URLS:
                    page.goto(url)
                    page.wait_for_timeout(2500)

                    cards = page.locator("a").all()

                    for c in cards:
                        try:
                            href = c.get_attribute("href")
                            text = c.inner_text()

                            if not href or not text:
                                continue

                            link = href if href.startswith("http") else base + href

                            if link in seen:
                                continue

                            if not match(text):
                                continue

                            price = parse_price(text) or "?"
                            rooms = parse_rooms(text) or "?"

                            seen.add(link)
                            save_seen()

                            print("🔥", link)
                            send("flat", link, price, rooms)

                        except:
                            continue

                time.sleep(CHECK_INTERVAL)

            except Exception as e:
                print("ERROR:", e)
                time.sleep(10)

run()
