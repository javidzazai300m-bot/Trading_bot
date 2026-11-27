from datetime import datetime
import json
import os
import pandas as pd
import requests
import yfinance as yf

# --- ZUGANGSDATEN AUS SICHEREN VARIABLEN LADEN ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "last_signal_state.json")

# --- YAHOO FINANCE TICKER ---
GOLD_TICKER = "GC=F"  # Gold Futures (alternativ XAUUSD=X)
DXY_TICKER = "DX-Y.NYB"  # US Dollar Index (DXY)
US10Y_TICKER = "^TNX"  # 10-jährige US-Staatsanleihen Rendite (US10Y)

# --- SIGNAL-EINSTELLUNGEN ---
# 2 = mindestens 2 aus 3 Faktoren müssen passen (z. B. Gold steigt + DXY fällt)
# 3 = alle 3 Faktoren müssen gleichzeitig passen (strenger, seltener)
MIN_CONFIRMATIONS = 2
PRICE_UPDATE_THRESHOLD = 15.0  # Zusätzliche Meldung bei >= 15 $ Kursänderung


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


def load_last_state():
  """Lädt den zuletzt gespeicherten Signal- und Preisstatus."""
  if os.path.exists(STATE_FILE):
    try:
      with open(STATE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return {
            "last_signal": data.get("last_signal"),
            "last_price": data.get("last_price"),
        }
    except Exception:
      return {"last_signal": None, "last_price": None}
  return {"last_signal": None, "last_price": None}


def save_last_state(signal, price):
  """Speichert das aktuelle Signal und den letzten Preis."""
  try:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
      json.dump(
          {
              "last_signal": signal,
              "last_price": price,
              "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          },
          f,
          indent=2,
      )
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


def download_m30_data(ticker, period="10d", interval="30m"):
  """Lädt M30-Daten für ein Symbol und bereinigt MultiIndex-Spalten."""
  df = yf.download(ticker, period=period, interval=interval, progress=False)
  if df is None or df.empty:
    return pd.DataFrame()
  if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
  df = df.dropna(subset=["Close", "High", "Low"])
  return df


def analyze_trend(df):
  """Analysiert den Trend auf Basis der letzten abgeschlossenen M30-Kerze (iloc[-2])."""
  if df.empty or len(df) < 26:
    return None

  df = df.copy()
  df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

  # iloc[-2] = letzte abgeschlossene 30m-Kerze (vermeidet Fehlsignale durch laufende Kerze)
  close_closed = float(df["Close"].iloc[-2])
  prev_closed = float(df["Close"].iloc[-3])
  ema_closed = float(df["EMA_20"].iloc[-2])
  ema_prev = float(df["EMA_20"].iloc[-3])

  if any(pd.isna(x) for x in (close_closed, prev_closed, ema_closed, ema_prev)):
    return None

  # Bullisch: Kurs über EMA-20 und (EMA steigt oder Momentum nach oben)
  bullish = (close_closed > ema_closed) and (
      ema_closed >= ema_prev or close_closed > prev_closed
  )
  # Bearisch: Kurs unter EMA-20 und (EMA fällt oder Momentum nach unten)
  bearish = (close_closed < ema_closed) and (
      ema_closed <= ema_prev or close_closed < prev_closed
  )

  return {
      "bullish": bullish,
      "bearish": bearish,
      "close": close_closed,
      "ema_20": ema_closed,
  }


def check_gold_signal():
  """Ermittelt ein BUY-, SELL- oder NEUTRAL-Signal auf M30 inkl. Preis, SL und TP."""
  print("🔄 Lade M30-Marktdaten für Gold, DXY und US10Y...")
  try:
    df_gold = download_m30_data(GOLD_TICKER)
    df_dxy = download_m30_data(DXY_TICKER)
    df_us10y = download_m30_data(US10Y_TICKER)

    gold_trend = analyze_trend(df_gold)
    dxy_trend = analyze_trend(df_dxy)
    us10y_trend = analyze_trend(df_us10y)

    if not gold_trend or not dxy_trend or not us10y_trend:
      print("⚠️ Zu wenig gültige M30-Daten für Gold, DXY oder US10Y geladen.")
      return None

    df_gold = df_gold.copy()
    df_gold["ATR"] = calculate_atr(df_gold)

    current_price = float(df_gold["Close"].iloc[-1])
    gold_atr = float(df_gold["ATR"].iloc[-2])

    if pd.isna(current_price) or pd.isna(gold_atr) or gold_atr <= 0:
      print("⚠️ Gold-Preis oder M30-ATR ist ungültig.")
      return None

    ts = df_gold.index[-1]
    price_time = (
        ts.tz_convert("Europe/Berlin").strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(ts, "tzinfo") and ts.tzinfo is not None
        else str(ts)
    )

    # Für Gold-BUY: Gold steigt (bullish), DXY fällt (bearish), US10Y fällt (bearish)
    buy_votes = sum([
        gold_trend["bullish"],
        dxy_trend["bearish"],
        us10y_trend["bearish"],
    ])

    # Für Gold-SELL: Gold fällt (bearish), DXY steigt (bullish), US10Y steigt (bullish)
    sell_votes = sum([
        gold_trend["bearish"],
        dxy_trend["bullish"],
        us10y_trend["bullish"],
    ])

    entry_price = current_price

    if buy_votes >= MIN_CONFIRMATIONS and buy_votes > sell_votes:
      signal = "BUY"
      stop_loss = round(entry_price - (1.5 * gold_atr), 2)
      take_profit = round(entry_price + (3.0 * gold_atr), 2)
    elif sell_votes >= MIN_CONFIRMATIONS and sell_votes > buy_votes:
      signal = "SELL"
      stop_loss = round(entry_price + (1.5 * gold_atr), 2)
      take_profit = round(entry_price - (3.0 * gold_atr), 2)
    else:
      signal = "NEUTRAL"
      stop_loss = None
      take_profit = None

    return {
        "symbol": "Gold Futures (GC=F) [M30]",
        "signal": signal,
        "buy_votes": buy_votes,
        "sell_votes": sell_votes,
        "current_price": round(current_price, 2),
        "entry_price": round(entry_price, 2),
        "sl": stop_loss,
        "tp": take_profit,
        "price_time": price_time,
    }
  except Exception as e:
    print(f"❌ Fehler beim Laden/Analysieren der M30-Daten: {e}")
    return None


def main():
  current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  print(f"\n[{current_time}] Starte M30 Gold-Signal-Prüfung (BUY / SELL / NEUTRAL)...")

  data = check_gold_signal()

  if data is None:
    print("⚠️ Konnte keine Daten abrufen.")
    send_telegram_message(
        "⚠️ Gold-Bot (M30): Warnung – Konnte Marktdaten nicht abrufen."
    )
    return

  state = load_last_state()
  last_signal = state["last_signal"]
  last_price = state["last_price"]

  signal = data["signal"]
  current_price = data["current_price"]

  sl_text = f"${data['sl']}" if data["sl"] is not None else "–"
  tp_text = f"${data['tp']}" if data["tp"] is not None else "–"
  score_text = f"BUY {data['buy_votes']}/3 | SELL {data['sell_votes']}/3"

  print(
      f"🔍 Signal: {signal} ({score_text}) | Aktuell: ${current_price} "
      f"({data['price_time']}) | Einstieg: ${data['entry_price']} | "
      f"SL: {sl_text} | TP: {tp_text}"
  )

  price_moved_significantly = (
      last_price is not None
      and abs(current_price - float(last_price)) >= PRICE_UPDATE_THRESHOLD
  )

  if signal != last_signal or price_moved_significantly:
    emoji_map = {"BUY": "🟢", "SELL": "🔴", "NEUTRAL": "🟡"}
    emoji = emoji_map.get(signal, "⚪")
    reason_note = (
        " (Kursbewegung)"
        if signal == last_signal and price_moved_significantly
        else ""
    )

    report = (
        f"{emoji} <b>GOLD SIGNAL (M30): {signal}</b>{reason_note}\n"
        f"Asset: {data['symbol']}\n"
        f"Bestätigung: <b>{score_text}</b>\n"
        f"Aktueller Preis: <b>${current_price}</b>\n"
        f"Einstiegspreis: <b>${data['entry_price']}</b>\n"
        f"Stop-Loss (SL): <b>{sl_text}</b>\n"
        f"Take-Profit (TP): <b>{tp_text}</b>\n"
        f"Kurszeit: {data['price_time']}\n"
        f"Bot-Zeit: {current_time}"
    )
    send_telegram_message(report)
    save_last_state(signal, current_price)
  else:
    print(
        f"ℹ️ Signal '{signal}' unverändert (${current_price}) – keine Doppelmeldung."
    )


if __name__ == "__main__":
  main()
