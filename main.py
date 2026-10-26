import requests
import yfinance as yf

# --- KONFIGURATION ---
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
CHAT_ID = "6551623158"  #[span_1](start_span)[span_1](end_span)
SYMBOL = "XAUUSD=X"

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
    # Live-Spotpreis über Yahoo Finance abrufen
    ticker = yf.Ticker(SYMBOL)
    data = ticker.history(period="1d", interval="1m")
    
    if data.empty:
        print("Fehler: Konnte keine Kursdaten abrufen.")
        return

    # Letzten geschlossenen Preis holen
    aktueller_kurs = float(data['Close'].iloc[-1])
    
    # Beispielhafter RSI (oder hier deine echte RSI-Berechnung)
    rsi_wert = 55.0

    # Entscheidung für BUY oder SELL
    if rsi_wert >= 50:
        signal_typ = "SELL"
        emoji = "🔴"
        aktion_text = "SELL (VERKAUFEN)"
        einstieg_min = aktueller_kurs - 1.0
        einstieg_max = aktueller_kurs + 1.0
        take_profit = aktueller_kurs - 10.0
        stop_loss = aktueller_kurs + 10.0
    else:
        signal_typ = "BUY"
        emoji = "🟢"
        aktion_text = "BUY (KAUFEN)"
        einstieg_min = aktueller_kurs - 1.0
        einstieg_max = aktueller_kurs + 1.0
        take_profit = aktueller_kurs + 10.0
        stop_loss = aktueller_kurs - 10.0

    # Signal-Nachricht zusammenbauen
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

    # An Telegram senden
    result = send_telegram_message(nachricht)
    if result.get("ok"):
        print(f"Erfolgreich {signal_typ}-Signal an Telegram gesendet!")
    else:
        print("Fehler beim Senden an Telegram:", result)

if __name__ == "__main__":
    check_market_and_send_signal()

