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

def fetch_prices():
    headers = {
        "authorization": f"apikey {API_KEY}",
        "content-type": "application/json"
    }
    response = requests.get(URL, headers=headers)
    data = response.json()
    prices = {}
    for item in data.get("result", []):
        marka = item.get("marka")
        benzin = item.get("benzin")
        try:
            fiyat = float(benzin)
            prices[marka] = fiyat
        except (TypeError, ValueError):
            continue
    return prices

def load_last_prices():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_prices(prices):
    with open(STATE_FILE, "w") as f:
        json.dump(prices, f)

def format_change(current, previous):
    if previous is None:
        return "(ilk veri) 🟡"

    change = current - previous
    percent = (change / previous) * 100
    symbol = "🟢" if change > 0 else "🔴" if change < 0 else "🟡"
    color = "green" if change > 0 else "red" if change < 0 else "orange"
    tag = f"<font color='{color}'>({percent:.2f}% değişim)</font>"

    important = ""
    if abs(percent) >= 1:
        important = "<b>‼️ ÖNEMLİ DEĞİŞİM (>%1) ‼️</b>\n"

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
    current_prices = fetch_prices()
    previous_prices = load_last_prices()
    save_prices(current_prices)

    if not current_prices:
        send_telegram_message("⚠️ Sarıyer için geçerli benzin fiyatı bulunamadı.")
        return

    message_lines = ["⛽ <b>Sarıyer Benzin Fiyatları</b>"]
    for marka, fiyat in current_prices.items():
        previous = previous_prices.get(marka)
        change_text = format_change(fiyat, previous)
        line = f"<b>{marka}</b>: {fiyat:.2f}₺ {change_text}"
        message_lines.append(line)

    message = "\n".join(message_lines)
    send_telegram_message(message)

if __name__ == "__main__":
    main()
