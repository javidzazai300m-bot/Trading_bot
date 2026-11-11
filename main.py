from datetime import datetime
import pandas as pd
import requests
import yfinance as yf

# --- DEINE ZUGANGSDATEN ---
TELEGRAM_TOKEN = 8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc
TELEGRAM_CHAT_ID = 6551623158


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
  """Analysiert Gold auf dem M15-Timeframe mit dynamischer EMA & ATR Logik."""
  ticker_symbol = "GC=F"  # Gold-Futures
  interval = "15m"
  period = "1mo"  # 1 Monat Historie garantiert genügend Kerzen für M15

  try:
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty or len(df) < 50:
      print(f"⚠️ Zu wenig oder keine Daten geladen (Zeilen: {len(df)})")
      return None

    # Indikatoren berechnen (EMA 20 & EMA 50 für M15)
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["ATR"] = calculate_atr(df)

    current_price = df["Close"].iloc[-1]
    ema_20 = df["EMA_20"].iloc[-1]
    ema_50 = df["EMA_50"].iloc[-1]
    atr = df["ATR"].iloc[-1]

    # Dynamische Trend- und Signal-Logik für M15
    if current_price > ema_20 and ema_20 > ema_50:
      trend = "BULLISH 🟢"
      signal = "BUY (LONG)"
      trade_advice = "JA (Aufwärtstrend im M15 - Long Einstieg)"
      entry_price = current_price
      stop_loss = entry_price - (1.5 * atr)
      take_profit = entry_price + (3.0 * atr)
    elif current_price < ema_20 and ema_20 < ema_50:
      trend = "BEARISH 🔴"
      signal = "SELL (SHORT)"
      trade_advice = "JA (Abwärtstrend im M15 - Short Einstieg)"
      entry_price = current_price
      stop_loss = entry_price + (1.5 * atr)
      take_profit = entry_price - (3.0 * atr)
    else:
      trend = "NEUTRAL / KORREKTUR 🟡"
      signal = "KEIN KLARES SIGNAL"
      trade_advice = "NEIN (Warten auf klaren Trend / Seitwärtsphase)"
      entry_price = current_price
      stop_loss = 0
      take_profit = 0

    return {
        "symbol": "Gold Futures (GC=F)",
        "timeframe": "M15",
        "trend": trend,
        "signal": signal,
        "trade_advice": trade_advice,
        "price": round(current_price, 2),
        "entry": round(entry_price, 2),
        "sl": round(stop_loss, 2),
        "tp": round(take_profit, 2),
        "ema_20": round(ema_20, 2),
        "ema_50": round(ema_50, 2),
    }

  except Exception as e:
    print(f"❌ Fehler bei der Gold-Analyse: {e}")
    return None


def main():
  current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  print(f"\n[{current_time}] Starte M15 Gold-Analyse...")

  data = check_gold_setup()

  if data:
    print(
        f"🔍 Preis: ${data['price']} | Signal: {data['signal']} | Trend:"
        f" {data['trend']}"
    )

    # Grundreport zusammenbauen
    report = (
        f"📊 M15 UPDATE: GOLD STATUS 📊\n"
        f"-----------------------------------\n"
        f"• Asset: {data['symbol']} ({data['timeframe']})\n"
        f"• Signal: {data['signal']}\n"
        f"• Trend: {data['trend']}\n"
        f"• Empfehlung: {data['trade_advice']}\n\n"
        f"💵 Aktueller Preis: ${data['price']}\n"
    )

    # SL und TP nur anhängen, wenn ein echtes Buy/Sell Signal vorliegt
    if data["sl"] > 0:
      report += (
          f"🎯 Einstiegspreis: ${data['entry']}\n"
          f"🛑 Stop-Loss (SL): ${data['sl']}\n"
          f"🎯 Take-Profit (TP): ${data['tp']}\n\n"
      )

    report += (
        f"• EMA 20: ${data['ema_20']} | EMA 50: ${data['ema_50']}\n"
        f"🕒 Zeit: {current_time}"
    )

    send_telegram_message(report)
  else:
    print("⚠️ Konnte keine Daten abrufen.")
    send_telegram_message(
        "⚠️ M15 Gold-Bot: Warnung - Konnte keine Marktdaten abrufen."
    )


if __name__ == "__main__":
  main()