import pandas as pd
import requests
import yfinance as yf

# --- DEINE ZUGANGSDATEN ---
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
TELEGRAM_CHAT_ID = "6551623158"


def send_telegram_message(message_text):
  """Sendet die Nachricht an deinen Telegram-Chat."""
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message_text,
  }
  try:
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    print("✅ Signal erfolgreich an Telegram gesendet.")
  except requests.exceptions.HTTPError as err:
    print(f"❌ Telegram HTTP-Fehler: {err}")
    print(f"Antwort von Telegram: {response.text}")
  except Exception as e:
    print(f"❌ Netzwerk- oder unerwarteter Fehler: {e}")


def calculate_atr(df, period=12):
  """Berechnet die Average True Range (ATR) für die Volatilität."""
  high_low = df["High"] - df["Low"]
  high_close = (df["High"] - df["Close"].shift()).abs()
  low_close = (df["Low"] - df["Close"].shift()).abs()
  ranges = pd.concat([high_low, high_close, low_close], axis=1)
  true_range = ranges.max(axis=1)
  return true_range.rolling(period).mean()


def check_gold_setup():
  """Analysiert Gold auf dem M15-Timeframe für klare Preis-Signale."""
  ticker_symbol = "GC=F"
  interval = "15m"
  period = "60d"

  try:
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty or len(df) < 50:
      print(f"⚠️ Zu wenig oder keine Daten geladen (Zeilen: {len(df)})")
      return None

    # ATR zur dynamischen Bestimmung von SL und TP
    df["ATR"] = calculate_atr(df)

    current_price = df["Close"].iloc[-1]
    prev_close = df["Close"].iloc[-2]
    atr = df["ATR"].iloc[-1]

    # Klare Preis-Action Logik (Vergleich letzte Kerze zur vorherigen)
    if current_price > prev_close:
      signal = "BUY (LONG SCALP)"
      trade_advice = "JA (Momentum Aufwärts - Long)"
      entry_price = current_price
      stop_loss = entry_price - (1.2 * atr)
      take_profit = entry_price + (1.8 * atr)
    else:
      signal = "SELL (SHORT SCALP)"
      trade_advice = "JA (Momentum Abwärts - Short)"
      entry_price = current_price
      stop_loss = entry_price + (1.2 * atr)
      take_profit = entry_price - (1.8 * atr)

    return {
        "symbol": "XAUUSD (Spot / Gold)",
        "timeframe": "M15 (15-Min Scalping)",
        "signal": signal,
        "trade_advice": trade_advice,
        "entry": round(entry_price, 2),
        "sl": round(stop_loss, 2),
        "tp": round(take_profit, 2),
    }

  except Exception as e:
    print(f"❌ Fehler bei der XAUUSD-Analyse: {e}")
    return None


def main():
  print("🤖 Führe XAUUSD M15 Preis-Signal Prüfung aus...")
  data = check_gold_setup()

  if data:
    report = (
        f"⚡ XAUUSD 15-MINUTEN SCALPING SIGNAL ⚡\n"
        f"-----------------------------------\n"
        f"📊 Asset: {data['symbol']} ({data['timeframe']})\n"
        f"• Signal: {data['signal']}\n"
        f"• Empfehlung: {data['trade_advice']}\n\n"
        f"• **Einstiegspreis:** ${data['entry']}\n"
        f"• **Stop-Loss (SL):** ${data['sl']}\n"
        f"• **Take-Profit (TP):** ${data['tp']}\n"
    )
    send_telegram_message(report)
  else:
    print("⚠️ Warnung: Konnte keine aktuellen Daten abrufen.")
    send_telegram_message(
        "⚠️ XAUUSD Scalp Bot: Warnung - Konnte keine Marktdaten abrufen."
    )


if __name__ == "__main__":
  main()
