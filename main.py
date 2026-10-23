import os
import requests
import datetime
import yfinance as yf

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
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Fehler: {e}")

def check_entry_signal(symbol="GC=F"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2d", interval="15m")

        if df.empty or len(df) < 2:
            return

        # Berechne EMA 9 und EMA 21 für konkretes Einstiegssignal
        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()

        # Kerze vor 15 Min (prev) und aktuelle Kerze (last)
        prev_ema9 = df['EMA9'].iloc[-2]
        prev_ema21 = df['EMA21'].iloc[-2]
        
        last_ema9 = df['EMA9'].iloc[-1]
        last_ema21 = df['EMA21'].iloc[-1]
        last_close = df['Close'].iloc[-1]

        signal = None
        
        # Bullish Crossover (EMA9 kreuzt EMA21 nach oben)
        if prev_ema9 <= prev_ema21 and last_ema9 > last_ema21:
            signal = "🟢 **BUY / LONG POSITION JETZT ÖFFNEN**"
            reason = "EMA 9 hat den EMA 21 nach oben gekreuzt (Bullish Momentum)."
            sl = last_close * 0.997  # ca. 0.3% Stop Loss
            tp = last_close * 1.006  # ca. 0.6% Take Profit

        # Bearish Crossover (EMA9 kreuzt EMA21 nach unten)
        elif prev_ema9 >= prev_ema21 and last_ema9 < last_ema21:
            signal = "🔴 **SELL / SHORT POSITION JETZT ÖFFNEN**"
            reason = "EMA 9 hat den EMA 21 nach unten gekreuzt (Bearish Momentum)."
            sl = last_close * 1.003
            tp = last_close * 0.994

        if signal:
            now_str = datetime.datetime.now().strftime("%H:%M Uhr")
            message = (
                f"🚨 **EINSIEGSSIGNAL AB JETZT!** ({now_str})\n"
                f"📊 **Asset:** Gold (XAU/USD)\n\n"
                f"🎯 **Aktion:** {signal}\n"
                f"💵 **Einstiegskurs:** `{last_close:.2f}`\n\n"
                f"💡 **Grund:** {reason}\n\n"
                f"📍 **Vorschlag Levels:**\n"
                f"• SL: `{sl:.2f}`\n"
                f"• TP: `{tp:.2f}`"
            )
            send_telegram_message(message)
        else:
            print("Kein konkretes Einstiegssignal im aktuellen 15M-Fenster.")

    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    check_entry_signal("GC=F")
