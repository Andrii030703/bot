import time, requests, re, os, random, json
from playwright.sync_api import sync_playwright

TOKEN = os.getenv("TOKEN")
CHAT_IDS = os.getenv("CHAT_IDS").split(",")

SAGA_URL = "https://www.saga.hamburg/immobiliensuche"
BASE = "https://www.saga.hamburg"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118 Safari/537.36"
]

seen = set()

# 📲 TELEGRAM
def send(link):
    for chat_id in CHAT_IDS:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
            "chat_id": chat_id,
            "text": f"🔥 НОВА КВАРТИРА\n\n{link}",
            "reply_markup": {
                "inline_keyboard": [
                    [{"text": "⚡ ВІДКРИТИ", "url": link}]
                ]
            }
        })

# 🧠 затримка як людина
def human_delay(a=1, b=3):
    time.sleep(random.uniform(a, b))

# 🔁 retry
def safe_goto(page, url):
    for i in range(5):
        try:
            page.goto(url, timeout=40000)
            human_delay()
            return True
        except Exception as e:
            print("Retry:", e)
            time.sleep(3 + i)
    return False

# 💾 cookies
def load_cookies(context):
    try:
        with open("cookies.json", "r") as f:
            context.add_cookies(json.load(f))
            print("Cookies loaded")
    except:
        print("No cookies yet")

def save_cookies(context):
    try:
        cookies = context.cookies()
        with open("cookies.json", "w") as f:
            json.dump(cookies, f)
    except:
        pass

# 🎯 поведінка
def human_behavior(page):
    try:
        page.mouse.move(random.randint(100, 400), random.randint(100, 400))
        human_delay()

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        human_delay()

        page.evaluate("window.scrollTo(0, 0)")
        human_delay()
    except:
        pass

# 🚀 MAIN
def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage"
            ]
        )

        context = browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 800},
            locale="de-DE",
            timezone_id="Europe/Berlin"
        )

        # ❗ антидетект
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        load_cookies(context)

        page = context.new_page()

        print("🔥 ANTIBAN PRO BOT STARTED")

        while True:
            try:
                ok = safe_goto(page, SAGA_URL)

                if not ok:
                    print("❌ BLOCKED - retry later")
                    time.sleep(20)
                    continue

                human_behavior(page)

                links = page.locator("a").all()
                print("Links:", len(links))

                for a in links:
                    try:
                        href = a.get_attribute("href")

                        if not href:
                            continue

                        if "wohnung" not in href.lower():
                            continue

                        link = href if href.startswith("http") else BASE + href

                        if link in seen:
                            continue

                        seen.add(link)

                        print("FOUND:", link)
                        send(link)

                    except:
                        continue

                save_cookies(context)

                # ⏱ швидкість + randomness
                time.sleep(random.uniform(3, 7))

            except Exception as e:
                print("ERROR:", e)
                time.sleep(10)
run()
