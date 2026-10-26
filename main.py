import requests
import yfinance as yf

# --- KONFIGURATION ---
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
CHAT_ID = "6551623158" #[span_1](start_span)[span_1](end_span)
SYMBOL = "GC=F"  # Gold Futures / Spot

def send_telegram_message(message):
    """Sendet eine Nachricht direkt an deinen Telegram-Chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        print("Telegram API Response:", response.text)
        return response.json()
    except Exception as e:
        print("Fehler beim Telegram-Aufruf:", e)
        return {}

def check_market_and_send_signal():
    try:
        # 1. Daten abrufen
        ticker = yf.Ticker(SYMBOL)
        data = ticker.history(period="1d", interval="1m")
        
        # Falls yfinance leer ist, versuchen wir das Ausweich-Symbol XAUUSD=X
        if data.empty:
            print("Erster Versuch leer, versuche XAUUSD=X...")
            ticker = yf.Ticker("XAUUSD=X")
            data = ticker.history(period="1d", interval="1m")

        if data.empty:
            send_telegram_message("⚠️ **Fehler:** Konnte keine Kursdaten von Yahoo Finance abrufen. Bitte später erneut versuchen.")
            return

        # 2. Aktuellen Kurs ermitteln
        aktueller_kurs = float(data['Close'].iloc[-1])
        
        # 3. Signallogik (Beispielhafter RSI / Richtungsberechnung)
        rsi_wert = 55.0  # Ersetze dies durch deine echte RSI-Berechnung

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

        # 4. Nachricht aufbauen
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

        # 5. Absenden
        res = send_telegram_message(nachricht)
        print("Ergebnis:", res)

    except Exception as e:
        # Sendet eine Fehlermeldung direkt an Telegram, falls das Skript abstürzt
        send_telegram_message(f"❌ **Skript-Fehler:** {str(e)}")

if __name__ == "__main__":
    check_market_and_send_signal()
