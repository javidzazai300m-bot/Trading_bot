import pandas as pd
import requests
import yfinance as yf

# --- DEINE ZUGANGSDATEN ---
# Tipp: Am besten nutzt du einen neu generierten Token aus BotFather!
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
TELEGRAM_CHAT_ID = "6551623158"


def send_telegram_message(message_text):
  """Sendet eine Nachricht direkt an deinen Telegram-Chat."""
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message_text,
      "parse_mode": "Markdown",
  }
  try:
    response = requests.post(url, json=payload)
    if response.status_code == 200:
      print("Telegram-Nachricht erfolgreich gesendet!")
    else:
      print(f"Fehler beim Senden: {response.text}")
  except Exception as e:
    print(f"Netzwerkfehler: {e}")


def check_ema_trend(ticker_symbol, interval="1h", period="60d"):
  """Berechnet EMA 50 & 200 und bestimmt den Trendstatus."""
  try:
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty or len(df) < 200:
      return None

    # EMA 50 und EMA 200 berechnen
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA_200"] = df["Close"].ewm(span=200, adjust=False).mean()

    current_price = df["Close"].iloc[-1]
    ema_50 = df["EMA_50"].iloc[-1]
    ema_200 = df["EMA_200"].iloc[-1]

    # Trend-Logik
    if ema_50 > ema_200 and current_price > ema_50:
      trend = "BULLISH 🟢"
      description = "Starker Aufwärtstrend (Kurs > EMA50 > EMA200)"
    elif ema_50 < ema_200 and current_price < ema_50:
      trend = "BEARISH 🔴"
      description = "Starker Abwärtstrend (Kurs < EMA50 < EMA200)"
    else:
      trend = "NEUTRAL / KORREKTUR 🟡"
      description = "Misch- oder Seitwärtsmarkt"

    return {
        "symbol": ticker_symbol,
        "trend": trend,
        "description": description,
        "price": round(current_price, 2),
        "ema_50": round(ema_50, 2),
        "ema_200": round(ema_200, 2),
    }

  except Exception as e:
    print(f"Fehler bei {ticker_symbol}: {e}")
    return None


def main():
  # Zu prüfende Märkte (Gold, Bitcoin, Ethereum)
  symbols = {"Gold (XAU/USD)": "GC=F", "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD"}

  report = "🤖 *Zabaritradingbot Markt-Analyse*\n"
  report += "-----------------------------------\n\n"

  for name, sym in symbols.items():
    data = check_ema_trend(sym, interval="1h", period="60d")
    if data:
      report += (
          f"📊 *{name}* (`{sym}`)\n"
          f"• *Trend:* {data['trend']}\n"
          f"• *Kurs:* ${data['price']}\n"
          f"• *EMA 50:* ${data['ema_50']} | *EMA 200:* ${data['ema_200']}\n"
          f"• _{data['description']}_\n\n"
      )

  # Nachricht absenden
  send_telegram_message(report)


if __name__ == "__main__":
  main()
