import requests
import MetaTrader5 as mt5

# --- KONFIGURATION ---
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
CHAT_ID = "6551623158"  #[span_1](start_span)[span_1](end_span)
SYMBOL = "XAUUSD"

def send_telegram_message(message):
    """Sendet die Nachricht an deinen Telegram-Chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.json()

def check_market_and_send_signal():
    """Verbindet sich mit MT5, prüft die Richtung und sendet das Signal."""
    # 1. Verbindung zu MT5 herstellen
    if not mt5.initialize():
        print("MT5 Initialisierung fehlgeschlagen:", mt5.last_error())
        return

    # 2. Aktuellen Tick (Preis) direkt vom Broker abrufen
    symbol_info = mt5.symbol_info_tick(SYMBOL)
    if symbol_info is None:
        print(f"Konnte Kurs für {SYMBOL} nicht abrufen.")
        mt5.shutdown()
        return

    # Für BUY nutzen wir den Ask-Kurs, für SELL den Bid-Kurs
    ask_preis = symbol_info.ask
    bid_preis = symbol_info.bid
    aktueller_kurs = ask_preis  # Standardmäßig

    # --- HIER DEINE STRATEGIE-LOGIK EINBAUEN ---
    # Beispiel: Du ermittelst anhand deiner Indikatoren (z.B. RSI), ob Buy oder Sell vorliegt.
    rsi_wert = 55.0  # Ersetze dies durch deinen echten RSI-Wert
    
    # Beispiel-Bedingung: Wenn RSI < 45 -> BUY, wenn RSI > 55 -> SELL
    if rsi_wert < 45:
        signal_typ = "BUY"
        emoji = "🟢"
        aktion_text = "BUY (KAUFEN)"
        aktueller_kurs = ask_preis
        einstieg_min = aktueller_kurs - 1.0
        einstieg_max = aktueller_kurs + 1.0
        take_profit = aktueller_kurs + 10.0  # Ziel nach oben
        stop_loss = aktueller_kurs - 10.0    # Absicherung nach unten
    else:
        signal_typ = "SELL"
        emoji = "🔴"
        aktion_text = "SELL (VERKAUFEN)"
        aktueller_kurs = bid_preis
        einstieg_min = aktueller_kurs - 1.0
        einstieg_max = aktueller_kurs + 1.0
        take_profit = aktueller_kurs - 10.0  # Ziel nach unten
        stop_loss = aktueller_kurs + 10.0    # Absicherung nach oben

    # 3. Nachricht im exakten Format zusammenbauen
    nachricht = (
        f"{emoji} **TRADING SIGNAL** {emoji}\n\n"
        f"• Asset: Gold (XAU/USD)\n"
        f"• Aktueller Kurs: {aktueller_kurs:.2f}\n"
        f"• Aktion: {emoji} {aktion_text}\n\n"
        f"🎯 Einstieg: Ab {einstieg_min:.1f} bis {einstieg_max:.1f}\n"
        f"🎯 Take-Profit (Ziel): {take_profit:.1f}\n"
        f"🛡️ Stop-Loss (Absicherung): {stop_loss:.1f}\n\n"
        f"📊 RSI: {rsi_wert}"
    )

    # 4. An Telegram senden
    result = send_telegram_message(nachricht)
    if result.get("ok"):
        print(f"Erfolgreich {signal_typ}-Signal an Telegram gesendet!")
    else:
        print("Fehler beim Senden:", result)

    # MT5 Verbindung schließen
    mt5.shutdown()

if __name__ == "__main__":
    check_market_and_send_signal()
