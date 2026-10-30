import requests
import yfinance as yf
import pandas as pd

# --- KONFIGURATION ---
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
CHAT_ID = "6551623158"
SYMBOL = "GC=F"
PREIS_KORREKTUR = -9.0 

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
        print(f"❌ Fehler beim Senden an Telegram: {e}")
        return {}

def main():
    print("🔄 Starte Kursabfrage im 15-Minuten-Takt (ohne RSI)...")
    try:
        # 1. Kurs von Yahoo holen (15-Minuten-Intervall)
        ticker = yf.Ticker(SYMBOL)
        data = ticker.history(period="1d", interval="15m")
        
        if data.empty:
            print("⚠️ GC=F liefert keine Daten, versuche XAUUSD=X...")
            ticker = yf.Ticker("XAUUSD=X")
            data = ticker.history(period="1d", interval="15m")

        if data.empty:
            print("❌ Fehler: Konnte absolut keine Kursdaten abrufen.")
            send_telegram_message("⚠️ **Bot-Fehler:** Konnte keine Kursdaten von Yahoo Finance abrufen.")
            return

        # Zeitzonen-Awareness entfernen
        if data.index.tz is not None:
            data.index = data.index.tz_convert(None)

        # Prüfen, ob genügend Daten für den Vergleich da sind
        if len(data) < 2:
            print("❌ Fehler: Nicht genügend Datenpunkte für den Trendvergleich.")
            return

        # Letzte und vorherige Zeile ermitteln
        letzte_zeile = data.iloc[-1]
        vorherige_zeile = data.iloc[-2]
        letzte_zeit = data.index[-1]
        
        roher_kurs = float(letzte_zeile['Close'])
        vorheriger_schluss = float(vorherige_zeile['Close'])
        aktueller_kurs = roher_kurs + PREIS_KORREKTUR
        
        print(f"✅ Letzte Kerze von: {letzte_zeit} | Roh={roher_kurs}, Korrigiert={aktueller_kurs}")
        
        # 2. Reine Trend-Logik (Steigt der Kurs -> BUY, Fällt er -> SELL)
        if roher_kurs >= vorheriger_schluss:
            emoji = "🔵"
            aktion_text = "BUY (KAUFEN)"
            einstieg_min = aktueller_kurs - 1.0
            einstieg_max = aktueller_kurs + 1.0
            take_profit = aktueller_kurs + 10.0
            stop_loss = aktueller_kurs - 5.0
        else:
            emoji = "🔴"
            aktion_text = "SELL (VERKAUFEN)"
            einstieg_min = aktueller_kurs - 1.0
            einstieg_max = aktueller_kurs + 1.0
            take_profit = aktueller_kurs - 10.0
            stop_loss = aktueller_kurs + 5.0

        # 3. Nachricht zusammenbauen mit klarer Einstiegsspanne
        nachricht = (
            f"{emoji} **GOLD TRADING SIGNAL** {emoji}\n\n"
            f"• Asset: Gold (XAU/USD)\n"
            f"• Aktueller Kurs: {aktueller_kurs:.2f}\n"
            f"• Aktion: {aktion_text}\n\n"
            f"🎯 Einstieg: Ab {einstieg_min:.1f} bis {einstieg_max:.1f}\n"
            f"🎯 Take-Profit (Ziel): {take_profit:.1f}\n"
            f"🛡️ Stop-Loss (Absicherung): {stop_loss:.1f}"
        )

        # 4. Senden an Telegram
        result = send_telegram_message(nachricht)
        if result.get("ok"):
            print("🚀 Nachricht erfolgreich an Telegram gesendet!")
        else:
            print(f"❌ Telegram-API Fehler: {result}")

    except Exception as e:
        print(f"❌ Schwerwiegender Fehler im Skript: {e}")

if __name__ == "__main__":
    main()
