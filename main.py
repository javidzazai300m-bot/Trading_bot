import os
import requests
import yfinance as yf

# Telegram Zugangsdaten
BOT_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
CHAT_ID = "6551623158"


def send_telegram_message(message: str):
    """Sendet eine formatierte Nachricht an deinen Telegram-Chat."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram-Nachricht erfolgreich gesendet!")
        else:
            print(f"❌ Fehler beim Senden: {response.text}")
    except Exception as e:
        print(f"⚠️ Netzwerkfehler: {e}")


def analyze_and_send_signal(symbol="GC=F", asset_name="Gold (XAU/USD)"):
    """Holt die aktuellen Marktdaten von yfinance und baut das Signal auf."""
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="5d", interval="1h")

    if df.empty:
        print("Keine Daten erhalten.")
        return

    # Aktueller Preis
    current_price = round(df["Close"].iloc[-1], 2)

    # Einfache Berechnung von Support & Resistance (letzte 24 Stunden)
    recent_data = df.tail(24)
    support = round(recent_data["Low"].min(), 2)
    resistance = round(recent_data["High"].max(), 2)

    # Beispiel-Logik für Signal-Erstellung
    # (Kannst du je nach deiner Strategie/RSI/Moving Averages anpassen)
    if current_price > (support + resistance) / 2:
        signal_typ = "🟢 KAUFEN (BUY)"
        von_preis = support
        bis_preis = current_price
        target_price = round(resistance * 1.002, 2)
    else:
        signal_typ = "🔴 VERKAUFEN (SELL)"
        von_preis = current_price
        bis_preis = resistance
        target_price = round(support * 0.998, 2)

    # Klar strukturiertes Nachrichten-Format
    nachricht = (
        f"🚨 **TRADING SIGNAL** 🚨\n\n"
        f"• **Asset:** {asset_name}\n"
        f"• **Aktueller Kurs:** {current_price}\n"
        f"• **Aktion:** {signal_typ}\n\n"
        f"📍 **Preis-Bereich:** Von **{von_preis}** bis **{bis_preis}**\n"
        f"🎯 **Ziel (Take-Profit):** {target_price}\n"
    )

    send_telegram_message(nachricht)


if __name__ == "__main__":
    analyze_and_send_signal()
