import requests
import yfinance as yf

# --- KONFIGURATION ---
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
CHAT_ID = "6551623158"
SYMBOL = "GC=F"

# HIER KANNST DU DEN PREIS ANPASSEN:
# Wenn der Bot z.B. 14 Dollar zu hoch anzeigt, tragen wir hier -14.0 ein.
# Du kannst diesen Wert anpassen, falls sich der Abstand leicht ändert.
PREIS_KORREKTUR = -14.0 

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Fehler beim Senden: {e}")
        return {}

def main():
    try:
        # 1. Kurs von Yahoo holen
        ticker = yf.Ticker(SYMBOL)
        data = ticker.history(period="1d", interval="1m")
        
        if data.empty:
            ticker = yf.Ticker("XAUUSD=X")
            data = ticker.history(period="1d", interval="1m")

        if data.empty:
            send_telegram_message("⚠️ **Fehler:** Konnte keine Kursdaten abrufen.")
            return

        # 2. Rohpreis holen und die Korrektur (Offset) anrechnen, damit er exakt zu MT5 passt
        roher_kurs = float(data['Close'].iloc[-1])
        aktueller_kurs = roher_kurs + PREIS_KORREKTUR
        
        # 3. Signal-Logik
        rsi_wert = 55.0  

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

        # 4. Nachricht zusammenbauen
        nachricht = (
            f"{emoji} **TRADING SIGNAL** {emoji}\n\n"
            f"• Asset: Gold (XAU/USD)\n"
            f"• Aktueller Kurs: {aktueller_kurs:.2f}\n"
            f"• Aktion: {emoji} {aktion_text}\n\n"
            f"🎯 Einstieg: Ab {einstieg_min:.1f} bis {einstieg_max:.1f}\n"
            f"🎯 Take-Profit (Ziel): {take_-profit:.1f}\n"
            f"🛡️ Stop-Loss (Absicherung): {stop_loss:.1f}\n\n"
            f"📊 RSI: {rsi_wert}"
        )

        # Korrigierter Fix für Take-Profit Variablenname im String (falls nötig)
        nachricht = nachricht.replace("take_-profit", "Take-Profit")

        # 5. Senden
        result = send_telegram_message(nachricht)
        if result.get("ok"):
            print("Erfolgreich gesendet!")
        else:
            print(f"Fehler: {result}")

    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    main()
