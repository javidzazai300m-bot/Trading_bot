from datetime import datetime
import os
import time
import pandas as pd
import requests
import yfinance as yf

# --- ZUGANGSDATEN AUS SICHEREN VARIABLEN LADEN ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(message_text):
  """Sendet die Nachricht an deinen Telegram-Chat."""
  if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ Telegram-Token oder Chat-ID nicht gefunden!")
    return

  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message_text,
      "parse_mode": "Markdown",
  }
  try:
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    print("✅ Signal erfolgreich an Telegram gesendet.")
  except Exception as e:
    print(f"❌ Telegram-Fehler: {e}")


def calculate_atr(df, period=12):
  """Berechnet die Average True Range (ATR)."""
  high_low = df["High"] - df["Low"]
  high_close = (df["High"] - df["Close"].shift()).abs()
  low_close = (df["Low"] - df["Close"].shift()).abs()
  ranges = pd.concat([high_low, high_close, low_close], axis=1)
  true_range = ranges.max(axis=1)
  return true_range.rolling(period).mean()


def check_gold_setup():
  """Analysiert Gold auf dem M15-Timeframe."""
  ticker_symbol = "GC=F"
  interval = "15m"
  period = "1mo"

  try:
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period=period, interval=interval)

    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    if df.empty or len(df) < 50:
      return None

    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["ATR"] = calculate_atr(df)

    current_price = float(df["Close"].iloc[-1])
    ema_20 = float(df["EMA_20"].iloc[-1])
    ema_50 = float(df["EMA_50"].iloc[-1])
    atr = float(df["ATR"].iloc[-1])

    if pd.isna(current_price) or pd.isna(ema_20) or pd.isna(ema_50):
      return None

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
    print(f"❌ Fehler bei der Analyse: {e}")
    return None


def main():
  print("🚀 Gold-Bot gestartet und im Überwachungsmodus...")
  last_signal = None  # Speichert das vorherige Signal

  while True:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{current_time}] Prüfe Gold-Setup...")

    data = check_gold_setup()

    if data:
      print(
          f"🔍 Preis: ${data['price']} | Signal: {data['signal']} | Trend:"
          f" {data['trend']}"
      )

      # Optionale Logik: Nachricht nur bei Signalwechsel senden oder bei jedem Intervall
      # Hier senden wir eine Nachricht, wenn sich das Signal ändert ODER es ein echter Trade ist:
      if data["signal"] != last_signal:
        report = (
            f"📊 M15 UPDATE: GOLD STATUS 📊\n"
            f"-----------------------------------\n"
            f"• Asset: {data['symbol']} ({data['timeframe']})\n"
            f"• Signal: {data['signal']}\n"
            f"• Trend: {data['trend']}\n"
            f"• Empfehlung: {data['trade_advice']}\n\n"
            f"💵 Aktueller Preis: ${data['price']}\n"
        )

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
        last_signal = data["signal"]
      else:
        print(
            "ℹ️ Signal unverändert – keine erneute Telegram-Nachricht"
            " erforderlich."
        )
    else:
      print("⚠️ Konnte keine Daten abrufen.")

    # 300 Sekunden = 5 Minuten warten bis zur nächsten Prüfung
    time.sleep(300)


if __name__ == "__main__":
  main()
