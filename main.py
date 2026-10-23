import requests
import yfinance as yf

BOT_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
CHAT_ID = "6551623158"


def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram-Nachricht erfolgreich gesendet!")
        else:
            print(f"❌ Fehler: {response.text}")
    except Exception as e:
        print(f"⚠️ Fehler: {e}")


def analyze_and_send_signal(symbol="GC=F", asset_name="Gold (XAU/USD)"):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="5d", interval="1h")

    if df.empty:
        print("Keine Daten erhalten.")
        return

    current_price = round(df["Close"].iloc[-1], 2)
    recent_data = df.tail(24)
    support = round(recent_data["Low"].min(), 2)
    resistance = round(recent_data["High"].max(), 2)

    # Signal-Entscheidung basierend auf aktuellem Preis
    if current_price > (support + resistance) / 2:
        # BUY SIGNAL
        aktion = "🟢 **BUY (KAUFEN)**"
        
        # Klare Kaufzone: Nahe Support bis leicht über aktuellem Kurs
        buy_from = round(current_price * 0.998, 2)
        buy_to = round(current_price * 1.001, 2)
        
        take_profit = round(resistance, 2)
        stop_loss = round(support * 0.995, 2)

        nachricht = (
            f"🚨 **TRADING SIGNAL** 🚨\n\n"
            f"• **Asset:** {asset_name}\n"
            f"• **Aktueller Kurs:** {current_price}\n"
            f"• **Aktion:** {aktion}\n\n"
            f"🟢 **BUY-Einstieg:** Ab **{buy_from}** bis **{buy_to}**\n"
            f"🎯 **Take-Profit (Ziel):** **{take_profit}**\n"
            f"🛡️ **Stop-Loss (Absicherung):** **{stop_loss}**\n"
        )
    else:
        # SELL SIGNAL
        aktion = "🔴 **SELL (VERKAUFEN)**"
        
        # Klare Verkaufzone: Vom aktuellen Kurs bis leicht höher
        sell_from = round(current_price * 0.999, 2)
        sell_to = round(current_price * 1.002, 2)
        
        take_profit = round(support, 2)
        stop_loss = round(resistance * 1.005, 2)

        nachricht = (
            f"🚨 **TRADING SIGNAL** 🚨\n\n"
            f"• **Asset:** {asset_name}\n"
            f"• **Aktueller Kurs:** {current_price}\n"
            f"• **Aktion:** {aktion}\n\n"
            f"🔴 **SELL-Einstieg:** Ab **{sell_from}** bis **{sell_to}**\n"
            f"🎯 **Take-Profit (Ziel):** **{take_profit}**\n"
            f"🛡️ **Stop-Loss (Absicherung):** **{stop_loss}**\n"
        )

    send_telegram_message(nachricht)


if __name__ == "__main__":
    analyze_and_send_signal()
