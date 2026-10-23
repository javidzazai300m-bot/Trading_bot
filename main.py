import os
import requests
import datetime
import yfinance as yf

# Telegram Zugangsdaten
BOT_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
CHAT_ID = "6551623158"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Signal erfolgreich gesendet!")
        else:
            print(f"Fehler beim Senden: {response.text}")
    except Exception as e:
        print(f"Fehler: {e}")

def check_entry_signal(symbol="GC=F"):
    try:
        # Wir holen uns die letzten Kerzen (z.B. im 15-Minuten-Takt)
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2d", interval="15m")

        if df.empty or len(df) < 10:
            print("Keine ausreichenden Marktdaten.")
            return

        # Gleitende Durchschnitte (EMA 9 und EMA 21) für das Signal berechnen
        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()

        # Vorherige und aktuelle Kerze vergleichen
        prev_ema9 = df['EMA9'].iloc[-2]
        prev_ema21 = df['EMA21'].iloc[-2]
        
        last_ema9 = df['EMA9'].iloc[-1]
        last_ema21 = df['EMA21'].iloc[-1]
        last_close = df['Close'].iloc[-1]

        signal = None
        
        # Bullish Crossover (EMA 9 kreuzt EMA 21 nach oben -> Kaufen)
        if prev_ema9 <= prev_ema21 and last_ema9 > last_ema21:
            signal = "🟢 **BUY / LONG POSITION JETZT ÖFFNEN**"
            reason = "Der Trend ist kurzfristig nach oben gedreht (EMA 9 über EMA 21)."
            sl = last_close * 0.997  # Stop Loss knapp darunter
            tp = last_close * 1.006  # Take Profit als Ziel

        # Bearish Crossover (EMA 9 kreuzt EMA 21 nach unten -> Verkaufen)
        elif prev_ema9 >= prev_ema21 and last_ema9 < last_ema21:
            signal = "🔴 **SELL / SHORT POSITION JETZT ÖFFNEN**"
            reason = "Der Trend ist kurzfristig nach unten gedreht (EMA 9 unter EMA 21)."
            sl = last_close * 1.003  # Stop Loss knapp darüber
            tp = last_close * 0.994  # Take Profit als Ziel

        # Wenn ein Signal da ist, schicken wir dir die Nachricht
        if signal:
            now_str = datetime.datetime.now().strftime("%H:%M Uhr")
            message = (
                f"🚨 **TRADING SIGNAL: JETZT HANDELN!** ({now_str})\n"
                f"📊 **Asset:** Gold (XAU/USD)\n\n"
                f"🎯 **Aktion:** {signal}\n"
                f"💵 **Einstiegskurs:** `{last_close:.2f}`\n\n"
                f"💡 **Grund:** {reason}\n\n"
                f"🛡️ **Vorschlag für Risk Management:**\n"
                f"• Stop Loss (SL): `{sl:.2f}`\n"
                f"• Take Profit (TP): `{tp:.2f}`"
            )
            send_telegram_message(message)
        else:
            print("Kein neues Kreuzungssignal im aktuellen Takt. Bot wartet...")

    except Exception as e:
        print(f"Fehler bei der Analyse: {e}")

if __name__ == "__main__":
    check_entry_signal("GC=F")
