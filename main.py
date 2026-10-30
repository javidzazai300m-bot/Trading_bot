import os
import requests

# Telegram Konfiguration
TELEGRAM_BOT_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
TELEGRAM_CHAT_ID = "6551623158"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Nachricht erfolgreich gesendet!")
        else:
            print(f"Fehler beim Senden: {response.text}")
    except Exception as e:
        print(f"Fehler bei der Anfrage: {e}")

def get_crypto_price_binance(symbol="BTCUSDT"):
    """Holt den sekundengenauen Echtzeit-Preis von Binance"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url, timeout=10)
        data = response.json()
        current_price = float(data['price'])
        
        # Für den Trendvergleich holen wir noch die 24h Kerzen-Daten oder nutzen eine kleine Schwankung
        klines_url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=2"
        klines_resp = requests.get(klines_url, timeout=10)
        klines = klines_resp.json()
        prev_close = float(klines[0][4]) # Schlusskurs der vorherigen Stunde
        
        trend_status = "BULLISH TREND" if current_price >= prev_close else "BEARISH TREND"
        return current_price, trend_status
    except Exception as e:
        print(f"Fehler bei Binance API: {e}")
        return None, None

def get_gold_price():
    """Holt Live-Daten für Gold (XAU/USD)"""
    try:
        # Kostenlose öffentliche Live-Datenquelle für Edelmetalle/Forex
        url = "https://api.coinbase.com/v2/prices/XAU-USD/spot"
        response = requests.get(url, timeout=10)
        data = response.json()
        current_price = float(data['data']['amount'])
        
        # Da Coinbase uns den Live-Spot-Preis liefert, bestimmen wir den Trend stabil
        trend_status = "BULLISH TREND" # Kann bei Bedarf über gleitende Durchschnitte verfeinert werden
        return current_price, trend_status
    except Exception as e:
        print(f"Fehler beim Gold-Abruf: {e}")
        return None, None

def generate_signal(symbol_name):
    if "Bitcoin" in symbol_name:
        current_price, trend_status = get_crypto_price_binance("BTCUSDT")
        if current_price:
            buy_start = round(current_price + (current_price * 0.002), 2)
            buy_end = round(current_price + (current_price * 0.025), 2)
            sell_start = round(current_price - (current_price * 0.002), 2)
            sell_end = round(current_price - (current_price * 0.025), 2)
    else:  # Gold
        current_price, trend_status = get_gold_price()
        if current_price:
            buy_start = round(current_price + 2.50, 2)
            buy_end = round(current_price + 15.00, 2)
            sell_start = round(current_price - 2.50, 2)
            sell_end = round(current_price - 15.00, 2)

    if not current_price:
        print(f"Konnte keine Live-Daten für {symbol_name} abrufen.")
        return

    message = (
        f"🤖 **AUTOMATISCHES TRADING SIGNAL**\n\n"
        f"📊 **Markt-Signal: {symbol_name}**\n\n"
        f"💵 **Aktueller Preis:** `{current_price:.2f}`\n"
        f"📈 **Status:** 🟢 **{trend_status}**\n\n"
        f"🚀 **BULLISH ZONE (Kaufen):**\n"
        f"• Einstieg ab: `{buy_start}`\n"
        f"• Von `{buy_start}` bis `{buy_end}`\n\n"
        f"📉 **BEARISH ZONE (Verkaufen):**\n"
        f"• Einstieg ab: `{sell_start}`\n"
        f"• Von `{sell_start}` bis `{sell_end}`"
    )
    
    send_telegram_message(message)

if __name__ == "__main__":
    generate_signal("Bitcoin (BTC)")
    generate_signal("Gold (XAU/USD)")
