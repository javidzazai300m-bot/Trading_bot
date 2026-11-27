from datetime import datetime, timezone
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
      "parse_mode": "HTML",
      "disable_web_page_preview": True,
  }
  try:
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    print("✅ Telegram-Nachricht erfolgreich gesendet.")
  except Exception as e:
    print(f"❌ Telegram-Fehler: {e}")


def calculate_atr(df, period=14):
  """Berechnet die Average True Range (ATR)."""
  high_low = df["High"] - df["Low"]
  high_close = (df["High"] - df["Close"].shift()).abs()
  low_close = (df["Low"] - df["Close"].shift()).abs()
  ranges = pd.concat([high_low, high_close, low_close], axis=1)
  true_range = ranges.max(axis=1)
  return true_range.rolling(period).mean()


def check_gold_setup():
  """Analysiert Gold (GC=F) im H1-Zeitfenster ohne EMA."""
  ticker_symbol = "GC=F"
  interval = "1h"
  period = "10d"

  print("🔄 Lade H1-Marktdaten von Yahoo Finance...")
  try:
    df = yf.download(
        tickers=ticker_symbol,
        period=period,
        interval=interval,
        progress=False,
        auto_adjust=False,
    )

    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    required_cols = {"Open", "High", "Low", "Close"}
    if df.empty or not required_cols.issubset(df.columns) or len(df) < 20:
      print(f"⚠️ Zu wenig oder unvollständige Daten geladen (Zeilen: {len(df)})")
      return None

    df = df.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    df["ATR"] = calculate_atr(df, period=14)

    last_idx = df.index[-1]
    prev_high = float(df["High"].iloc[-2])
    prev_low = float(df["Low"].iloc[-2])
    prev_close = float(df["Close"].iloc[-2])

    last_open = float(df["Open"].iloc[-1])
    current_price = float(df["Close"].iloc[-1])
    atr = float(df["ATR"].iloc[-1])

    if pd.isna(current_price) or pd.isna(atr) or atr <= 0:
      print("⚠️ Preis oder ATR ungültig / NaN.")
      return None

    if hasattr(last_idx, "tzinfo") and last_idx.tzinfo is not None:
      candle_time_str = last_idx.tz_convert("Europe/Berlin").strftime(
          "%Y-%m-%d %H:%M"
      )
      now_utc = datetime.now(timezone.utc)
      candle_age_hours = (
          now_utc - last_idx.tz_convert(timezone.utc)
      ).total_seconds() / 3600.0
    else:
      candle_time_str = str(last_idx)
      candle_age_hours = None

    print(
        f"🕒 Letzte H1-Kerze: {candle_time_str} | Close: {current_price:.2f} |"
        f" ATR: {atr:.2f}"
    )

    # --- SIGNAL-LOGIK OHNE EMA ---
    # BUY: Gold steigt über das vorherige H1-Hoch & Schlusskurs und grüne Kerze
    buy_signal = (
        (current_price > prev_high)
        and (current_price > prev_close)
        and (current_price > last_open)
    )

    # SELL: Gold fällt unter das vorherige H1-Tief & Schlusskurs und rote Kerze
    sell_signal = (
        (current_price < prev_low)
        and (current_price < prev_close)
        and (current_price < last_open)
    )

    entry_price = current_price

    if buy_signal:
      signal = "BUY (LONG)"
      direction_text = "Gold steigt – Ausbruch über vorheriges H1-Hoch"
      sl_price = entry_price - (1.5 * atr)
      tp_price = entry_price + (3.0 * atr)
    elif sell_signal:
      signal = "SELL (SHORT)"
      direction_text = "Gold fällt – Bruch unter vorheriges H1-Tief"
      sl_price = entry_price + (1.5 * atr)
      tp_price = entry_price - (3.0 * atr)
    else:
      signal = "KEIN SIGNAL (WARTEN)"
      direction_text = "Noch kein klarer Ausbruch über/unter die letzte Kerze"
      sl_price = None
      tp_price = None

    return {
        "symbol": "Gold Futures (GC=F)",
        "timeframe": "H1",
        "signal": signal,
        "direction_text": direction_text,
        "price": round(current_price, 2),
        "entry": round(entry_price, 2),
        "sl": round(sl_price, 2) if sl_price is not None else None,
        "tp": round(tp_price, 2) if tp_price is not None else None,
        "prev_high": round(prev_high, 2),
        "prev_low": round(prev_low, 2),
        "atr": round(atr, 2),
        "candle_time": candle_time_str,
        "candle_age_hours": (
            round(candle_age_hours, 1) if candle_age_hours is not None else None
        ),
    }

  except Exception as e:
    print(f"❌ Fehler beim Laden der Daten: {e}")
    return None


def main():
  now_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  print(f"\n[{now_local}] Starte H1 Gold-Analyse (ohne EMA)...")

  data = check_gold_setup()

  if not data:
    print("⚠️ Konnte keine Daten abrufen.")
    send_telegram_message(
        "⚠️ <b>H1 Gold-Bot:</b> Konnte aktuell keine Marktdaten abrufen."
    )
    return

  print(
      f"🔍 Signal: {data['signal']} | Preis: ${data['price']} | SL:"
      f" {data['sl']} | TP: {data['tp']}"
  )

  stale_warning = ""
  if data["candle_age_hours"] is not None and data["candle_age_hours"] > 3.0:
    stale_warning = (
        "\n⚠️ <i>Hinweis: Letzte Kerze ist über"
        f" {data['candle_age_hours']}h alt (Markt evtl. geschlossen oder"
        " Yahoo-Verzögerung).</i>"
    )

  if data["signal"].startswith("BUY"):
    header = "🟢 <b>GOLD BUY SIGNAL (H1)</b>"
  elif data["signal"].startswith("SELL"):
    header = "🔴 <b>GOLD SELL SIGNAL (H1)</b>"
  else:
    header = "🟡 <b>GOLD H1 UPDATE (KEIN TRADE)</b>"

  message = (
      f"{header}\n"
      f"━━━━━━━━━━━━━━━━━━━━\n"
      f"📌 <b>Status:</b> {data['signal']}\n"
      f"📈 <b>Lage:</b> {data['direction_text']}\n\n"
      f"💵 <b>Aktueller Preis:</b> ${data['price']:.2f}\n"
      f"🎯 <b>Einstiegspreis:</b> ${data['entry']:.2f}\n"
  )

  if data["sl"] is not None and data["tp"] is not None:
    message += (
        f"🛑 <b>SL Preis:</b> ${data['sl']:.2f}\n"
        f"🏆 <b>TP Preis:</b> ${data['tp']:.2f}\n\n"
    )
  else:
    message += (
        "🛑 <b>SL Preis:</b> — (kein Setup)\n"
        "🏆 <b>TP Preis:</b> — (kein Setup)\n\n"
    )

  message += (
      f"Vorheriges Hoch/Tief: ${data['prev_high']:.2f} /"
      f" ${data['prev_low']:.2f} | ATR: ${data['atr']:.2f}\n"
      f"🕯️ H1-Kerze: {data['candle_time']}\n"
      f"🕒 Bot-Zeit: {now_local}"
      f"{stale_warning}"
  )

  send_telegram_message(message)


if __name__ == "__main__":
  main()
