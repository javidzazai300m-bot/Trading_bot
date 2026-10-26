import os
import time
import requests
import yfinance as yf

# --- KONFIGURATION ---
TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
# Deine Chat-ID aus dem Screenshot (@Zabaritradingbot / idbot: 655163158)
CHAT_ID = "655163158"  
SYMBOL = "GC=F"  # Gold (XAU/USD über Yahoo Finance)

# Intervalle & Schwellenwerte
CHECK_INTERVAL_SECONDS = 60  # Prüft jede Minute
RSI_PERIOD = 14

last_signal_type = None  # Verhindert Spam, wenn das Signal aktiv bleibt

def get_market_data():
    """Lädt aktuelle Kursdaten und berechnet den RSI."""
    try:
        ticker = yf.Ticker(SYMBOL)
        df = ticker.history(period="1d", interval="1m")
        if df.empty or len(df) < RSI_PERIOD + 2:
            return None, None
        
        current_price = df['Close'].iloc[-1]
        
        # Einfache RSI-Berechnung
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
        return response.json()
    except Exception as e:
        print(f"Fehler beim Senden an Telegram: {e}")
        return None

def run_bot():
    global last_signal_type
    print("Trading-Bot gestartet und überwacht den Markt...")
    
    while True:
        price, rsi = get_market_data()
        
        if price and rsi:
            print(f"[{time.strftime('%H:%M:%S')}] Aktueller Kurs: {price:.2f} | RSI: {rsi:.1f}")
            
            # --- LOGIK FÜR KLARE SIGNALE ---
            
            # Beispiel-Bedingung für SELL (Markt bricht nach unten aus oder RSI im überkauften Bereich)
            if rsi >= 70 and last_signal_type != "SELL":
                entry_low = round(price - 2.0, 2)
                entry_high = round(price + 2.0, 2)
                tp = round(price - 15.0, 2)
                sl = round(price + 10.0, 2)
                
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
                last_signal_type = "SELL"
                
            # Beispiel-Bedingung für BUY (Markt zieht nach oben oder RSI im überverkauften Bereich)
            elif rsi <= 30 and last_signal_type != "BUY":
                entry_low = round(price - 2.0, 2)
                entry_high = round(price + 2.0, 2)
                tp = round(price + 15.0, 2)
                sl = round(price - 10.0, 2)
                
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
                last_signal_type = "BUY"
                
            # Reset des Status, wenn sich der Markt beruhigt (RSI normalisiert sich)
            elif 45 < rsi < 55:
                last_signal_type = None
                
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    run_bot()
