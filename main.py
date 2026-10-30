import os
import requests
import yfinance as yf

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
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Nachricht erfolgreich gesendet!")
    else:
        print(f"Fehler beim Senden: {response.text}")

def get_market_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="5d", interval="1d")
        if df.empty:
            return None
        current_price = float(df['Close'].iloc[-1])
        prev_close = float(df['Close'].iloc[-2])
        
        # Trendbestimmung (einfach basierend auf Vortagesvergleich oder Indikatoren)
        trend_status = "BULLISH TREND" if current_price >= prev_close else "BEARISH TREND"
        return current_price, trend_status
    except Exception as e:
        print(f"Fehler beim Abrufen der Daten für {ticker_symbol}: {e}")
        return None, None

def generate_signal(symbol_name, ticker_symbol):
    current_price, trend_status = get_market_data(ticker_symbol)
    if current_price is None:
        print(f"Konnte keine Daten für {symbol_name} abrufen.")
        return

    # Dynamische Zonen-Berechnung (Beispiel-Puffer basierend auf Preis)
    buffer = current_price * 0.003  # 0.3% Puffer
    
    if "Bitcoin" in symbol_name:
        buy_start = round(current_price + (current_price * 0.002), 2)
        buy_end = round(current_price + (current_price * 0.025), 2)
        sell_start = round(current_price - (current_price * 0.002), 2)
        sell_end = round(current_price - (current_price * 0.025), 2)
    else:  # Gold
        buy_start = round(current_price + 2.50, 2)
        buy_end = round(current_price + 15.00, 2)
        sell_start = round(current_price - 2.50, 2)
        sell_end = round(current_price - 15.00, 2)

    # Nachricht im exakten Format erstellen
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
    # Signale für Bitcoin und Gold ausführen
    generate_signal("Bitcoin (BTC)", "BTC-USD")
    generate_signal("Gold (XAU/USD)", "GC=F")
