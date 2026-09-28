import os
import requests
import yfinance as yf
import pandas as pd

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SYMBOLS = {
    "Gold (XAU/USD)": "GC=F",
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD"
}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.post(url, data=payload)
    print("Telegram Response Status:", response.status_code)
    print("Telegram Response Text:", response.text)

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze_market():
    messages = ["📊 MARKT-ANALYSEN & SIGNALE 📊\n"]
    
    for name, ticker in SYMBOLS.items():
        try:
            df = yf.download(ticker, period="7d", interval="1h", progress=False)
            if df.empty:
                print(f"Keine Daten für {ticker}")
                continue
                
            # Schlusskurse als Pandas Series extrahieren
            if isinstance(df.columns, pd.MultiIndex):
                close_prices = df['Close'][ticker]
            else:
                close_prices = df['Close']
            
            close_prices = close_prices.dropna()

            ema20_series = close_prices.ewm(span=20, adjust=False).mean()
            ema50_series = close_prices.ewm(span=50, adjust=False).mean()
            rsi_series = calculate_rsi(close_prices)

            current_price = float(close_prices.iloc[-1])
            prev_price = float(close_prices.iloc[-2])
            percent_change = ((current_price - prev_price) / prev_price) * 100

            ema20 = float(ema20_series.iloc[-1])
            ema50 = float(ema50_series.iloc[-1])
            rsi = float(rsi_series.iloc[-1])

            if current_price > ema20 and ema20 > ema50 and rsi > 50:
                signal = "🟢 BULLISH SIGNAL (KAUFEN)"
                recommendation = "Aufwärtstrend! Kauf / Long im Blick behalten."
            elif current_price < ema20 and ema20 < ema50 and rsi < 50:
                signal = "🔴 BEARISH SIGNAL (VERKAUFEN)"
                recommendation = "Abwärtstrend! Verkauf / Short im Blick behalten."
            else:
                signal = "⚪ NEUTRAL / SEITWÄRTS"
                recommendation = "Abwarten auf einen Ausbruch."

            msg = (
                f"Asset: {name}\n"
                f"Preis: ${current_price:,.2f} ({percent_change:+.2f}%)\n"
                f"RSI: {rsi:.1f}\n"
                f"Signal: {signal}\n"
                f"Empfehlung: {recommendation}\n"
                f"-----------------------------------"
            )
            messages.append(msg)
        except Exception as e:
            print(f"Fehler bei {name}: {e}")

    final_message = "\n\n".join(messages)
    send_telegram_message(final_message)

if __name__ == "__main__":
    analyze_market()
