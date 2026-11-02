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
    
    # Laden der Daten (nutze 5 Tage, um Lücken bei Wochenenden zu vermeiden)
    data = yf.download(SYMBOL, period="5d", interval=TIMEFRAME, progress=False)
    
    if data.empty or len(data) < EMA_PERIOD + 2:
        print(f"Nicht genügend Daten empfangen. Zeilen: {len(data)}")
        return

    # WICHTIG: Korbereinigung für yfinance MultiIndex Spalten
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]
    
    # Sicherstellen, dass 'Close' existiert
    if 'Close' not in data.columns:
        print(f"Fehler: Spalte 'Close' nicht gefunden. Vorhandene Spalten: {data.columns}")
        return

    # 12-EMA berechnen
    data['EMA'] = data['Close'].ewm(span=EMA_PERIOD, adjust=False).mean()
    
    # Wir nehmen die letzten beiden GESCHLOSSENEN Kerzen (-2 und -3) oder die aktuellen (-1 und -2)
    # Empfehlung für Crossover: Auf die letzte abgeschlossene Kerze (-2) prüfen, 
    # um Fehlsignale durch zuckende Live-Kurse (-1) zu vermeiden.
    prev_close = float(data['Close'].iloc[-2])
    prev_ema = float(data['EMA'].iloc[-2])
    current_close = float(data['Close'].iloc[-3])
    current_ema = float(data['EMA'].iloc[-3])

    print(f"Letzte geschlossene Kerze - Close: {prev_close:.2f} | EMA(12): {prev_ema:.2f}")

    # Signallogik (Crossover auf Basis der letzten geschlossenen Kerze)
    # Wenn vorher unter dem EMA und jetzt darüber -> BUY
    # (Hinweis: Bei umgekehrter Indexierung von -3 zu -2 vergleicht man den Übergang)
    
    # Sauberer Vergleich mit -2 (aktuell) und -3 (vorheriger Tick)
    c_close = float(data['Close'].iloc[-1])
    c_ema = float(data['EMA'].iloc[-1])
    p_close = float(data['Close'].iloc[-2])
    p_ema = float(data['EMA'].iloc[-2])

    print(f"Aktueller Kurs: {c_close:.2f} | EMA: {c_ema:.2f}")
    print(f"Vorheriger Kurs: {p_close:.2f} | EMA: {p_ema:.2f}")

    if p_close <= p_ema and c_close > c_ema:
        sl = c_close * (1 - SL_PERCENT)
        tp = c_close * (1 + TP_PERCENT)
        
        msg = (
            f"🟢 **GOLD (XAUUSD) KAUFSIGNAL (BUY)**\n\n"
            f"⏱ **Zeitrahmen:** M15\n"
            f"💰 **Einstieg / Kurs:** `{c_close:.2f} $`\n"
            f"🛑 **Stop-Loss (SL):** `{sl:.2f} $`\n"
            f"🎯 **Take-Profit (TP):** `{tp:.2f} $`\n"
            f"📊 **EMA(12):** `{c_ema:.2f} $`"
        )
        send_telegram_message(msg)
        
    elif p_close >= p_ema and c_close < c_ema:
        sl = c_close * (1 + SL_PERCENT)
        tp = c_close * (1 - TP_PERCENT)
        
        msg = (
            f"🔴 **GOLD (XAUUSD) VERKAUFSIGNAL (SELL)**\n\n"
            f"⏱ **Zeitrahmen:** M15\n"
            f"💰 **Einstieg / Kurs:** `{c_close:.2f} $`\n"
            f"🛑 **Stop-Loss (SL):** `{sl:.2f} $`\n"
            f"🎯 **Take-Profit (TP):** `{tp:.2f} $`\n"
            f"📊 **EMA(12):** `{c_ema:.2f} $`"
        )
        send_telegram_message(msg)
    else:
        print("Kein neues Signal im M15-Zeitrahmen.")

if __name__ == "__main__":
    check_gold_signal()
