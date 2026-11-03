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
      # parse_mode entfernt, um Markdown-Fehler zu vermeiden
  }
  try:
    response = requests.post(url, json=payload)
    # Wichtig: Löst bei HTTP-Fehlern (z.B. 400 Bad Request) einen Fehler aus
    response.raise_for_status()
    print("✅ Signal erfolgreich an Telegram gesendet.")
  except requests.exceptions.HTTPError as err:
    print(f"❌ Telegram HTTP-Fehler: {err}")
    print(f"Antwort von Telegram: {response.text}")
  except Exception as e:
    print(f"❌ Netzwerk- oder unerwarteter Fehler: {e}")


def calculate_atr(df, period=14):
  """Berechnet die Average True Range (ATR) für die Volatilität."""
  high_low = df["High"] - df["Low"]
  high_close = (df["High"] - df["Close"].shift()).abs()
  low_close = (df["Low"] - df["Close"].shift()).abs()
  ranges = pd.concat([high_low, high_close, low_close], axis=1)
  true_range = ranges.max(axis=1)
  return true_range.rolling(period).mean()


def check_gold_setup():
  """Analysiert Gold auf dem M15-Timeframe mit EMA & ATR."""
  ticker_symbol = "XAUUSD=X"
  interval = "15m"
  period = "60d"

  try:
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty or len(df) < 200:
      return None

    # Indikatoren berechnen
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA_200"] = df["Close"].ewm(span=200, adjust=False).mean()
    df["ATR"] = calculate_atr(df)

    current_price = df["Close"].iloc[-1]
    ema_50 = df["EMA_50"].iloc[-1]
    ema_200 = df["EMA_200"].iloc[-1]
    atr = df["ATR"].iloc[-1]

    # Trend- und Signal-Logik (M15)
    if ema_50 > ema_200 and current_price > ema_50:
      trend = "BULLISH 🟢"
      signal = "BUY (LONG)"
      trade_advice = "JA (Trend ist Bullish - Jetzt Long traden)"
      stop_loss = current_price - (1.5 * atr)
      take_profit = current_price + (3.0 * atr)
    elif ema_50 < ema_200 and current_price < ema_50:
      trend = "BEARISH 🔴"
      signal = "SELL (SHORT)"
      trade_advice = "JA (Trend ist Bearish - Jetzt Short traden)"
      stop_loss = current_price + (1.5 * atr)
      take_profit = current_price - (3.0 * atr)
    else:
      trend = "NEUTRAL / SEITWÄRTS 🟡"
      signal = "KEIN TRADE"
      trade_advice = "NEIN (Warten auf klaren Trend / Seitwärtsphase)"
      stop_loss = 0
      take_profit = 0

    return {
        "symbol": "Gold (XAU/USD)",
        "timeframe": "M15",
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
    print(f"Fehler bei der Gold-Analyse: {e}")
    return None


def main():
  print("🤖 Starte einmalige Gold M15 Prüfung...")

  data = check_gold_setup()

  if data:
    current_signal = data["signal"]
    print(f"Aktuelles Signal ermittelt: {current_signal}")

    # Wenn ein echter Trade vorliegt, an Telegram senden
    if current_signal != "KEIN TRADE":
      report = (
          f"🚨 NEUES M15 TRADING SIGNAL 🚨\n"
          f"-----------------------------------\n"
          f"📊 Asset: {data['symbol']} ({data['timeframe']})\n"
          f"• Trend: {data['trend']}\n"
          f"• Signal: {data['signal']}\n"
          f"• Empfehlung: {data['trade_advice']}\n\n"
          f"• Aktueller Preis (Einstieg): ${data['price']}\n"
          f"• Stop-Loss (SL): ${data['sl']}\n"
          f"• Take-Profit (TP): ${data['tp']}\n\n"
          f"• EMA 50: ${data['ema_50']} | EMA 200: ${data['ema_200']}\n"
      )
      send_telegram_message(report)
    else:
      print("ℹ️ Kein klares Trade-Signal (Seitwärtsphase). Keine Nachricht gesendet.")
  else:
    print("⚠️ Warnung: Konnte keine aktuellen Daten abrufen.")


if __name__ == "__main__":
  main()
