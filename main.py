from datetime import datetime, timezone
import os
import pandas as pd
import requests
import yfinance as yf

# --- ZUGANGSDATEN AUS SICHEREN VARIABLEN LADEN ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(message_text):
  """Sendet die Nachricht an deinen Telegram-Chat (HTML vermeidet Sonderzeichen-Fehler)."""
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
  """Analysiert Gold (GC=F) im H1-Zeitfenster auf BUY- und SELL-Setups."""
  ticker_symbol = "GC=F"  # Gold Futures
  interval = "1h"  # H1 Zeitfenster
  period = "14d"  # 14 Tage H1-Daten (~336 Kerzen)

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
    if df.empty or not required_cols.issubset(df.columns) or len(df) < 60:
      print(f"⚠️ Zu wenig oder unvollständige Daten geladen (Zeilen: {len(df)})")
      return None

    df = df.dropna(subset=["Open", "High", "Low", "Close"]).copy()

    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["ATR"] = calculate_atr(df, period=14)

    last_idx = df.index[-1]
    prev_close = float(df["Close"].iloc[-2])
    last_open = float(df["Open"].iloc[-1])
    last_high = float(df["High"].iloc[-1])
    last_low = float(df["Low"].iloc[-1])
    current_price = float(df["Close"].iloc[-1])

    ema_20 = float(df["EMA_20"].iloc[-1])
    ema_50 = float(df["EMA_50"].iloc[-1])
    prev_ema_20 = float(df["EMA_20"].iloc[-2])
    atr = float(df["ATR"].iloc[-1])

    if (
        pd.isna(current_price)
        or pd.isna(ema_20)
        or pd.isna(ema_50)
        or pd.isna(atr)
        or atr <= 0
    ):
      print("⚠️ Indikatoren enthalten ungültige oder NaN-Werte.")
      return None

    # Kerzenzeit normalisieren für saubere Anzeige
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

    # --- KLARE TREND- & IMPULS-LOGIK ---
    # Steigendes Gold -> BUY (Long)
    bullish_trend = (
        (current_price > ema_20)
        and (ema_20 > ema_50)
        and (ema_20 >= prev_ema_20)
    )
    bullish_momentum = (current_price > last_open) and (
        current_price >= prev_close
    )

    # Fallendes Gold -> SELL (Short)
    bearish_trend = (
        (current_price < ema_20)
        and (ema_20 < ema_50)
        and (ema_20 <= prev_ema_20)
    )
    bearish_momentum = (current_price < last_open) and (
        current_price <= prev_close
    )

    entry_price = current_price

    if bullish_trend and bullish_momentum:
      signal = "BUY (LONG)"
      direction_text = "Gold steigt – Aufwärtssetup aktiv"
      sl_price = entry_price - (1.5 * atr)
      tp_price = entry_price + (3.0 * atr)  # Chance-Risiko-Verhältnis ~ 1:2
    elif bearish_trend and bearish_momentum:
      signal = "SELL (SHORT)"
      direction_text = "Gold fällt – Abwärtssetup aktiv"
      sl_price = entry_price + (1.5 * atr)
      tp_price = entry_price - (3.0 * atr)  # Chance-Risiko-Verhältnis ~ 1:2
    else:
      signal = "KEIN SIGNAL (WARTEN)"
      direction_text = "Kein klarer Trend-/Impuls-Ausbruch im H1"
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
        "ema_20": round(ema_20, 2),
        "ema_50": round(ema_50, 2),
        "atr": round(atr, 2),
        "candle_time": candle_time_str,
        "candle_age_hours": (
            round(candle_age_hours, 1) if candle_age_hours is not None else None
        ),
        "last_high": round(last_high, 2),
        "last_low": round(last_low, 2),
    }

  except Exception as e:
    print(f"❌ Fehler beim Laden der Daten: {e}")
    return None


def main():
  now_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  print(f"\n[{now_local}] Starte H1 Gold-Analyse...")

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
        f" {data['candle_age_hours']}h alt (evtl. Markt geschlossen oder"
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
      f"EMA 20: ${data['ema_20']:.2f} | EMA 50: ${data['ema_50']:.2f} | ATR:"
      f" ${data['atr']:.2f}\n"
      f"🕯️ H1-Kerze: {data['candle_time']}\n"
      f"🕒 Bot-Zeit: {now_local}"
      f"{stale_warning}"
  )

  send_telegram_message(message)


if __name__ == "__main__":
  main()
