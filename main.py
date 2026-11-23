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

# --- YAHOO FINANCE TICKER ---
GOLD_TICKER = "GC=F"  # Gold Futures (alternativ XAUUSD=X)
DXY_TICKER = "DX-Y.NYB"  # US Dollar Index (DXY)
US10Y_TICKER = "^TNX"  # 10-jährige US-Staatsanleihen Rendite (US10Y)


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


def download_h1_data(ticker, period="30d", interval="1h"):
  """Lädt H1-Daten für ein Symbol und bereinigt MultiIndex-Spalten."""
  df = yf.download(ticker, period=period, interval=interval, progress=False)
  if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
  return df


def analyze_direction(df):
  """Prüft für DXY oder US10Y, ob der Wert im H1-Chart steigt, fällt oder neutral ist."""
  if df.empty or len(df) < 25:
    return None

  df = df.copy()
  df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

  current_val = float(df["Close"].iloc[-1])
  prev_val = float(df["Close"].iloc[-2])
  ema_20 = float(df["EMA_20"].iloc[-1])
  ema_20_prev = float(df["EMA_20"].iloc[-2])

  if pd.isna(current_val) or pd.isna(prev_val) or pd.isna(ema_20):
    return None

  is_falling = (current_val < prev_val) and (
      ema_20 < ema_20_prev or current_val < ema_20
  )
  is_rising = (current_val > prev_val) and (
      ema_20 > ema_20_prev or current_val > ema_20
  )

  return {
      "is_falling": is_falling,
      "is_rising": is_rising,
  }


def check_gold_signal():
  """Ermittelt ein BUY-, SELL- oder NEUTRAL-Signal inkl. aktuellem Preis, Einstieg, SL und TP."""
  print("🔄 Lade H1-Marktdaten für DXY, US10Y und Gold...")
  try:
    df_dxy = download_h1_data(DXY_TICKER)
    df_us10y = download_h1_data(US10Y_TICKER)
    df_gold = download_h1_data(GOLD_TICKER)

    dxy = analyze_direction(df_dxy)
    us10y = analyze_direction(df_us10y)

    if not dxy or not us10y:
      print("⚠️ Zu wenig Daten für DXY oder US10Y geladen.")
      return None

    if df_gold.empty or len(df_gold) < 25:
      print("⚠️ Zu wenig Gold-Daten geladen.")
      return None

    df_gold["ATR"] = calculate_atr(df_gold)
    current_price = float(df_gold["Close"].iloc[-1])
    gold_atr = float(df_gold["ATR"].iloc[-1])

    if pd.isna(current_price) or pd.isna(gold_atr):
      print("⚠️ Gold-Preis oder ATR ist NaN.")
      return None

    entry_price = current_price

    # DXY & US10Y fallen -> BUY
    if dxy["is_falling"] and us10y["is_falling"]:
      signal = "BUY"
      stop_loss = round(entry_price - (1.5 * gold_atr), 2)
      take_profit = round(entry_price + (3.0 * gold_atr), 2)

    # DXY & US10Y steigen -> SELL
    elif dxy["is_rising"] and us10y["is_rising"]:
      signal = "SELL"
      stop_loss = round(entry_price + (1.5 * gold_atr), 2)
      take_profit = round(entry_price - (3.0 * gold_atr), 2)

    # Alles andere -> NEUTRAL
    else:
      signal = "NEUTRAL"
      stop_loss = None
      take_profit = None

    return {
        "symbol": "Gold Futures (GC=F)",
        "signal": signal,
        "current_price": round(current_price, 2),
        "entry_price": round(entry_price, 2),
        "sl": stop_loss,
        "tp": take_profit,
    }
  except Exception as e:
    print(f"❌ Fehler beim Laden/Analysieren der Daten: {e}")
    return None


def main():
  current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  print(f"\n[{current_time}] Starte H1 Gold-Signal-Prüfung (BUY / SELL / NEUTRAL)...")

  data = check_gold_signal()

  if data:
    last_signal = load_last_signal()
    signal = data["signal"]

    sl_text = f"${data['sl']}" if data["sl"] is not None else "–"
    tp_text = f"${data['tp']}" if data["tp"] is not None else "–"

    print(
        f"🔍 Signal: {signal} | Aktuell: ${data['current_price']} | "
        f"Einstieg: ${data['entry_price']} | SL: {sl_text} | TP: {tp_text}"
    )

    if signal != last_signal:
      emoji_map = {"BUY": "🟢", "SELL": "🔴", "NEUTRAL": "🟡"}
      emoji = emoji_map.get(signal, "⚪")

      report = (
          f"{emoji} <b>GOLD SIGNAL: {signal}</b>\n"
          f"Asset: {data['symbol']}\n"
          f"Aktueller Preis: <b>${data['current_price']}</b>\n"
          f"Einstiegspreis: <b>${data['entry_price']}</b>\n"
          f"Stop-Loss (SL): <b>{sl_text}</b>\n"
          f"Take-Profit (TP): <b>{tp_text}</b>\n"
          f"Zeit: {current_time}"
      )
      send_telegram_message(report)
      save_last_signal(signal)
    else:
      print(f"ℹ️ Signal '{signal}' ist bereits aktiv – keine Doppelmeldung.")
  else:
    print("⚠️ Konnte keine Daten abrufen.")
    send_telegram_message(
        "⚠️ Gold-Bot: Warnung – Konnte Marktdaten nicht abrufen."
    )


if __name__ == "__main__":
  main()
