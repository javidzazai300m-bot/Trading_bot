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
  }
  try:
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    print("✅ Signal erfolgreich an Telegram gesendet.")
  except requests.exceptions.HTTPError as err:
    print(f"❌ Telegram HTTP-Fehler: {err}")
    print(f"Antwort von Telegram: {response.text}")
  except Exception as e:
    print(f"❌ Netzwerk- oder unerwarteter Fehler: {e}")


def calculate_atr(df, period=12):
  """Berechnet die Average True Range (ATR) für die Volatilität."""
  high_low = df["High"] - df["Low"]
  high_close = (df["High"] - df["Close"].shift()).abs()
  low_close = (df["Low"] - df["Close"].shift()).abs()
  ranges = pd.concat([high_low, high_close, low_close], axis=1)
  true_range = ranges.max(axis=1)
  return true_range.rolling(period).mean()


def check_gold_setup():
  """Analysiert Gold auf dem M15-Timeframe für 15-Minuten-Scalping."""
  ticker_symbol = "GC=F"  # Nutzt stabile Future-Daten als Quelle
  interval = "15m"
  period = "60d"  # 60 Tage Historie reicht völlig für M15 aus

  try:
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty or len(df) < 50:
      print(f"⚠️ Zu wenig oder keine Daten geladen (Zeilen: {len(df)})")
      return None

    # Indikatoren berechnen (für schnelleres Scalping können EMA 20/50 oder EMA 50/200 genutzt werden)
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA_200"] = df["Close"].ewm(span=200, adjust=False).mean()
    df["ATR"] = calculate_atr(df)

    current_price = df["Close"].iloc[-1]
    ema_50 = df["EMA_50"].iloc[-1]
    ema_200 = df["EMA_200"].iloc[-1]
    atr = df["ATR"].iloc[-1]

    # Trend- und Signal-Logik (M15 Scalping)
    if ema_50 > ema_200 and current_price > ema_50:
      trend = "BULLISH 🟢"
      signal = "BUY (LONG SCALP)"
      trade_advice = "JA (M15 Trend Bullish - Scalp Long)"
      stop_loss = current_price - (1.2 * atr)  # Etwas strafferer SL für Scalping
      take_profit = current_price + (1.8 * atr)
    elif ema_50 < ema_200 and current_price < ema_50:
      trend = "BEARISH 🔴"
      signal = "SELL (SHORT SCALP)"
      trade_advice = "JA (M15 Trend Bearish - Scalp Short)"
      stop_loss = current_price + (1.2 * atr)
      take_profit = current_price - (1.8 * atr)
    else:
      trend = "NEUTRAL / SEITWÄRTS 🟡"
      signal = "KEIN TRADE"
      trade_advice = "NEIN (Kein klarer M15 Trend - Warten)"
      stop_loss = 0
      take_profit = 0

    return {
        "symbol": "XAUUSD (Spot / Gold)",
        "timeframe": "M15 (15-Min Scalping)",
        "trend": trend,
        "signal": signal,
        "trade_advice": trade_advice,
        "price": round(current_price, 2),
        "sl": round(stop_loss, 2),
        "tp": round(take_profit, 2),
        "ema_50": round(ema_50, 2),
        "ema_200": round(ema_200, 2),
    }

  except Exception as e:
    print(f"❌ Fehler bei der XAUUSD-Analyse: {e}")
    return None


def main():
  print("🤖 Führe XAUUSD M15 Scalping Prüfung aus...")
  data = check_gold_setup()

  if data:
    report = (
        f"⚡ XAUUSD 15-MINUTEN SCALPING BOT ⚡\n"
        f"-----------------------------------\n"
        f"📊 Asset: {data['symbol']} ({data['timeframe']})\n"
        f"• Trend: {data['trend']}\n"
        f"• Signal: {data['signal']}\n"
        f"• Empfehlung: {data['trade_advice']}\n\n"
        f"• Aktueller Preis: ${data['price']}\n"
        f"• Stop-Loss (SL): ${data['sl']}\n"
        f"• Take-Profit (TP): ${data['tp']}\n\n"
        f"• EMA 50: ${data['ema_50']} | EMA 200: ${data['ema_200']}\n"
    )
    send_telegram_message(report)
  else:
    print("⚠️ Warnung: Konnte keine aktuellen Daten abrufen.")
    send_telegram_message(
        "⚠️ XAUUSD Scalp Bot: Warnung - Konnte keine Marktdaten abrufen."
    )


if __name__ == "__main__":
  main()
