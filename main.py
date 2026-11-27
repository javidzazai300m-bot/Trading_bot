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


def download_h1_data(ticker, period="30d", interval="1h"):
  """Lädt H1-Daten für ein Symbol und bereinigt MultiIndex-Spalten."""
  df = yf.download(ticker, period=period, interval=interval, progress=False)
  if df is None or df.empty:
    return pd.DataFrame()
  if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
  df = df.dropna(subset=["Close", "High", "Low"])
  return df


def get_live_price(ticker):
  """Holt den aktuellsten Preis aus 30-Minuten-Kerzen (30m) inkl. Zeitstempel."""
  try:
    df_30m = yf.download(ticker, period="5d", interval="30m", progress=False)
    if df_30m is None or df_30m.empty:
      return None, None
    if isinstance(df_30m.columns, pd.MultiIndex):
      df_30m.columns = df_30m.columns.get_level_values(0)
    df_30m = df_30m.dropna(subset=["Close"])
    if df_30m.empty:
      return None, None

    last_price = float(df_30m["Close"].iloc[-1])
    if pd.isna(last_price):
      return None, None

    ts = df_30m.index[-1]
    if hasattr(ts, "tzinfo") and ts.tzinfo is not None:
      ts_str = ts.tz_convert("Europe/Berlin").strftime("%Y-%m-%d %H:%M:%S")
    else:
      ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")

    return last_price, ts_str
  except Exception as e:
    print(f"⚠️ Konnte 30m-Kurs nicht laden: {e}")
    return None, None


def analyze_trend(df):
  """Analysiert den Trend auf Basis der letzten abgeschlossenen H1-Kerze (iloc[-2])."""
  if df.empty or len(df) < 26:
    return None

  df = df.copy()
  df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

  # iloc[-2] = letzte abgeschlossene Stunde (vermeidet Fehlsignale durch laufende Kerzen)
  close_closed = float(df["Close"].iloc[-2])
  prev_closed = float(df["Close"].iloc[-3])
  ema_closed = float(df["EMA_20"].iloc[-2])
  ema_prev = float(df["EMA_20"].iloc[-3])

  if any(pd.isna(x) for x in (close_closed, prev_closed, ema_closed, ema_prev)):
    return None

  #
