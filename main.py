import time
import requests
import pandas as pd
import yfinance as yf

# --- DEINE DATEN ---
SYMBOL = "GC=F"          # Gold Futures (XAUUSD-Äquivalent)
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
TELEGRAM_CHAT_ID = "6551623158"

def send_telegram_message(message):
    """Sendet die Signal-Nachricht direkt an deinen Telegram-Chat"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Telegram-Nachricht erfolgreich gesendet!")
        else:
            print(f"Fehler beim Senden: {response.text}")
    except Exception as e:
        print(f"Verbindungsfehler: {e}")

def check_trading_signals():
    """Analysiert den Markt nach Bull- und Bear-Flags inkl. Entry, SL und TP"""
    print(f"Analysiere Markt für {SYMBOL} (Buy & Sell)...")
    
    # 1. Kursdaten laden (Stunden-Kerzen der letzten 5 Tage)
    df = yf.download(SYMBOL, period="5d", interval="1h", progress=False)
    if df.empty:
        print("Keine Daten erhalten.")
        return

    # MultiIndex-Spalten von yfinance bereinigen, falls vorhanden
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 2. Bedingungen für Bullenflagge (BUY) & Bärenflagge (SELL)
    # Mast-Berechnung (Veränderung über 5 Kerzen)
    df['Impulse'] = (df['Close'] - df['Close'].shift(5)) / df['Close'].shift(5) * 100
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # --- BULL FLAG (BUY) ---
    is_bull_impulse = prev['Impulse'] > 1.5
    bull_breakout = is_bull_impulse and (latest['Close'] > prev['High'])
    
    if bull_breakout:
        entry = latest['Close']
        stop_loss = prev['Low'] - 1.5          # SL knapp unter das Tief der Flagge
        mast_height = prev['Close'] - df['Close'].shift(5)
        take_profit = entry + mast_height       # TP in Höhe des Mastes nach oben
        
        msg = (
            f"🟢 *BULL FLAG SIGNAL (BUY)* 🟢\n\n"
            f"• **Asset:** Gold (XAUUSD / GC=F)\n"
            f"• **Einstieg (Entry):** `{entry:.2f}`\n"
            f"• **Stop-Loss (SL):** `{stop_loss:.2f}`\n"
            f"• **Take-Profit (TP):** `{take_profit:.2f}`\n"
            f"• **Zeit:** `{df.index[-1]}`"
        )
        send_telegram_message(msg)
        return

    # --- BEAR FLAG (SELL) ---
    is_bear_impulse = prev['Impulse'] < -1.5
    bear_breakout = is_bear_impulse and (latest['Close'] < prev['Low'])
    
    if bear_breakout:
        entry = latest['Close']
        stop_loss = prev['High'] + 1.5         # SL knapp über das Hoch der Flagge
        mast_height = abs(prev['Close'] - df['Close'].shift(5))
        take_profit = entry - mast_height       # TP in Höhe des Mastes nach unten
        
        msg = (
            f"🔴 *BEAR FLAG SIGNAL (SELL)* 🔴\n\n"
            f"• **Asset:** Gold (XAUUSD / GC=F)\n"
            f"• **Einstieg (Entry):** `{entry:.2f}`\n"
            f"• **Stop-Loss (SL):** `{stop_loss:.2f}`\n"
            f"• **Take-Profit (TP):** `{take_profit:.2f}`\n"
            f"• **Zeit:** `{df.index[-1]}`"
        )
        send_telegram_message(msg)
        return

    print("Kein Signal (weder Buy noch Sell) im aktuellen Intervall.")

if __name__ == "__main__":
    check_trading_signals()
