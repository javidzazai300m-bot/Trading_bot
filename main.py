import os
import requests
import yfinance as yf
import pandas as pd

# Telegram Zugangsdaten aus GitHub Secrets auslesen
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Liste der Symbole: Gold, Bitcoin, Ethereum
SYMBOLS = {
    "Gold (XAU/USD)": "GC=F",
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD"
}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze_market():
    messages = ["📊 **MARKT-ANALYSEN & SIGNALE** 📊\n"]
    
    for name, ticker in SYMBOLS.items():
        # Daten abrufen (Stunden-Intervall)
        df = yf.download(ticker, period="7d", interval="1h")
        if df.empty:
            continue
            
        # Wenn MultiIndex vorhanden ist (yfinance Standard), vereinfachen
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Technische Indikatoren berechnen
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['RSI'] = calculate_rsi(df)

        current_price = float(df['Close'].iloc[-1])
        prev_price = float(df['Close'].iloc[-2])
        percent_change = ((current_price - prev_price) / prev_price) * 100

        ema20 = float(df['EMA_20'].iloc[-1])
        ema50 = float(df['EMA_50'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])

        # Signal-Logik
        if current_price > ema20 and ema20 > ema50 and rsi > 50:
            signal = "🟢 **BULLISH SIGNAL (KAUFEN)**"
            recommendation = "Der Trend steigt. Gute Gelegenheit für Kauf / Long."
        elif current_price < ema20 and ema20 < ema50 and rsi < 50:
            signal = "🔴 **BEARISH SIGNAL (VERKAUFEN)**"
            recommendation = "Der Trend fällt. Gute Gelegenheit für Verkauf / Short."
        else:
            signal = "⚪ **NEUTRAL / SEITWÄRTS**"
            recommendation = "Abwarten, bis ein deutlicher Ausbruch erfolgt."

        msg = (
            f"Asset: **{name}**\n"
            f"Preis: `${current_price:,.2f}` ({percent_change:+.2f}%)\n"
            f"RSI: `{rsi:.1f}`\n"
            f"Signal: {signal}\n"
            f"Empfehlung: {recommendation}\n"
            f"-----------------------------------"
        )
        messages.append(msg)

    final_message = "\n\n".join(messages)
    send_telegram_message(final_message)

if __name__ == "__main__":
    analyze_market()
