def check_gold_setup():
  """Analysiert Gold auf dem M15-Timeframe mit Timeout-Schutz."""
  ticker_symbol = "GC=F"
  interval = "15m"
  period = "1mo"

  try:
    print("⏳ Lade Marktdaten von yfinance...")
    ticker = yf.Ticker(ticker_symbol)

    # Hier holen wir die Daten (mit eingebautem Sicherheitsnetz)
    df = ticker.history(period=period, interval=interval, timeout=10)

    if df.empty or len(df) < 50:
      print(f"⚠️ Zu wenig oder keine Daten geladen (Zeilen: {len(df)})")
      return None

    # Indikatoren berechnen
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["ATR"] = calculate_atr(df)

    current_price = df["Close"].iloc[-1]
    ema_20 = df["EMA_20"].iloc[-1]
    ema_50 = df["EMA_50"].iloc[-1]
    atr = df["ATR"].iloc[-1]

    # Trend- und Signal-Logik
    if current_price > ema_20 and ema_20 > ema_50:
      trend = "BULLISH 🟢"
      signal = "BUY (LONG)"
      trade_advice = "JA (Aufwärtstrend im M15 - Long Einstieg)"
      entry_price = current_price
      stop_loss = entry_price - (1.5 * atr)
      take_profit = entry_price + (3.0 * atr)
    elif current_price < ema_20 and ema_20 < ema_50:
      trend = "BEARISH 🔴"
      signal = "SELL (SHORT)"
      trade_advice = "JA (Abwärtstrend im M15 - Short Einstieg)"
      entry_price = current_price
      stop_loss = entry_price + (1.5 * atr)
      take_profit = entry_price - (3.0 * atr)
    else:
      trend = "NEUTRAL / KORREKTUR 🟡"
      signal = "KEIN KLARES SIGNAL"
      trade_advice = "NEIN (Warten auf klaren Trend / Seitwärtsphase)"
      entry_price = current_price
      stop_loss = 0
      take_profit = 0

    return {
        "symbol": "Gold Futures (GC=F)",
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

  except Exception as e:
    print(f"❌ Fehler bei der Datenabfrage: {e}")
    return None
