import os
import requests
import pandas as pd
import yfinance as yf

# ==========================================
# KONFIGURATION & ZUGANGSDATEN
# ==========================================
# Am sichersten über Umgebungsvariablen (GitHub Secrets) einbinden:
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "DEIN_TELEGRAM_TOKEN_HIER")
CHAT_ID = os.getenv("CHAT_ID", "6551623158")  # Deine Telegram ID aus dem Screenshot

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
    # 1. SMA 20 kreuzt SMA 50 nach oben ODER
    # 2. RSI ist überverkauft (z.B. unter 35)
    if (sma_20_prev < sma_50_prev and sma_20_curr > sma_50_curr) or rsi < 35:
        signal = "BUY"
        action_text = "🟢 BUY (KAUFEN)"
        
        # Einstiegszone, TP und SL berechnen
        entry_min = round(current_price - 2.0, 2)
        entry_max = round(current_price + 2.0, 2)
        take_profit = round(current_price + 15.0, 2)  # Ziel nach oben
        stop_loss = round(current_price - 10.0, 2)   # Absicherung nach unten

    # 🔴 BEARISH / SELL SIGNAL BEDINGUNGEN:
    # 1. SMA 20 kreuzt SMA 50 nach unten ODER
    # 2. RSI ist überkauft (z.B. über 65)
    elif (sma_20_prev > sma_50_prev and sma_20_curr < sma_50_curr) or rsi > 65:
        signal = "SELL"
        action_text = "🔴 SELL (VERKAUFEN)"
        
        # Einstiegszone, TP und SL berechnen
        entry_min = round(current_price - 2.0, 2)
        entry_max = round(current_price + 2.0, 2)
        take_profit = round(current_price - 15.0, 2)  # Ziel nach unten
        stop_loss = round(current_price + 10.0, 2)   # Absicherung nach oben

    # Wenn ein Signal generiert wurde -> Telegram-Nachricht aufbauen
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
        print(f"Kein klares Signal aktuell. Kurs: {current_price}, RSI: {rsi}")

if __name__ == "__main__":
    run_bot()
