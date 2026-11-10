import time
import requests
import pandas as pd
import yfinance as yf

# --- DEINE DATEN ---
SYMBOL = "GC=F"          # Gold Futures (XAUUSD-Äquivalent)
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
TELEGRAM_CHAT_ID = "6551623158"

def send_telegram_message(message):
    """Sendet die Nachricht direkt an deinen Telegram-Chat"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Verbindungsfehler: {e}")

def check_trading_signals():
    """Analysiert den Markt und sendet immer eine Status- oder Signalnachricht"""
    print(f"Analysiere Markt für {SYMBOL}...")
    
    # 1. Kursdaten laden
    df = yf.download(SYMBOL, period="5d", interval="15m", progress=False)
    if df.empty:
        print("Keine Daten erhalten.")
        return

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 2. Bedingungen für Bullen- und Bärenflagge
    df['Impulse'] = (df['Close'] - df['Close'].shift(5)) / df['Close'].shift(5) * 100
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # --- BULL FLAG (BUY) ---
    is_bull_impulse = prev['Impulse'] > 1.0
    bull_breakout = is_bull_impulse and (latest['Close'] > prev['High'])
    
    if bull_breakout:
        entry = latest['Close']
        stop_loss = prev['Low'] - 1.0
        mast_height = prev['Close'] - df['Close'].shift(5)
        take_profit = entry + mast_height
        
        msg = (
            f"🟢 *BULL FLAG SIGNAL (BUY)* 🟢\n\n"
            f"• **Asset:** Gold (XAUUSD)\n"
            f"• **Einstieg (Entry):** `{entry:.2f}`\n"
            f"• **Stop-Loss (SL):** `{stop_loss:.2f}`\n"
            f"• **Take-Profit (TP):** `{take_profit:.2f}`\n"
            f"• **Zeit:** `{df.index[-1]}`"
        )
        send_telegram_message(msg)
        return

    # --- BEAR FLAG (SELL) ---
    is_bear_impulse = prev['Impulse'] < -1.0
    bear_breakout = is_bear_impulse and (latest['Close'] < prev['Low'])
    
    if bear_breakout:
        entry = latest['Close']
        stop_loss = prev['High'] + 1.0
        mast_height = abs(prev['Close'] - df['Close'].shift(5))
        take_profit = entry - mast_height
        
        msg = (
            f"🔴 *BEAR FLAG SIGNAL (SELL)* 🔴\n\n"
            f"• **Asset:** Gold (XAUUSD)\n"
            f"• **Einstieg (Entry):** `{entry:.2f}`\n"
            f"• **Stop-Loss (SL):** `{stop_loss:.2f}`\n"
            f"• **Take-Profit (TP):** `{take_profit:.2f}`\n"
            f"• **Zeit:** `{df.index[-1]}`"
        )
        send_telegram_message(msg)
        return

    # --- WENN KEIN SIGNAL DA IST (Statusmeldung) ---
    status_msg = (
        f"🔍 *Gold-Bot Status-Update*\n\n"
        f"• Kurs analysiert: `{latest['Close']:.2f}`\n"
        f"• Status: Kein klares Flaggen-Signal im Moment.\n"
        f"• Zeit: `{df.index[-1]}`\n\n"
        f"_Bot läuft und prüft beim nächsten Intervall erneut._"
    )
    send_telegram_message(status_msg)

if __name__ == "__main__":
    check_trading_signals()