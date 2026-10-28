import requests
import yfinance as yf
import pandas as pd

# --- KONFIGURATION ---
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
CHAT_ID = "6551623158"
SYMBOL = "GC=F"
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
        print(f"❌ Fehler beim Senden an Telegram: {e}")
        return {}

def main():
    print("🔄 Starte Kursabfrage...")
    try:
        # 1. Kurs von Yahoo holen (Tages- oder Stundenbasis)
        ticker = yf.Ticker(SYMBOL)
        data = ticker.history(period="7d", interval="1h")
        
        if data.empty:
            print("⚠️ GC=F liefert keine Daten, versuche XAUUSD=X...")
            ticker = yf.Ticker("XAUUSD=X")
            data = ticker.history(period="7d", interval="1h")

        if data.empty:
            print("❌ Fehler: Konnte absolut keine Kursdaten abrufen.")
            send_telegram_message("⚠️ **Bot-Fehler:** Konnte keine Kursdaten von Yahoo Finance abrufen.")
            return

        # Zeitzonen-Awareness entfernen, falls vorhanden, um Fehler zu vermeiden
        if data.index.tz is not None:
            data.index = data.index.tz_convert(None)

        # Letzte gültige Zeile ermitteln
        letzte_zeile = data.iloc[-1]
        letzte_zeit = data.index[-1]
        roher_kurs = float(letzte_zeile['Close'])
        aktueller_kurs = roher_kurs + PREIS_KORREKTUR
        
        print(f"✅ Letzte Kerze von: {letzte_zeit} | Roh={roher_kurs}, Korrigiert={aktueller_kurs}")
        
        # 2. Sauberer RSI (Wilder's Smoothing Methode)
        delta = data['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        # Exponentieller gleitender Durchschnitt (Standard für RSI)
        avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        rsi_series = 100 - (100 / (1 + rs))
        rsi_wert = float(rsi_series.iloc[-1])
        
        print(f"📊 Berechneter RSI: {rsi_wert:.2f}")

        # 3. Signal-Logik
        if rsi_wert >= 50:
            emoji = "🔴"
            aktion_text = "SELL (VERKAUFEN)"
            einstieg_min = aktueller_kurs - 1.0
            einstieg_max = aktueller_kurs + 1.0
            take_profit = aktueller_kurs - 10.0
            stop_loss = aktueller_kurs + 10.0
        else:
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
            f"🎯 Take-Profit (Ziel): {take_profit:.1f}\n"
            f"🛡️ Stop-Loss (Absicherung): {stop_loss:.1f}\n\n"
            f"📊 RSI: {rsi_wert:.2f}"
        )

        # 5. Senden
        result = send_telegram_message(nachricht)
        if result.get("ok"):
            print("🚀 Nachricht erfolgreich an Telegram gesendet!")
        else:
            print(f"❌ Telegram-API Fehler: {result}")

    except Exception as e:
        print(f"❌ Schwerwiegender Fehler im Skript: {e}")

if __name__ == "__main__":
    main()
