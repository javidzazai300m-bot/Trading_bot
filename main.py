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

        if df.empty or len(df) < 10:
            return

        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()

        prev_ema9 = df['EMA9'].iloc[-2]
        prev_ema21 = df['EMA21'].iloc[-2]
        
        last_ema9 = df['EMA9'].iloc[-1]
        last_ema21 = df['EMA21'].iloc[-1]
        last_close = df['Close'].iloc[-1]

        now = datetime.datetime.now()
        now_str = now.strftime("%H:%M Uhr")
        
        # Feste Trading-Zeiten / Haupt-Sessions (Deutsche Zeit CET)
        # Zeigt das aktive Handelsfenster an
        handels_fenster = "09:00 – 17:30 Uhr (London & New York Session)"
        gueltig_bis = (now + datetime.timedelta(hours=2)).strftime("%H:%M Uhr")

        # Crossover Prüfungen
        if prev_ema9 <= prev_ema21 and last_ema9 > last_ema21:
            sl = last_close * 0.997
            tp = last_close * 1.006
            message = (
                f"🚨 **TRADING SIGNAL & ZEITEN!** ({now_str})\n"
                f"📊 **Asset:** Gold (XAU/USD)\n\n"
                f"🎯 **Aktion:** 🟢 **BUY / LONG POSITION JETZT ÖFFNEN**\n"
                f"💵 **Einstiegskurs:** `{last_close:.2f}`\n\n"
                f"⏳ **Traden & Zeiten:**\n"
                f"• 🕒 **Aktives Handelsfenster:** {handels_fenster}\n"
                f"• ⏱️ **Signal gültig / Halten bis:** ca. **{gueltig_bis}**\n\n"
                f"🛡️ **Risk Management:**\n"
                f"• SL: `{sl:.2f}`\n"
                f"• TP: `{tp:.2f}`"
            )
            send_telegram_message(message)

        elif prev_ema9 >= prev_ema21 and last_ema9 < last_ema21:
            sl = last_close * 1.003
            tp = last_close * 0.994
            message = (
                f"🚨 **TRADING SIGNAL & ZEITEN!** ({now_str})\n"
                f"📊 **Asset:** Gold (XAU/USD)\n\n"
                f"🎯 **Aktion:** 🔴 **SELL / SHORT POSITION JETZT ÖFFNEN**\n"
                f"💵 **Einstiegskurs:** `{last_close:.2f}`\n\n"
                f"⏳ **Traden & Zeiten:**\n"
                f"• 🕒 **Aktives Handelsfenster:** {handels_fenster}\n"
                f"• ⏱️ **Signal gültig / Halten bis:** ca. **{gueltig_bis}**\n\n"
                f"🛡️ **Risk Management:**\n"
                f"• SL: `{sl:.2f}`\n"
                f"• TP: `{tp:.2f}`"
            )
            send_telegram_message(message)
        else:
            trend = "🟢 **BULLISH**" if last_ema9 > last_ema21 else "🔴 **BEARISH**"
            message = (
                f"⏳ **MARKT STATUS & ZEITEN** ({now_str})\n"
                f"📊 **Asset:** Gold (XAU/USD)\n"
                f"💵 **Aktueller Kurs:** `{last_close:.2f}`\n"
                f"📈 **Aktueller Trend:** {trend}\n\n"
                f"🕒 **Empfohlene Traden-Zeit:**\n"
                f"• Haupt-Handelsfenster: **{handels_fenster}**\n"
                f"• Nächster Check in 15 Min. Bot wartet auf Richtungswechsel."
            )
            send_telegram_message(message)

    except Exception as e:
        print(f"Fehler bei der Analyse: {e}")

if __name__ == "__main__":
    check_entry_signal("GC=F")
