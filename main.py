import os
import requests

def send_telegram_signals():
    # 1. Telegram Zugangsdaten aus den Umgebungsvariablen / GitHub Secrets laden
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    # Falls nicht als Umgebungsvariable gesetzt, direkt eintragen:
    if not bot_token:
        bot_token = "DEIN_TELEGRAM_BOT_TOKEN"
    if not chat_id:
        chat_id = "DEINE_CHAT_ID"

    # 2. Deine Marktdaten / Signale (hier deine Werte eintragen)
    market_signals = [
        {
            "asset_name": "Bitcoin (BTC)",
            "current_price": 83133.08,
            "is_bullish": True,
            "bullish_entry": 83310.87,
            "bullish_target": 84977.08,
            "bearish_entry": 81197.64,
            "bearish_target": 79573.69
        },
        {
            "asset_name": "Gold (XAU/USD)",
            "current_price": 4139.10,
            "is_bullish": False,
            "bullish_entry": 4174.90,
            "bullish_target": 4258.40,
            "bearish_entry": 4124.00,
            "bearish_target": 4041.52
        }
    ]

    # 3. Nachricht im exakten Design aufbauen
    message = "🤖 **AUTOMATISCHES TRADING SIGNAL**\n\n"

    for signal in market_signals:
        if signal["is_bullish"]:
            status_text = "🟢 **BULLISH TREND**"
        else:
            status_text = "🔴 **BEARISH TREND**"

        message += (
            f"📊 **Markt-Signal: {signal['asset_name']}**\n\n"
            f"💵 **Aktueller Preis:** `{signal['current_price']:.2f}`\n"
            f"📈 **Status:** {status_text}\n\n"
            f"🚀 **BULLISH ZONE (Kaufen):**\n"
            f"• Einstieg ab: `{signal['bullish_entry']:.2f}`\n"
            f"• Von `{signal['bullish_entry']:.2f}` bis `{signal['bullish_target']:.2f}`\n\n"
            f"📉 **BEARISH ZONE (Verkaufen):**\n"
            f"• Einstieg ab: `{signal['bearish_entry']:.2f}`\n"
            f"• Von `{signal['bearish_entry']:.2f}` bis `{signal['bearish_target']:.2f}`\n\n"
        )

    # Letzten Zeilenumbruch entfernen
    message = message.strip()

    # 4. An Telegram senden
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    response = requests.post(url, json=payload)
    response_data = response.json()

    # 5. Überprüfung im GitHub Log
    if response.status_code == 200 and response_data.get("ok"):
        print("✅ Signal erfolgreich an Telegram gesendet!")
    else:
        print("❌ Fehler beim Senden an Telegram:")
        print(response_data)
        raise Exception(f"Telegram API Fehler: {response_data}")

if __name__ == "__main__":
    send_telegram_signals()
