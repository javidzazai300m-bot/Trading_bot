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
        df = ticker.history(period="5d", interval="15m")

        if df.empty or len(df) < 20:
            return

        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        last_close = df['Close'].iloc[-1]
        last_ema = df['EMA50'].iloc[-1]
        
        # Berechne Preis-Zonen (Support und Resistance aus den letzten 20 Kerzen)
        support = df['Low'].tail(20).min()
        resistance = df['High'].tail(20).max()

        now_str = datetime.datetime.now().strftime("%H:%M Uhr")

        # Bestimme Trend und Preis-Bereiche
        if last_close > last_ema:
            trend = "🟢 **BULLISH (LONG)**"
            preis_zone = (
                f"• 🟢 **Bullish-Bereich (Kaufen):** Zwischen `{support:.2f}` und `{last_close:.2f}`\n"
                f"• 🎯 **Handelsempfehlung:** Suche Long-Einstiege in diesem Preisband (Ziel Richtung `{resistance:.2f}`)"
            )
        else:
            trend = "🔴 **BEARISH (SHORT)**"
            preis_zone = (
                f"• 🔴 **Bearish-Bereich (Verkaufen):** Zwischen `{last_close:.2f}` und `{resistance:.2f}`\n"
                f"• 🎯 **Handelsempfehlung:** Suche Short-Einstiege in diesem Preisband (Ziel Richtung `{support:.2f}`)"
            )

        message = (
            f"📊 **MARKT & PREIS-ZONEN** ({now_str})\n"
            f"🪙 **Asset:** Gold (XAU/USD)\n"
            f"💵 **Aktueller Kurs:** `{last_close:.2f}`\n"
            f"📈 **Aktueller Trend:** {trend}\n\n"
            f"📍 **Genaue Preis-Grenzen für den Trade:**\n"
            f"{preis_zone}\n\n"
            f"🛡️ **Wichtige Chart-Marken:**\n"
            f"• Support (Unterstützung): `{support:.2f}`\n"
            f"• Resistance (Widerstand): `{resistance:.2f}`"
        )
        send_telegram_message(message)

    except Exception as e:
        print(f"Fehler bei der Analyse: {e}")

if __name__ == "__main__":
    check_entry_signal("GC=F")
