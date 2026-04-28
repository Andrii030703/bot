import time, requests, re
from playwright.sync_api import sync_playwright

# ===== НАЛАШТУВАННЯ =====
TOKEN = "8548267283:AAEFAN5LxgjkLcUltKPpfQ85M_2REZ6NsEU"
CHAT_IDS = ["8002075187", "7813659703"]

URLS = [
    ("https://www.saga.hamburg/immobiliensuche", "https://www.saga.hamburg"),
    ("https://www.immobilienscout24.de/Suche/de/hamburg/hamburg/wohnung-mieten", "https://www.immobilienscout24.de"),
    ("https://www.wg-gesucht.de/wohnungen-in-Hamburg.55.2.1.0.html", "https://www.wg-gesucht.de")
]

CHECK_INTERVAL = 10
MAX_PRICE = 950
ROOMS = ["2", "2.5", "3", "3.5", "4"]

# ===== РОЗУМНИЙ ФІЛЬТР =====
GOOD_COMPANIES = [
    "saga", "saga gwg",
    "bauverein der elbgemeinden",
    "bve",
    "hansa baugenossenschaft",
    "schiffszimmerer",
    "fluwog",
    "barmbek baugenossenschaft",
    "süderelbe"
]

GOOD_WORDS = [
    "genossenschaft",
    "wohnungsbaugenossenschaft",
    "städtisch",
    "öffentlich"
]

BAD_WORDS = [
    "gmbh",
    "immobilien",
    "makler",
    "agentur",
    "vertrieb",
    "consulting",
    "holding",
    "courtage",
    "provision"
]

seen = set()

# ===== TELEGRAM =====
def send(link):
    for chat_id in CHAT_IDS:
        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={
                "chat_id": chat_id,
                "text": f"🚨🔥 КВАРТИРА!\n{link}"
            })

            # другий сигнал
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={
                "chat_id": chat_id,
                "text": "🔔 ТЕРМІНОВО ПЕРЕВІР!"
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

# ===== AI-ФІЛЬТР =====
def score_listing(text, link):
    text = text.lower()
    score = 0

    # сильні плюси
    for name in GOOD_COMPANIES:
        if name in text:
            score += 5

    for word in GOOD_WORDS:
        if word in text:
            score += 3

    # мінуси
    for bad in BAD_WORDS:
        if bad in text:
            score -= 4

    # контекст
    if "immomio" in text or "immomio" in link:
        score += 4

    if "saga" in text:
        score += 5

    if "genossenschaft" in text:
        score += 3

    return score

def match(text, link):
    score = score_listing(text, link)

    if score < 4:
        return False

    price = parse_price(text)
    rooms = parse_rooms(text)

    if price and price > MAX_PRICE:
        return False

    if rooms and rooms not in ROOMS:
        return False

    print("AI SCORE:", score, "|", link)
    return True

# ===== ОСНОВА =====
def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🚀 FINAL BOT STARTED")

        while True:
            try:
                for url, base in URLS:
                    page.goto(url)
                    page.wait_for_timeout(3000)

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

                            if not match(text, link):
                                continue

                            seen.add(link)

                            print("🔥 FOUND:", link)
                            send(link)

                        except:
                            continue

                time.sleep(CHECK_INTERVAL)

            except Exception as e:
                print("❌ ERROR:", e)
                time.sleep(20)

run()