import os
import requests
import pandas as pd
import yfinance as yf

# ==========================================
# KONFIGURATION & ZUGANGSDATEN
# ==========================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc")
CHAT_ID = os.getenv("CHAT_ID", "6551623158")

SYMBOL = "GC=F"  # Gold Futures / XAUUSD auf yfinance
INTERVAL = "15m" # Chart-Zeitfenster (z.B. 15m, 1h, 1d)
PERIOD = "5d"   # Zeitraum für Datenabruf

# ==========================================
# INDIKATOR-BERECHNUNGEN
# ==========================================
def calculate_rsi(data, window=14):
    """ Berechnet den Relative Strength Index (RSI) """
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def send_telegram_message(message):
    """ Sendet eine Nachricht an Deinen Telegram-Bot """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Telegram-Nachricht erfolgreich gesendet!")
        else:
            print(f"❌ Fehler beim Senden: {response.text}")
    except Exception as e:
        print(f"❌ Fehler: {e}")

# ==========================================
# HAUPTPROGRAMM / TRADING LOGIK
# ==========================================
def run_bot():
    print("🔄 Lade Marktdaten für Gold...")
    df = yf.download(tickers=SYMBOL, period=PERIOD, interval=INTERVAL)

    if df.empty:
        print("❌ Keine Daten empfangen.")
        return

    # Gleitende Durchschnitte & RSI berechnen
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['RSI'] = calculate_rsi(df)

    # Aktuelle und vorherige Werte holen
    current_price = round(float(df['Close'].iloc[-1]), 2)
    rsi = round(float(df['RSI'].iloc[-1]), 2)
    
    sma_20_curr = float(df['SMA_20'].iloc[-1])
    sma_50_curr = float(df['SMA_50'].iloc[-1])
    sma_20_prev = float(df['SMA_20'].iloc[-2])
    sma_50_prev = float(df['SMA_50'].iloc[-2])

    signal = None

    # 🟢 BULLISH / BUY SIGNAL BEDINGUNGEN:
    if (sma_20_prev < sma_50_prev and sma_20_curr > sma_50_curr) or rsi < 35:
        signal = "BUY"
        action_text = "🟢 BUY (KAUFEN)"
        
        entry_min = round(current_price - 2.0, 2)
        entry_max = round(current_price + 2.0, 2)
        take_profit = round(current_price + 15.0, 2)
        stop_loss = round(current_price - 10.0, 2)

    # 🔴 BEARISH / SELL SIGNAL BEDINGUNGEN:
    elif (sma_20_prev > sma_50_prev and sma_20_curr < sma_50_curr) or rsi > 65:
        signal = "SELL"
        action_text = "🔴 SELL (VERKAUFEN)"
        
        entry_min = round(current_price - 2.0, 2)
        entry_max = round(current_price + 2.0, 2)
        take_profit = round(current_price - 15.0, 2)
        stop_loss = round(current_price + 10.0, 2)

    # Wenn ein Signal vorliegt -> Trading Signal senden
    if signal:
        msg = (
            f"🚨 *TRADING SIGNAL* 🚨\n\n"
            f"• *Asset:* Gold (XAU/USD)\n"
            f"• *Aktueller Kurs:* {current_price}\n"
            f"• *Aktion:* {action_text}\n\n"
            f"🎯 *Einstieg:* Ab {entry_min} bis {entry_max}\n"
            f"🎯 *Take-Profit (Ziel):* {take_profit}\n"
            f"🛡️ *Stop-Loss (Absicherung):* {stop_loss}\n\n"
            f"📊 *RSI:* {rsi}"
        )
        send_telegram_message(msg)
    else:
        # Neu: Sendet eine Info-Nachricht, wenn der Markt neutral ist
        status_msg = (
            f"ℹ️ *MARKT-UPDATE (NEUTRAL)*\n\n"
            f"• *Asset:* Gold (XAU/USD)\n"
            f"• *Aktueller Kurs:* {current_price}\n"
            f"• *Status:* Keines der Kriterien (BUY/SELL) erfüllt.\n"
            f"📊 *RSI:* {rsi}"
        )
        send_telegram_message(status_msg)

if __name__ == "__main__":
    run_bot()
