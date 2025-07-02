import cloudscraper
import random
import string
import base64
import time
import threading
import os
from queue import Queue

# === Config ===
THREADS = 50         # lowered to reduce request bursts
RETRY_LIMIT = 2
BATCH_SIZE = 100     # keeping it manageable

# === Random Generators ===
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

# === Registration Task ===
def register_task(ref_code, queue, scraper):
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
            "User-Agent": scraper.headers.get('User-Agent', ''),
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        for _ in range(RETRY_LIMIT):
            try:
                res = scraper.post("https://aetheris.company/api/reg", json=payload, headers=headers, timeout=15)
                if res.status_code == 200 and "token" in res.json():
                    print(f"✅ Registered: {email} | Password: {password}")
                    break
                else:
                    print(f"❌ Reg failed ({res.status_code}): {res.text[:200]}...")
            except Exception as e:
                print(f"❌ Exception: {e}")

        else:
            print(f"❌ Skipped: {email}")

# === Batch Runner ===
def run_batch(ref_code, scraper):
    queue = Queue()
    for _ in range(BATCH_SIZE):
        queue.put(None)

    threads = []
    for _ in range(THREADS):
        t = threading.Thread(target=register_task, args=(ref_code, queue, scraper))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

# === Main ===
if __name__ == "__main__":
    print("\n🌲 FOREST ARMY — Cloudscraper Referral Bot")
    try:
        with open("code.txt") as f:
            codes = [decode_ref(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ code.txt not found.")
        exit()

    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    )
    print("🔌 Proxy Mode: OFF")

    try:
        while True:
            for code in codes:
                print(f"\n🚀 New batch for referral code: {code}")
                run_batch(code, scraper)
                time.sleep(5)  # pause between batches
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
