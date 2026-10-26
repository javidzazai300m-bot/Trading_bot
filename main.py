import os
import requests
import yfinance as yf

# --- KONFIGURATION ---
TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
CHAT_ID = "6551623158"
SYMBOL = "GC=F"  # Gold (XAU/USD über Yahoo Finance)
RSI_PERIOD = 14

def get_market_data():
    """Lädt aktuelle Kursdaten und berechnet den RSI."""
    try:
        ticker = yf.Ticker(SYMBOL)
        df = ticker.history(period="1d", interval="1m")
        if df.empty or len(df) < RSI_PERIOD + 2:
            return None, None
        
        current_price = df['Close'].iloc[-1]
        
        # RSI Berechnung
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=RSI_PERIOD).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_PERIOD).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        return float(current_price), float(current_rsi)
    except Exception as e:
        print(f"Fehler beim Abrufen der Marktdaten: {e}")
        return None, None

def send_telegram_message(message):
    """Sendet die Nachricht direkt an deinen Telegram-Bot."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        print("Telegram Antwort:", response.text)
        return response.json()
    except Exception as e:
        print(f"Fehler beim Senden an Telegram: {e}")
        return None

def main():
    price, rsi = get_market_data()
    
    if price is None or rsi is None:
        print("Konnte keine gültigen Marktdaten abrufen.")
        return

    print(f"Aktueller Kurs: {price:.2f} | RSI: {rsi:.1f}")

    # --- BEISPIEL-LOGIK FÜR SIGNALE ---
    # SELL Signal bei RSI über 65
    if rsi >= 65:
        entry_low = round(price - 1.0, 2)
        entry_high = round(price + 1.0, 2)
        tp = round(price - 10.0, 2)
        sl = round(price + 8.0, 2)
        
        message = (
            f"🚨 *TRADING SIGNAL* 🚨\n\n"
            f"• Asset: Gold (XAU/USD)\n"
            f"• Aktueller Kurs: {price:.2f}\n"
            f"• Aktion: 🔴 *SELL (VERKAUFEN)*\n\n"
            f"🎯 *Einstieg:* Ab {entry_low} bis {entry_high}\n"
            f"🎯 *Take-Profit (Ziel):* {tp}\n"
            f"🛡 *Stop-Loss (Absicherung):* {sl}\n\n"
            f"📊 *RSI:* {rsi:.1f}"
        )
        send_telegram_message(message)

    # BUY Signal bei RSI unter 35
    elif rsi <= 35:
        entry_low = round(price - 1.0, 2)
        entry_high = round(price + 1.0, 2)
        tp = round(price + 10.0, 2)
        sl = round(price - 8.0, 2)
        
        message = (
            f"🚨 *TRADING SIGNAL* 🚨\n\n"
            f"• Asset: Gold (XAU/USD)\n"
            f"• Aktueller Kurs: {price:.2f}\n"
            f"• Aktion: 🟢 *BUY (KAUFEN)*\n\n"
            f"🎯 *Einstieg:* Ab {entry_low} bis {entry_high}\n"
            f"🎯 *Take-Profit (Ziel):* {tp}\n"
            f"🛡 *Stop-Loss (Absicherung):* {sl}\n\n"
            f"📊 *RSI:* {rsi:.1f}"
        )
        send_telegram_message(message)
    else:
        print("Kein Kriterium für ein Signal erfüllt (Markt im neutralen Bereich).")

if __name__ == "__main__":
    main()
