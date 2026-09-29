import requests
import yfinance as yf

# ---------------------------------------------------------
# KONFIGURATION
# ---------------------------------------------------------
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
CHAT_ID = "6551623158"

# Aktive Handelspaare (Bitcoin & Gold)
SYMBOLS = {
    "Bitcoin (BTC)": "BTC-USD",
    "Gold (XAU/USD)": "GC=F"
}

def send_telegram_message(message: str):
    """Sendet eine Nachricht an den Telegram-Bot."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Nachricht erfolgreich an Telegram gesendet!")
    except Exception as e:
        print(f"Fehler beim Senden der Nachricht: {e}")

def analyze_market(symbol_ticker: str, symbol_name: str) -> str:
    """Holt Marktdaten und berechnet Bullish- & Bearish-Zonen."""
    ticker = yf.Ticker(symbol_ticker)
    df = ticker.history(period="5d", interval="1h")
    
    if df.empty:
        return f"⚠️ Keine Daten für {symbol_name} gefunden."
    
    current_price = df['Close'].iloc[-1]
    high_price = df['High'].tail(24).max()  # 24-Stunden-Hoch
    low_price = df['Low'].tail(24).min()    # 24-Stunden-Tief
    
    # Preis-Reichweiten berechnen (+2% / -2% Zielzonen)
    bullish_trigger = high_price
    bearish_trigger = low_price
    bullish_target = bullish_trigger * 1.02
    bearish_target = bearish_trigger * 0.98
    
    # Trend-Tendenz
    if current_price > (high_price + low_price) / 2:
        bias = "🟢 **BULLISH TREND**"
    else:
        bias = "🔴 **BEARISH TREND**"

    msg = (
        f"📊 *Markt-Signal: {symbol_name}*\n"
        f"___________________________________\n\n"
        f"💵 **Aktueller Preis:** `{current_price:.2f}`\n"
        f"📈 **Status:** {bias}\n\n"
        f"🚀 **BULLISH ZONE (Kaufen):**\n"
        f"• Einstieg ab: `{bullish_trigger:.2f}`\n"
        f"• Von `{bullish_trigger:.2f}` bis `{bullish_target:.2f}`\n\n"
        f"📉 **BEARISH ZONE (Verkaufen):**\n"
        f"• Einstieg ab: `{bearish_trigger:.2f}`\n"
        f"• Von `{bearish_trigger:.2f}` bis `{bearish_target:.2f}`\n"
        f"___________________________________"
    )
    return msg

def main():
    full_report = "🤖 *AUTOMATISCHES TRADING SIGNAL*\n\n"
    for name, ticker in SYMBOLS.items():
        report = analyze_market(ticker, name)
        full_report += report + "\n\n"
    
    send_telegram_message(full_report)

if __name__ == "__main__":
    main()
