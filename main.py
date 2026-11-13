from datetime import datetime
import os
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
    print("✅ Telegram-Nachricht erfolgreich gesendet.")
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
  """Analysiert Gold im H1-Zeitfenster."""
  ticker_symbol = "GC=F"  # Gold Futures
  interval = "1h"  # H1 Zeitfenster
  period = "30d"  # 30 Tage Historie für stabile EMAs

  print("🔄 Lade H1-Marktdaten von Yahoo Finance...")
  try:
    # Session mit Browser-User-Agent gegen Blockaden
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
            " like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
    })

    ticker = yf.Ticker(ticker_symbol, session=session)
    df = ticker.history(period=period, interval=interval)

    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    if df.empty or len(df) < 50:
      print(f"⚠️ Zu wenig Daten geladen (Zeilen: {len(df)})")
      return None

    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["ATR"] = calculate_atr(df)

    current_price = float(df["Close"].iloc[-1])
    ema_20 = float(df["EMA_20"].iloc[-1])
    ema_50 = float(df["EMA_50"].iloc[-1])
    atr = float(df["ATR"].iloc[-1])

    if pd.isna(current_price) or pd.isna(ema_20) or pd.isna(ema_50):
      print("⚠️ Indikatoren enthalten NaN-Werte.")
      return None

    # --- VERBESSERTE TREND-LOGIK ---
    # Prüft, ob der EMA 20 über dem EMA 50 liegt und der Preis über dem EMA 50 (verhindert falsche Shorts bei kleinen Rücksetzern)
    ema_slope_bullish = ema_20 > ema_50
    price_above_support = current_price > ema_50

    if ema_slope_bullish and price_above_support:
      trend = "BULLISH 🟢"
      signal = "BUY (LONG)"
      trade_advice = "JA (Aufwärtstrend im H1 - Long Einstieg)"
      entry_price = current_price
      stop_loss = entry_price - (1.5 * atr)
      take_profit = entry_price + (3.0 * atr)
    elif not ema_slope_bullish and current_price < ema_50:
      trend = "BEARISH 🔴"
      signal = "SELL (SHORT)"
      trade_advice = "JA (Abwärtstrend im H1 - Short Einstieg)"
      entry_price = current_price
      stop_loss = entry_price + (1.5 * atr)
      take_profit = entry_price - (3.0 * atr)
    else:
      trend = "NEUTRAL / KORREKTUR 🟡"
      signal = "KEIN KLARES SIGNAL (NEUTRAL)"
      trade_advice = "NEIN (Warten auf klaren Trend / Seitwärtsphase)"
      entry_price = current_price
      stop_loss = 0
      take_profit = 0

    return {
        "symbol": "Gold Futures (GC=F)",
        "timeframe": "H1",
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
    print(f"❌ Fehler beim Laden der Daten: {e}")
    return None


def main():
  current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  print(f"\n[{current_time}] Starte H1 Gold-Analyse...")

  data = check_gold_setup()

  if data:
    print(
        f"🔍 Preis: ${data['price']} | Signal: {data['signal']} | Trend:"
        f" {data['trend']}"
    )

    report = (
        f"📊 H1 UPDATE: GOLD STATUS 📊\n"
        f"-----------------------------------\n"
        f"• Asset: {data['symbol']} ({data['timeframe']})\n"
        f"• Signal / Status: {data['signal']}\n"
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
    else:
      report += f"🎯 Einstiegspreis: ${data['entry']} (Kein Trade aktiv)\n\n"

    report += (
        f"• EMA 20: ${data['ema_20']} | EMA 50: ${data['ema_50']}\n"
        f"🕒 Zeit: {current_time}"
    )

    send_telegram_message(report)
  else:
    print("⚠️ Konnte keine Daten abrufen.")
    send_telegram_message(
        "⚠️ H1 Gold-Bot: Warnung - Konnte keine Marktdaten abrufen."
    )


if __name__ == "__main__":
  main()
