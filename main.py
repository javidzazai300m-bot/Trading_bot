import requests
import yfinance as yf

# ---------------------------------------------------------
# KONFIGURATION & RISIKOMANAGEMENT
# ---------------------------------------------------------
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
CHAT_ID = "6551623158"

# Dein festgelegtes Risiko pro Trade in Euro
RISK_EUR = 20.00

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
    """Holt Marktdaten und berechnet konkrete Einstiege, SL, TP und Lot-Größe."""
    ticker = yf.Ticker(symbol_ticker)
    df = ticker.history(period="5d", interval="1h")
    
    if df.empty:
        return f"⚠️ Keine Daten für {symbol_name} gefunden."
    
    current_price = df['Close'].iloc[-1]
    high_price = df['High'].tail(24).max()  # 24-Stunden-Hoch
    low_price = df['Low'].tail(24).min()    # 24-Stunden-Tief
    
    # Signal-Logik basierend auf der Marktphase
    if current_price > (high_price + low_price) / 2:
        signal_type = "🟢 **KAUFSIGNAL (BUY)**"
        entry_price = current_price
        stop_loss = entry_price * 0.995       # SL 0.5% unter Einstieg
        take_profit = entry_price * 1.010     # TP 1.0% über Einstieg
        
        risk_per_unit = entry_price - stop_loss
        lot_size = RISK_EUR / (risk_per_unit * 10) if risk_per_unit > 0 else 0.01
    else:
        signal_type = "🔴 **VERKAUFSIGNAL (SELL)**"
        entry_price = current_price
        stop_loss = entry_price * 1.005       # SL 0.5% über Einstieg
        take_profit = entry_price * 0.990     # TP 1.0% unter Einstieg
        
        risk_per_unit = stop_loss - entry_price
        lot_size = RISK_EUR / (risk_per_unit * 10) if risk_per_unit > 0 else 0.01

    # Lot-Größe auf 2 Nachkommastellen runden (Mindestens 0.01 Lot)
    lot_size = max(0.01, round(lot_size, 2))

    msg = (
        f"📊 *{signal_type}: {symbol_name}*\n"
        f"___________________________________\n\n"
        f"💵 **Einstiegspreis:** `{entry_price:.2f}`\n"
        f"🛑 **Stop-Loss (SL):** `{stop_loss:.2f}`\n"
        f"🎯 **Take-Profit (TP):** `{take_profit:.2f}`\n\n"
        f"⚙️ **Risikomanagement:**\n"
        f"• Risiko pro Trade: `{RISK_EUR:.2f} EUR`\n"
        f"• Empfohlene Lot-Größe: `{lot_size} Lot`\n"
        f"___________________________________"
    )
    return msg

def main():
    full_report = "🤖 *Javidtradingbot - Konkrete Signale*\n\n"
    for name, ticker in SYMBOLS.items():
        report = analyze_market(ticker, name)
        full_report += report + "\n\n"
    
    send_telegram_message(full_report)

if __name__ == "__main__":
    main()

