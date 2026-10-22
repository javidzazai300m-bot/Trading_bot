import requests

def send_trading_signal(bot_token, chat_id, asset_name, current_price, status_is_bullish, bullish_entry, bullish_target, bearish_entry, bearish_target):
    # Status-Anzeige festlegen
    if status_is_bullish:
        status_text = "🟢 **BULLISH TREND**"
    else:
        status_text = "🔴 **BEARISH TREND**"

    # Nachricht mit Markdown-Formatierung aufbauen
    message = (
        f"🤖 **AUTOMATISCHES TRADING SIGNAL**\n\n"
        f"📊 **Markt-Signal: {asset_name}**\n\n"
        f"💵 **Aktueller Preis:** `{current_price:.2f}`\n"
        f"📈 **Status:** {status_text}\n\n"
        f"🚀 **BULLISH ZONE (Kaufen):**\n"
        f"• Einstieg ab: `{bullish_entry:.2f}`\n"
        f"• Von `{bullish_entry:.2f}` bis `{bullish_target:.2f}`\n\n"
        f"📉 **BEARISH ZONE (Verkaufen):**\n"
        f"• Einstieg ab: `{bearish_entry:.2f}`\n"
        f"• Von `{bearish_entry:.2f}` bis `{bearish_target:.2f}`"
    )

    # Telegram API Anfrage
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"  # Wichtig für Fett-Schrift und Code-Blöcke
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# --- BEISPIEL FÜR DEINE SIGNALE ---

BOT_TOKEN = "DEIN_TELEGRAM_BOT_TOKEN"
CHAT_ID = "DEINE_CHAT_ID"

# 1. Bitcoin Signal senden
send_trading_signal(
    bot_token=BOT_TOKEN,
    chat_id=CHAT_ID,
    asset_name="Bitcoin (BTC)",
    current_price=83133.08,
    status_is_bullish=True,
    bullish_entry=83310.87,
    bullish_target=84977.08,
    bearish_entry=81197.64,
    bearish_target=79573.69
)

# 2. Gold Signal senden
send_trading_signal(
    bot_token=BOT_TOKEN,
    chat_id=CHAT_ID,
    asset_name="Gold (XAU/USD)",
    current_price=4139.10,
    status_is_bullish=False,
    bullish_entry=4174.90,
    bullish_target=4258.40,
    bearish_entry=4124.00,
    bearish_target=4041.52
)

