import requests
import json
import os

API_KEY = os.getenv("COLLECTAPI_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

CITY = "istanbul"
DISTRICT = "sariyer"
URL = f"https://api.collectapi.com/gasPrice/turkeyGasoline?city={CITY}&district={DISTRICT}"
STATE_FILE = "state.json"

def fetch_price():
    headers = {
        "authorization": f"apikey {API_KEY}",
        "content-type": "application/json"
    }
    response = requests.get(URL, headers=headers)
    data = response.json()
    for item in data["result"]:
        if item["marka"].lower() == "shell":
            return float(item["benzin"])
    return None

def load_last_price():
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return None
            return json.loads(content).get("last_price")
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def save_price(price):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_price": price}, f)

def format_change(current, previous):
    if previous is None:
        return "(ilk veri) 🟡"

    change = current - previous
    percent = (change / previous) * 100
    symbol = "🟢" if change > 0 else "🔴" if change < 0 else "🟡"
    color = "green" if change > 0 else "red" if change < 0 else "orange"
    tag = f"<b><font color='{color}'>({percent:.2f}% değişim)</font></b>"

    important = ""
    if abs(percent) >= 5:
        important = "<b>‼️ ÖNEMLİ DEĞİŞİM ‼️</b>\n"

    return f"{important}{symbol} {tag}"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def main():
    current_price = fetch_price()
    previous_price = load_last_price()
    save_price(current_price)

    change_text = format_change(current_price, previous_price)
    message = f"⛽ Sarıyer Shell Benzin Fiyatı: <b>{current_price:.2f}₺</b>\n{change_text}"
    send_telegram_message(message)

if __name__ == "__main__":
    main()
