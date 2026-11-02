import pandas as pd
import requests
import yfinance as yf

# --- DEINE ZUGANGSDATEN ---
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
TELEGRAM_CHAT_ID = "6551623158"


def send_telegram_message(message_text):
  """Sendet die Nachricht an deinen Telegram-Chat."""
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message_text,
      "parse_mode": "Markdown",
  }
  try:
    requests.post(url, json=payload)
  except Exception as e:
    print(f"Netzwerkfehler: {e}")


def calculate_atr(df, period=14):
  """Berechnet die Average True Range (ATR) für die Volatilität."""
  high_low = df['High'] - df['Low']
  high_close = (df['High'] - df['Close'].shift()).abs()
  low_close = (df['Low'] - df['Close'].shift()).abs()
  ranges = pd.concat([high_low, high_close, low_close], axis=1)
  true_range = ranges.max(axis=1)
  return true_range.rolling(period).mean()


def check_market_setup(ticker_symbol, interval='1h', period='60d'):
  """Berechnet Trend, Einstieg, SL und TP basierend auf EMA & ATR."""
  try:
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty or len(df) < 200:
      return None

    # Indikatoren berechnen
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['ATR'] = calculate_atr(df)

    current_price = df['Close'].iloc[-1]
    ema_50 = df['EMA_50'].iloc[-1]
    ema_200 = df['EMA_200'].iloc[-1]
    atr = df['ATR'].iloc[-1]

    # Trend- und Signal-Logik
    if ema_50 > ema_200 and current_price > ema_50:
      trend = 'BULLISH 🟢'
      signal = 'BUY (LONG)'
      # SL unter dem aktuellen Kurs basierend auf ATR, TP mit CRV 2:1
      stop_loss = current_price - (1.5 * atr)
      take_profit = current_price + (3.0 * atr)
    elif ema_50 < ema_200 and current_price < ema_50:
      trend = 'BEARISH 🔴'
      signal = 'SELL (SHORT)'
      # SL über dem aktuellen Kurs, TP nach unten
      stop_loss = current_price + (1.5 * atr)
      take_profit = current_price - (3.0 * atr)
    else:
      trend = 'NEUTRAL / KORREKTUR 🟡'
      signal = 'KEIN TRADE (Seitwärtsmarkt)'
      stop_loss = 0
      take_profit = 0

    return {
        'symbol': ticker_symbol,
        'trend': trend,
        'signal': signal,
        'price': round(current_price, 2),
        'sl': round(stop_loss, 2),
        'tp': round(take_profit, 2),
        'ema_50': round(ema_50, 2),
        'ema_200': round(ema_200, 2),
    }

  except Exception as e:
    print(f'Fehler bei {ticker_symbol}: {e}')
    return None


def main():
  symbols = {'Gold (XAU/USD)': 'GC=F', 'Bitcoin': 'BTC-USD', 'Ethereum': 'ETH-USD'}

  report = '🤖 *Zabaritradingbot Signal-Analyse*\n'
  report += '-----------------------------------\n\n'

  for name, sym in symbols.items():
    data = check_market_setup(sym, interval='1h', period='60d')
    if data:
      report += (
          f'📊 *{name}* (`{sym}`)\n'
          f'• *Trend:* {data["trend"]}\n'
          f'• *Signal:* *{data["signal"]}*\n'
          f'• *Einstieg (Kurs):* ${data["price"]}\n'
      )
      if data['signal'] != 'KEIN TRADE (Seitwärtsmarkt)':
        report += (
            f'• *Stop-Loss (SL):* 🛑 ${data["sl"]}\n'
            f'• *Take-Profit (TP):* 🎯 ${data["tp"]}\n'
        )
      report += (
          f'• *EMA 50:* ${data["ema_50"]} | *EMA 200:* ${data["ema_200"]}\n\n'
      )

  send_telegram_message(report)


if __name__ == '__main__':
  main()
