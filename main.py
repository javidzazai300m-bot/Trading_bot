import os
import requests
import pandas as pd
import yfinance as yf

# --- Konfiguration ---
SYMBOL = "GC=F"   # Gold-Futures (XAUUSD)
TIMEFRAME = "15m" # M15 Zeitrahmen
EMA_PERIOD = 12

# Feste Zugangsdaten
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
TELEGRAM_CHAT_ID = "6551623158"

# Prozentuale Abstände für SL (0.2%) und TP (0.45%)
SL_PERCENT = 0.002
TP_PERCENT = 0.0045

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Telegram-Signal erfolgreich gesendet!")
        else:
            print(f"Fehler beim Senden: {response.text}")
    except Exception as e:
        print(f"Netzwerkfehler: {e}")

def check_gold_signal():
    print("Prüfe Gold (XAUUSD) auf M15...")
    data = yf.download(SYMBOL, period="2d", interval=TIMEFRAME, progress=False)
    
    if data.empty or len(data) < EMA_PERIOD + 2:
        print("Nicht genügend Daten empfangen.")
        return

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # 12-EMA berechnen
    data['EMA'] = data['Close'].ewm(span=EMA_PERIOD, adjust=False).mean()
    
    current_close = float(data['Close'].iloc[-1])
    current_ema = float(data['EMA'].iloc[-1])
    prev_close = float(data['Close'].iloc[-2])
    prev_ema = float(data['EMA'].iloc[-2])

    print(f"Aktueller Kurs: {current_close:.2f} | EMA(12): {current_ema:.2f}")

    # Signallogik (Crossover)
    if prev_close <= prev_ema and current_close > current_ema:
        # BUY: SL liegt darunter, TP darüber
        sl = current_close * (1 - SL_PERCENT)
        tp = current_close * (1 + TP_PERCENT)
        
        msg = (
            f"🟢 **GOLD (XAUUSD) KAUFSIGNAL (BUY)**\n\n"
            f"⏱ **Zeitrahmen:** M15\n"
            f"💰 **Einstieg / Kurs:** `{current_close:.2f} $`\n"
            f"🛑 **Stop-Loss (SL):** `{sl:.2f} $`\n"
            f"🎯 **Take-Profit (TP):** `{tp:.2f} $`\n"
            f"📊 **EMA(12):** `{current_ema:.2f} $`"
        )
        send_telegram_message(msg)
        
    elif prev_close >= prev_ema and current_close < current_ema:
        # SELL: SL liegt darüber, TP darunter
        sl = current_close * (1 + SL_PERCENT)
        tp = current_close * (1 - TP_PERCENT)
        
        msg = (
            f"🔴 **GOLD (XAUUSD) VERKAUFSIGNAL (SELL)**\n\n"
            f"⏱ **Zeitrahmen:** M15\n"
            f"💰 **Einstieg / Kurs:** `{current_close:.2f} $`\n"
            f"🛑 **Stop-Loss (SL):** `{sl:.2f} $`\n"
            f"🎯 **Take-Profit (TP):** `{tp:.2f} $`\n"
            f"📊 **EMA(12):** `{current_ema:.2f} $`"
        )
        send_telegram_message(msg)
    else:
        print("Kein neues Signal im M15-Zeitrahmen.")

if __name__ == "__main__":
    check_gold_signal()
