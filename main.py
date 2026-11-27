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
GOLD_TICKER = "GC=F"        # Gold Futures (alternativ XAUUSD=X)
DXY_TICKER = "DX-Y.NYB"     # US Dollar Index (DXY)
US10Y_TICKER = "^TNX"       # 10-jährige US-Staatsanleihen Rendite (US10Y)


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
  """Prüft für DXY oder US10Y, ob der Wert im H1-Chart steigt oder fällt."""
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

  change_pct = ((current_val - prev_val) / prev_val) * 100

  is_falling = (current_val < prev_val) and (
      ema_20 < ema_20_prev or current_val < ema_20
  )
  is_rising = (current_val > prev_val) and (
      ema_20 > ema_20_prev or current_val > ema_20
  )

  if is_falling:
    direction = "FALLEND 🔴"
  elif is_rising:
    direction = "STEIGEND 🟢"
  else:
    direction = "NEUTRAL 🟡"

  return {
      "current": current_val,
      "prev": prev_val,
      "change_pct": round(change_pct, 2),
      "ema_20": ema_20,
      "is_falling": is_falling,
      "is_rising": is_rising,
      "direction": direction,
  }


def check_macro_gold_setup():
  """Analysiert DXY und US10Y im H1-Chart und leitet das Gold-Signal ab."""
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
    gold_price = float(df_gold["Close"].iloc[-1])
    gold_prev = float(df_gold["Close"].iloc[-2])
    gold_atr = float(df_gold["ATR"].iloc[-1])

    if pd.isna(gold_price) or pd.isna(gold_atr):
      print("⚠️ Gold-Preis oder ATR ist NaN.")
      return None

    # --- MAKRO-LOGIK: DXY + US10Y ---
    # Beide fallen -> Rückenwind für Gold -> BUY
    if dxy["is_falling"] and us10y["is_falling"]:
      trend = "BULLISCH FÜR GOLD 🟢 (DXY & US10Y fallen)"
      signal = "BUY"
      trade_advice = "JA (DXY fällt + US10Y fällt → BUY Signal)"
      entry_price = gold_price
      stop_loss = entry_price - (1.5 * gold_atr)
      take_profit = entry_price + (3.0 * gold_atr)

    # Beide steigen -> Gegenwind für Gold -> SELL
    elif dxy["is_rising"] and us10y["is_rising"]:
      trend = "BÄRISCH FÜR GOLD 🔴 (DXY & US10Y steigen)"
      signal = "SELL"
      trade_advice = "JA (DXY steigt + US10Y steigt → SELL Signal)"
      entry_price = gold_price
      stop_loss = entry_price + (1.5 * gold_atr)
      take_profit = entry_price - (3.0 * gold_atr)

    # Gemischte Signale -> Abwarten
    else:
      trend = "GEMISCHT / UNKLAR 🟡"
      signal = "NEUTRAL"
      trade_advice = "NEIN (DXY und US10Y laufen nicht gleich)"
      entry_price = gold_price
      stop_loss = 0
      take_profit = 0

    return {
        "symbol": "Gold Futures (GC=F)",
        "timeframe": "H1",
        "trend": trend,
        "signal": signal,
        "trade_advice": trade_advice,
        "gold_price": round(gold_price, 2),
        "gold_prev": round(gold_prev, 2),
        "entry": round(entry_price, 2),
        "sl": round(stop_loss, 2),
        "tp": round(take_profit, 2),
        "dxy_val": round(dxy["current"], 2),
        "dxy_pct": dxy["change_pct"],
        "dxy_dir": dxy["direction"],
        "us10y_val": round(us10y["current"], 3),
        "us10y_pct": us10y["change_pct"],
        "us10y_dir": us10y["direction"],
    }
  except Exception as e:
    print(f"❌ Fehler beim Laden/Analysieren der Daten: {e}")
    return None


def main():
  current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  print(f"\n[{current_time}] Starte H1 Makro-Analyse (DXY + US10Y → Gold)...")

  data = check_macro_gold_setup()

  if data:
    last_signal = load_last_signal()
    current_signal = data["signal"]

    print(
        f"🔍 DXY: {data['dxy_val']} ({data['dxy_dir']}) | "
        f"US10Y: {data['us10y_val']}% ({data['us10y_dir']}) | "
        f"Gold: ${data['gold_price']} → Signal: {current_signal}"
    )

    # Nur senden, wenn BUY oder SELL vorliegt UND sich das Signal geändert hat
    if current_signal in ("BUY", "SELL") and current_signal != last_signal:
      report = (
          f"<b>📊 H1 MAKRO-GOLD SIGNAL: {current_signal} 📊</b>\n"
          f"-----------------------------------\n"
          f"• <b>Asset:</b> {data['symbol']} ({data['timeframe']})\n"
          f"• <b>Signal:</b> {current_signal}\n"
          f"• <b>Makro-Lage:</b> {data['trend']}\n"
          f"• <b>Empfehlung:</b> {data['trade_advice']}\n\n"
          f"💵 <b>DXY:</b> {data['dxy_val']} ({data['dxy_pct']:+}%)"
          f" [{data['dxy_dir']}]\n"
          f"📈 <b>US10Y:</b> {data['us10y_val']}% ({data['us10y_pct']:+}%)"
          f" [{data['us10y_dir']}]\n\n"
          f"🥇 <b>Gold Preis:</b> ${data['gold_price']} (Vorher:"
          f" ${data['gold_prev']})\n"
          f"🎯 <b>Einstiegspreis:</b> ${data['entry']}\n"
          f"🛑 <b>Stop-Loss (SL):</b> ${data['sl']}\n"
          f"🎯 <b>Take-Profit (TP):</b> ${data['tp']}\n\n"
          f"🕒 <b>Zeit:</b> {current_time}"
      )
      send_telegram_message(report)
      save_last_signal(current_signal)
    elif current_signal == "NEUTRAL":
      print("ℹ️ DXY & US10Y uneinheitlich – kein BUY/SELL-Signal gesendet.")
      save_last_signal("NEUTRAL")
    else:
      print(f"ℹ️ Signal '{current_signal}' bereits gesendet – keine Doppelmeldung.")
  else:
    print("⚠️ Konnte keine Daten abrufen.")
    send_telegram_message(
        "⚠️ H1 Gold-Bot: Warnung - Konnte DXY/US10Y/Gold-Daten nicht abrufen."
    )


if __name__ == "__main__":
  main()