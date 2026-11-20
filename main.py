from datetime import datetime
import json
import os
import pandas as pd
import requests
import yfinance as yf

# --- ZUGANGSDATEN AUS SICHEREN VARIABLEN LADEN ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
STATE_FILE = "last_signal_state.json"


def send_telegram_message(message_text):
  """Sendet die Nachricht an deinen Telegram-Chat."""
  if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ Telegram-Token oder Chat-ID nicht gefunden!")
    return

  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message_text,
      "parse_mode": "HTML",
  }
  try:
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    print("✅ Telegram-Nachricht erfolgreich gesendet.")
  except Exception as e:
    print(f"❌ Telegram-Fehler: {e}")


def load_last_signal():
  """Lädt das zuletzt gesendete Signal, um doppelte Meldungen zu vermeiden."""
  if os.path.exists(STATE_FILE):
    try:
      with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("last_signal")
    except Exception:
      return None
  return None


def save_last_signal(signal):
  """Speichert das aktuelle Signal."""
  try:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
      json.dump({"last_signal": signal}, f)
  except Exception as e:
    print(f"⚠️ Konnte Signal-Status nicht speichern: {e}")


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
  ticker_symbol = "GC=F"  # Gold Futures (alternativ XAUUSD=X falls verfügbar)
  interval = "1h"
  period = "30d"

  print("🔄 Lade H1-Marktdaten von Yahoo Finance...")
  try:
    df = yf.download(
        ticker_symbol, period=period, interval=interval, progress=False
    )

    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    if df.empty or len(df) < 25:
      print(f"⚠️ Zu wenig Daten geladen (Zeilen: {len(df)})")
      return None

    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["ATR"] = calculate_atr(df)

    current_price = float(df["Close"].iloc[-1])
    prev_price = float(df["Close"].iloc[-2])
    ema_20 = float(df["EMA_20"].iloc[-1])
    ema_20_prev = float(df["EMA_20"].iloc[-2])
    atr = float(df["ATR"].iloc[-1])

    if (
        pd.isna(current_price)
        or pd.isna(prev_price)
        or pd.isna(ema_20)
        or pd.isna(atr)
    ):
      print("⚠️ Indikatoren enthalten NaN-Werte.")
      return None

    price_rising = current_price > prev_price
    price_falling = current_price < prev_price
    ema_rising = ema_20 > ema_20_prev
    ema_falling = ema_20 < ema_20_prev

    # --- DIREKTE TREND-/BEWEGUNGSLOGIK ---
    # Gold steigt (Kurs höher als Vor-Kerze und EMA 20 dreht hoch bzw. Kurs über EMA 20)
    if price_rising and (ema_rising or current_price > ema_20):
      trend = "STEIGEND 🟢"
      signal = "BUY"
      trade_advice = "JA (Gold steigt - BUY Signal)"
      entry_price = current_price
      stop_loss = entry_price - (1.5 * atr)
      take_profit = entry_price + (3.0 * atr)
    # Gold fällt (Kurs tiefer als Vor-Kerze und EMA 20 dreht runter bzw. Kurs unter EMA 20)
    elif price_falling and (ema_falling or current_price < ema_20):
      trend = "FALLEND 🔴"
      signal = "SELL"
      trade_advice = "JA (Gold fällt - SELL Signal)"
      entry_price = current_price
      stop_loss = entry_price + (1.5 * atr)
      take_profit = entry_price - (3.0 * atr)
    else:
      trend = "SEITWÄRTS / UNKLAR 🟡"
      signal = "NEUTRAL"
      trade_advice = "NEIN (Keine klare Richtung)"
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
        "prev_price": round(prev_price, 2),
        "entry": round(entry_price, 2),
        "sl": round(stop_loss, 2),
        "tp": round(take_profit, 2),
        "ema_20": round(ema_20, 2),
    }
  except Exception as e:
    print(f"❌ Fehler beim Laden der Daten: {e}")
    return None


def main():
  current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  print(f"\n[{current_time}] Starte H1 Gold-Analyse...")

  data = check_gold_setup()

  if data:
    last_signal = load_last_signal()
    current_signal = data["signal"]

    print(
        f"🔍 Preis: ${data['price']} (Vorher: ${data['prev_price']}) | Signal:"
        f" {current_signal} | Trend: {data['trend']}"
    )

    # Nur senden, wenn ein BUY- oder SELL-Signal vorliegt UND es sich geändert hat
    if current_signal in ("BUY", "SELL") and current_signal != last_signal:
      report = (
          f"<b>📊 H1 GOLD SIGNAL: {current_signal} 📊</b>\n"
          f"-----------------------------------\n"
          f"• <b>Asset:</b> {data['symbol']} ({data['timeframe']})\n"
          f"• <b>Signal:</b> {current_signal}\n"
          f"• <b>Richtung:</b> {data['trend']}\n"
          f"• <b>Empfehlung:</b> {data['trade_advice']}\n\n"
          f"💵 <b>Aktueller Preis:</b> ${data['price']} (Vorher:"
          f" ${data['prev_price']})\n"
          f"🎯 <b>Einstiegspreis:</b> ${data['entry']}\n"
          f"🛑 <b>Stop-Loss (SL):</b> ${data['sl']}\n"
          f"🎯 <b>Take-Profit (TP):</b> ${data['tp']}\n\n"
          f"• <b>EMA 20:</b> ${data['ema_20']}\n"
          f"🕒 <b>Zeit:</b> {current_time}"
      )
      send_telegram_message(report)
      save_last_signal(current_signal)
    elif current_signal == "NEUTRAL":
      print("ℹ️ Aktuell neutral – kein BUY/SELL-Signal gesendet.")
      save_last_signal("NEUTRAL")
    else:
      print(f"ℹ️ Signal '{current_signal}' bereits gesendet – keine Doppelmeldung.")
  else:
    print("⚠️ Konnte keine Daten abrufen.")
    send_telegram_message(
        "⚠️ H1 Gold-Bot: Warnung - Konnte keine Marktdaten abrufen."
    )
if __name__ == "__main__":
  main()