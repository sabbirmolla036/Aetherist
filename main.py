import cloudscraper
import random
import string
import base64
import time
import threading
from queue import Queue

THREADS = 10
RETRY_LIMIT = 2
BATCH_SIZE = 10

def random_string(min_len=3, max_len=8):
    return ''.join(random.choices(string.ascii_lowercase, k=random.randint(min_len, max_len))).capitalize()

def random_name():
    return random_string(), random_string()

def random_email():
    first, last = random_name()
    number = random.randint(10, 99)
    return f"{first.lower()}.{last.lower()}{number}@gmail.com"

def random_password(min_len=8, max_len=12):
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choices(chars, k=random.randint(min_len, max_len)))

def decode_ref(b64):
    try:
        return base64.b64decode(b64).decode().strip()
    except:
        return None

def load_proxies():
    try:
        with open("proxies.txt") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ proxies.txt not found.")
        return []

def create_scraper(proxy=None):
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    )
    if proxy:
        scraper.proxies = {
            "http": proxy,
            "https": proxy
        }
    return scraper

def register_task(ref_code, queue, proxy=None):
    scraper = create_scraper(proxy)
    while True:
        try:
            _ = queue.get_nowait()
        except:
            return

        ref_url = f"https://aetheris.company/register?ref={ref_code}"
        try:
            scraper.get(ref_url, timeout=15)
        except Exception as e:
            print(f"❌ Failed to load referral page: {e}")
            continue

        first, last = random_name()
        email = random_email()
        password = random_password()

        payload = {
            "email": email,
            "first": first,
            "last": last,
            "password": password,
            "password2": password,
            "ref": ref_code
        }

        headers = {
            "Origin": "https://aetheris.company",
            "Referer": ref_url,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        }

        for _ in range(RETRY_LIMIT):
            try:
                res = scraper.post("https://aetheris.company/api/reg", json=payload, headers=headers, timeout=15)
                if res.status_code == 200 and "token" in res.text:
                    print(f"✅ Registered: {email} | Password: {password}")
                    break
                else:
                    print(f"❌ Reg failed ({res.status_code}): {res.text[:200]}...")
            except Exception as e:
                print(f"❌ Exception: {e}")

        else:
            print(f"❌ Skipped: {email}")

def run_batch(ref_code, proxies=None):
    queue = Queue()
    for _ in range(BATCH_SIZE):
        queue.put(None)

    threads = []
    for _ in range(THREADS):
        proxy = random.choice(proxies) if proxies else None
        t = threading.Thread(target=register_task, args=(ref_code, queue, proxy))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

if __name__ == "__main__":
    print("\n🌲 FOREST ARMY — Cloudscraper Referral Bot")
    try:
        with open("code.txt") as f:
            codes = [decode_ref(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ code.txt not found.")
        exit()

    print("\nChoose mode:")
    print("1. Run with proxy")
    print("2. Run without proxy")
    mode = input("Enter 1 or 2: ").strip()

    if mode == "1":
        proxies = load_proxies()
        if not proxies:
            print("❌ No proxies loaded. Exiting.")
            exit()
        print("🔌 Proxy Mode: ON")
    else:
        proxies = None
        print("🔌 Proxy Mode: OFF")

    try:
        while True:
            for code in codes:
                print(f"\n🚀 New batch for referral code: {code}")
                run_batch(code, proxies)
                time.sleep(5)
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
