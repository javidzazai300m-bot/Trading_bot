import os
import sys
import requests
import pandas as pd
import yfinance as yf

# --- Konfiguration ---
SYMBOL = "GC=F"       # Gold-Futures (XAUUSD)
TIMEFRAME = "15m"     # M15 Zeitrahmen
EMA_PERIOD = 12       # EMA Periode

# Feste Zugangsdaten (Bot-Token & deine Telegram-ID)
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
TELEGRAM_CHAT_ID = "6551623158"

# Risikomanagement: Abstände für Stop-Loss (0.2%) und Take-Profit (0.45%)
SL_PERCENT = 0.002
TP_PERCENT = 0.0045

def send_telegram_message(message):
    """Sendet eine formatierte Nachricht an deinen Telegram-Bot."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("Telegram-Signal erfolgreich gesendet!")
        else:
            print(f"Fehler beim Telegram-Versand: {response.text}")
    except Exception as e:
        print(f"Netzwerkfehler bei Telegram: {e}")

def check_gold_signal():
    print(f"Starte Marktanalyse für {SYMBOL} auf Zeitrahmen {TIMEFRAME}...")
    
    try:
        # Marktdaten laden (5 Tage, um Wochenenden sicher zu überbrücken)
        data = yf.download(SYMBOL, period="5d", interval=TIMEFRAME, progress=False)
    except Exception as e:
        print(f"Fehler beim Herunterladen der Daten von yfinance: {e}")
        return

    # Prüfen, ob genügend Daten vorhanden sind
    if data.empty or len(data) < EMA_PERIOD + 5:
        print(f"Warnung: Zu wenige Kerzen empfangen ({len(data)} Zeilen).")
        return

    # Bereinigung von yfinance MultiIndex-Spalten (falls vorhanden)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]
    
    if 'Close' not in data.columns:
        print(f"Kritischer Fehler: Spalte 'Close' fehlt in den Daten. Vorhanden: {data.columns}")
        return

    # 12er Exponential Moving Average (EMA) berechnen
    data['EMA'] = data['Close'].ewm(span=EMA_PERIOD, adjust=False).mean()
    
    # Werte der letzten abgeschlossenen Kerzen holen (-2 und -3 zur Vermeidung von Live-Rauschen)
    c_close = float(data['Close'].iloc[-2])
    c_ema = float(data['EMA'].iloc[-2])
    p_close = float(data['Close'].iloc[-3])
    p_ema = float(data['EMA'].iloc[-3])

    print(f"Kerze [-2] - Kurs: {c_close:.2f} | EMA: {c_ema:.2f}")
    print(f"Kerze [-3] - Kurs: {p_close:.2f} | EMA: {p_ema:.2f}")

    # Signallogik: Crossover-Erkennung
    # KAUFSIGNAL: Vorher unter dem EMA, jetzt darüber
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
        
    # VERKAUFSIGNAL: Vorher über dem EMA, jetzt darunter
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
        print("Kein Crossover-Signal im aktuellen Intervall. Bot bleibt stumm.")

if __name__ == "__main__":
    check_gold_signal()
