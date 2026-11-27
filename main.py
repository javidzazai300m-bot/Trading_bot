from datetime import datetime
import os
import pandas as pd
import requests
import yfinance as yf


def calculate_atr(df: pd.DataFrame, period: int = 12) -> pd.Series:
  """Berechnet die Average True Range (ATR)."""
  high_low = df["High"] - df["Low"]
  high_close = (df["High"] - df["Close"].shift()).abs()
  low_close = (df["Low"] - df["Close"].shift()).abs()
  ranges = pd.concat([high_low, high_close, low_close], axis=1)
  true_range = ranges.max(axis=1)
  return true_range.rolling(period).mean()


def get_spot_gold_data(
    ticker_symbol: str = "XAUUSD=X", interval: str = "15m", period: str = "5d"
) -> pd.DataFrame | None:
  """Lädt Spot-Gold-Daten (XAUUSD) über Yahoo Finance."""
  print(f"🔄 Lade Marktdaten für {ticker_symbol} ({interval})...")
  try:
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
    })

    ticker = yf.Ticker(ticker_symbol, session=session)
    df = ticker.history(period=period, interval=interval)

    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    if df.empty or len(df) < 50:
      print(f"⚠️ Zu wenig Daten geladen (Zeilen: {len(df)})")
      return None

    return df
  except Exception as e:
    print(f"❌ Fehler beim Laden der Daten: {e}")
    return None


def check_gold_setup() -> dict | None:
  """Analysiert Spot-Gold (XAUUSD) und berechnet Trend, Einstieg, SL und TP."""
  df = get_spot_gold_data(ticker_symbol="XAUUSD=X", interval="15m", period="5d")
  if df is None:
    return None

  df = df.copy()
  df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
  df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
  df["ATR"] = calculate_atr(df, period=12)

  current_price = float(df["Close"].iloc[-1])
  ema_20 = float(df["EMA_20"].iloc[-1])
  ema_50 = float(df["EMA_50"].iloc[-1])
  atr = float(df["ATR"].iloc[-1])

  if (
      pd.isna(current_price)
      or pd.isna(ema_20)
      or pd.isna(ema_50)
      or pd.isna(atr)
  ):
    print("⚠️ Indikatoren enthalten NaN-Werte.")
    return None

  entry_price = current_price

  if current_price > ema_20 and ema_20 > ema_50:
    trend = "BULLISH 🟢"
    signal = "BUY (LONG)"
    trade_advice = "JA (Aufwärtstrend im M15 - Long Einstieg)"
    stop_loss = entry_price - (1.5 * atr)
    take_profit = entry_price + (3.0 * atr)
  elif current_price < ema_20 and ema_20 < ema_50:
    trend = "BEARISH 🔴"
    signal = "SELL (SHORT)"
    trade_advice = "JA (Abwärtstrend im M15 - Short Einstieg)"
    stop_loss = entry_price + (1.5 * atr)
    take_profit = entry_price - (3.0 * atr)
  else:
    trend = "NEUTRAL / KORREKTUR 🟡"
    signal = "KEIN KLARES SIGNAL (NEUTRAL)"
    trade_advice = "NEIN (Warten auf klaren Trend / Seitwärtsphase)"
    stop_loss = 0.0
    take_profit = 0.0

  return {
      "symbol": "Gold Spot (XAUUSD)",
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


def send_telegram_message(message_text: str) -> None:
  """Sendet die Nachricht an Telegram über Umgebungsvariablen (Secrets)."""
  token = os.getenv("TELEGRAM_TOKEN")
  chat_id = os.getenv("TELEGRAM_CHAT_ID")

  if not token or not chat_id:
    print("ℹ️ Keine Telegram-Secrets gesetzt – Ausgabe nur in der Konsole.")
    return

  url = f"https://api.telegram.org/bot{token}/sendMessage"
  payload = {
      "chat_id": chat_id,
      "text": message_text,
  }
  try:
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    print("✅ Telegram-Nachricht erfolgreich gesendet.")
  except Exception as e:
    print(f"❌ Telegram-Fehler: {e}")


def format_report(data: dict, current_time: str) -> str:
  """Formatiert den Analysebericht für Konsole und Telegram."""
  report = (
      "\n📊 M15 UPDATE: GOLD
