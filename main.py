from datetime import datetime, timezone
import os
import pandas as pd
import requests
import yfinance as yf

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(message_text):
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
  high_low = df["High"] - df["Low"]
  high_close = (df["High"] - df["Close"].shift()).abs()
  low_close = (df["Low"] - df["Close"].shift()).abs()
  ranges = pd.concat([high_low, high_close, low_close], axis=1)
  true_range = ranges.max(axis=1)
  return true_range.rolling(period).mean()


def fetch_h1_data(symbol, period="10d"):
  df = yf.download(
      tickers=symbol,
      period=period,
      interval="1h",
      progress=False,
      auto_adjust=False,
  )
  if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

  required_cols = {"Open", "High", "Low", "Close"}
  if df.empty or not required_cols.issubset(df.columns):
    return None, None

  df = df.dropna(subset=["Open", "High", "Low", "Close"]).copy()
  if len(df) < 20:
    return None, None

  last_idx = df.index[-1]
  if hasattr(last_idx, "tzinfo") and last_idx.tzinfo is not None:
    candle_time_str = last_idx.tz_convert("Europe/Berlin").strftime(
        "%Y-%m-%d %H:%M"
    )
    now_utc = datetime.now(timezone.utc)
    age_hours = (
        now_utc - last_idx.tz_convert(timezone.utc)
    ).total_seconds() / 3600.0
  else:
    candle_time_str = str(last_idx)
    age_hours = None

  return df, {
      "symbol": symbol,
      "candle_time": candle_time_str,
      "age_hours": round(age_hours, 1) if age_hours is not None else None,
  }


def check_gold_setup():
  """Prüft GC=F und wechselt bei veralteter Kerze automatisch auf XAUUSD=X."""
  print("🔄 Lade H1-Marktdaten...")
  try:
    candidates = ["GC=F", "XAUUSD=X"]
    chosen_df = None
    chosen_meta = None

    for sym in candidates:
      df, meta = fetch_h1_data(sym)
      if df is not None and meta is not None:
        print(
            f"ℹ️ {sym} -> Letzte Kerze: {meta['candle_time']} (Alter:"
            f" {meta['age_hours']}h)"
        )
        chosen_df = df
        chosen_meta = meta
        # Sobald eine frische Kerze (<= 2h alt) gefunden ist, direkt verwenden
        if meta["age_hours"] is not None and meta["age_hours"] <= 2.0:
          break

    if chosen_df is None or chosen_meta is None:
      print("⚠️ Keine gültigen Marktdaten geladen.")
      return None

    chosen_df["ATR"] = calculate_atr(chosen_df, period=14)

    prev_high = float(chosen_df["High"].iloc[-2])
    prev_low = float(chosen_df["Low"].iloc[-2])
    prev_close = float(chosen_df["Close"].iloc[-2])

    last_open = float(chosen_df["Open"].iloc[-1])
    current_price = float(chosen_df["Close"].iloc[-1])
    atr = float(chosen_df["ATR"].iloc[-1])

    if pd.isna(current_price) or pd.isna(atr) or atr <= 0:
      print("⚠️ Preis oder ATR ungültig / NaN.")
      return None

    is_stale = (
        chosen_meta["age_hours"] is not None and chosen_meta["age_hours"] > 3.0
    )

    buy_signal = (
        (current_price > prev_high)
        and (current_price > prev_close)
        and (current_price > last_open)
    )
    sell_signal = (
        (current_price < prev_low)
        and (current_price < prev_close)
        and (current_price < last_open)
    )

    entry_price = current_price

    if is_stale:
      signal = "VERALTETE DATEN (KEIN TRADE)"
      direction_text = (
          "Yahoo liefert keine aktuelle H1-Kerze – Preis ggf. eingefroren"
      )
      sl_price = entry_price - (1.5 * atr)
      tp_price = entry_price + (3.0 * atr)
      level_hint = " <i>(Richtwert)</i>"
    elif buy_signal:
      signal = "BUY (LONG)"
      direction_text = "Gold steigt – Ausbruch über vorheriges H1-Hoch"
      sl_price = entry_price - (1.5 * atr)
      tp_price = entry_price + (3.0 * atr)
      level_hint = ""
    elif sell_signal:
      signal = "SELL (SHORT)"
      direction_text = "Gold fällt – Bruch unter vorheriges H1-Tief"
      sl_price = entry_price + (1.5 * atr)
      tp_price = entry_price - (3.0 * atr)
      level_hint = ""
    else:
      signal = "KEIN SIGNAL (WARTEN)"
      direction_text = "Noch kein klarer Ausbruch – Richtwerte auf Basis ATR"
      sl_price = entry_price - (1.5 * atr)
      tp_price = entry_price + (3.0 * atr)
      level_hint = " <i>(Richtwert Long)</i>"

    return {
        "symbol": chosen_meta["symbol"],
        "timeframe": "H1",
        "signal": signal,
        "direction_text": direction_text,
        "price": round(current_price, 2),
        "entry": round(entry_price, 2),
        "sl": round(sl_price, 2),
        "tp": round(tp_price, 2),
        "level_hint": level_hint,
        "prev_high": round(prev_high, 2),
        "prev_low": round(prev_low, 2),
        "atr": round(atr, 2),
        "candle_time": chosen_meta["candle_time"],
        "candle_age_hours": chosen_meta["age_hours"],
        "is_stale": is_stale,
    }

  except Exception as e:
    print(f"❌ Fehler beim Laden der Daten: {e}")
    return None


def main():
  now_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  print(f"\n[{now_local}] Starte H1 Gold-Analyse...")

  data = check_gold_setup()
  if not data:
    send_telegram_message(
        "⚠️ <b>H1 Gold-Bot:</b> Konnte aktuell keine Marktdaten abrufen."
    )
    return

  if data["is_stale"]:
    header = "⚠️ <b>GOLD H1 WARNUNG (ALTE KERZE)</b>"
  elif data["signal"].startswith("BUY"):
    header = "🟢 <b>GOLD BUY SIGNAL (H1)</b>"
  elif data["signal"].startswith("SELL"):
    header = "🔴 <b>GOLD SELL SIGNAL (H1)</b>"
  else:
    header = "🟡 <b>GOLD H1 UPDATE (KEIN TRADE)</b>"

  stale_note = (
      "\n⚠️ <i>Kerze ist"
      f" {data['candle_age_hours']}h alt – bitte Live-Chart prüfen!</i>"
      if data["is_stale"]
      else ""
  )

  message = (
      f"{header}\n"
      f"━━━━━━━━━━━━━━━━━━━━\n"
      f"📌 <b>Status:</b> {data['signal']}\n"
      f"📈 <b>Lage:</b> {data['direction_text']}\n\n"
      f"💵 <b>Aktueller Preis:</b> ${data['price']:.2f}\n"
      f"🎯 <b>Einstiegspreis:</b> ${data['entry']:.2f}\n"
      f"🛑 <b>SL Preis:</b> ${data['sl']:.2f}{data['level_hint']}\n"
      f"🏆 <b>TP Preis:</b> ${data['tp']:.2f}{data['level_hint']}\n\n"
      f"Quelle: {data['symbol']} | Vorheriges Hoch/Tief: ${data['prev_high']:.2f}"
      f" / ${data['prev_low']:.2f}\n"
      f"ATR: ${data['atr']:.2f} | H1-Kerze: {data['candle_time']}\n"
      f"🕒 Bot-Zeit: {now_local}"
      f"{stale_note}"
  )

  send_telegram_message(message)


if __name__ == "__main__":
  main()
