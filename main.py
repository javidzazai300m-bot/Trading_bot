import os
import requests
import datetime
import yfinance as yf

# Telegram Zugangsdaten
BOT_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
CHAT_ID = "6551623158"

# Telegram Nachrichten-Funktion
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
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
        print(f"Fehler: {e}")

# Marktanalyse für Trading-Session
def analyze_market(symbol="GC=F"):  # GC=F steht für Gold-Futures (XAU/USD)
    try:
        # Daten abrufen
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d", interval="15m")

        if df.empty:
            return "Keine Marktdaten verfügbar."

        # Letzter Schlusskurs und 50er EMA berechnen
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        last_close = df['Close'].iloc[-1]
        last_ema = df['EMA50'].iloc[-1]

        # Bestimme Trend/Richtung
        if last_close > last_ema:
            bias = "🟢 **BULLISH (LONG)**"
            detail = "Der Kurs liegt über dem EMA 50. Halte nach Buy-Setups Ausschau!"
        else:
            bias = "🔴 **BEARISH (SHORT)**"
            detail = "Der Kurs liegt unter dem EMA 50. Halte nach Sell-Setups Ausschau!"

        # Aktuelle Zeit bestimmen
        now_str = datetime.datetime.now().strftime("%H:%M Uhr (UTC/CET)")

        # Nachricht erstellen
        message = (
            f"⏰ **TRADING SESSION ALERT** ({now_str})\n"
            f"📊 **Asset:** Gold (XAU/USD)\n\n"
            f"🎯 **Markttrend / Direction:** {bias}\n"
            f"💵 **Aktueller Kurs:** `{last_close:.2f}`\n\n"
            f"💡 **Analyse:**\n{detail}"
        )
        return message

    except Exception as e:
        return f"Fehler bei der Analyse: {e}"

if __name__ == "__main__":
    signal_text = analyze_market("GC=F")
    send_telegram_message(signal_text)
