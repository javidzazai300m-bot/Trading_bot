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


def get_gold_data(interval: str = "1h", period: str = "1mo"):
  """Versucht Spot-Gold (XAUUSD=X) im 1H-Chart und nutzt GC=F als Fallback."""
  candidates = [
      ("XAUUSD=X", "Gold Spot (XAUUSD=X)"),
      ("GC=F", "Gold Futures Fallback (GC=F)"),
  ]

  session = requests.Session()
  session.headers.update({
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
      )
  })

  for symbol, label in candidates:
    print(f"Lade Marktdaten fuer {label} ({interval}, {period})...")
    try:
      ticker = yf.Ticker(symbol, session=session)
      df = ticker.history(period=period, interval=interval)

      if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

      if not df.empty and len(df) >= 50:
        return df, label

      print(f"Zu wenig Daten fuer {symbol} (Zeilen: {len(df)}).")
    except Exception as e:
      print(f"Fehler bei {symbol}: {e}")

  return None, None


def check_gold_setup() -> dict | None:
  """Analysiert Gold auf 1H und berechnet Trend, Einstieg, SL und TP."""
  df, source_label = get_gold_data(interval="1h", period="1mo")
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
    print("Indikatoren enthalten NaN-Werte.")
    return None

  entry_price = current_price

  if current_price > ema_20 and ema_20 > ema_50:
    trend = "BULLISH (Gruen)"
    signal = "BUY (LONG)"
    trade_advice = "JA (Aufwaertstrend im 1H - Long Einstieg)"
    stop_loss = entry_price - (1.5 * atr)
    take_profit = entry_price + (3.0 * atr)
  elif current_price < ema_20 and ema_20 < ema_50:
    trend = "BEARISH (Rot)"
    signal = "SELL (SHORT)"
    trade_advice = "JA (Abwaertstrend im 1H - Short Einstieg)"
    stop_loss = entry_price + (1.5 * atr)
    take_profit = entry_price - (3.0 * atr)
  else:
    trend = "NEUTRAL / KORREKTUR (Gelb)"
    signal = "KEIN KLARES SIGNAL (NEUTRAL)"
    trade_advice = "NEIN (Warten auf klaren Trend / Seitwaertsphase)"
    stop_loss = 0.0
    take_profit = 0.0

  return {
      "symbol": source_label,
      "timeframe": "1H",
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
  """Sendet die Nachricht an Telegram ueber Umgebungsvariablen (Secrets)."""
  token = os.getenv("TELEGRAM_TOKEN")
  chat_id = os.getenv("TELEGRAM_CHAT_ID")

  if not token or not chat_id:
    print("Keine Telegram-Secrets gesetzt - Ausgabe nur in der Konsole.")
    return

  url = f"https://api.telegram.org/bot{token}/sendMessage"
  payload = {
      "chat_id": chat_id,
      "text": message_text,
  }
  try:
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    print("Telegram-Nachricht erfolgreich gesendet.")
  except Exception as e:
    print(f"Telegram-Fehler: {e}")


def format_report(data: dict, current_time: str) -> str:
  """Formatiert den Analysebericht fuer Konsole und Telegram."""
  lines = [
      "",
      "1H UPDATE: GOLD STATUS",
      "-----------------------------------",
      f"- Asset: {data['symbol']} ({data['timeframe']})",
      f"- Signal / Status: {data['signal']}",
      f"- Trend: {data['trend']}",
      f"- Empfehlung: {data['trade_advice']}",
      "",
      f"Aktueller Preis: ${data['price']}",
  ]

  if data["sl"] > 0:
    lines.extend([
        f"Einstiegspreis: ${data['entry']}",
        f"Stop-Loss (SL): ${data['sl']}",
        f"Take-Profit (TP): ${data['tp']}",
        "",
    ])
  else:
    lines.extend([
        f"Einstiegspreis: ${data['entry']} (Kein Trade aktiv)",
        "",
    ])

  lines.extend([
      f"- EMA 20: ${data['ema_20']} | EMA 50: ${data['ema_50']}",
      f"Zeit: {current_time}",
  ])
  return "\n".join(lines)


def main() -> None:
  current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  print(f"\n[{current_time}] Starte 1H Gold-Analyse...")

  data = check_gold_setup()

  if data:
    report = format_report(data, current_time)
    print(report)
    send_telegram_message(report)
  else:
    print("Konnte keine Daten abrufen.")
    send_telegram_message(
        "1H Gold-Bot: Warnung - Konnte keine Marktdaten abrufen."
    )


if __name__ == "__main__":
  main()
