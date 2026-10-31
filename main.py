import time
import MetaTrader5 as mt5
import pandas as pd
import requests

# ---------------------------------------------------------
# TELEGRAM KONFIGURATION
# ---------------------------------------------------------
TELEGRAM_BOT_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
TELEGRAM_CHAT_ID = "6551623158"


def send_telegram_message(message):
    """Sendet eine Textnachricht an deinen Telegram Bot."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ Telegram-Benachrichtigung erfolgreich gesendet!")
        else:
            print(
                f"❌ Fehler beim Senden an Telegram: {response.status_code} - {response.text}"
            )
    except Exception as e:
        print(f"❌ Fehler bei der Verbindung zu Telegram: {e}")


# ---------------------------------------------------------
# METATRADER 5 INITIALISIERUNG
# ---------------------------------------------------------
if not mt5.initialize():
    print(
        "Metatrader 5 konnte nicht initialisiert werden, Fehler:",
        mt5.last_error(),
    )
    quit()

symbol = "XAUUSD"
timeframe = mt5.TIMEFRAME_M5


def get_data(symbol, timeframe, n=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df


def check_trade_signal():
    df = get_data(symbol, timeframe, n=50)

    # Gleitende Durchschnitte (EMA) berechnen
    df["EMA_9"] = df["close"].ewm(span=9, adjust=False).mean()
    df["EMA_21"] = df["close"].ewm(span=21, adjust=False).mean()

    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    # Signal: EMA 9 kreuzt von unten nach oben über EMA 21 (Golden Cross)
    if (
        prev_row["EMA_9"] <= prev_row["EMA_21"]
        and last_row["EMA_9"] > last_row["EMA_21"]
    ):
        return "BUY"

    # Signal: EMA 9 kreuzt von oben nach unten unter EMA 21 (Death Cross)
    elif (
        prev_row["EMA_9"] >= prev_row["EMA_21"]
        and last_row["EMA_9"] < last_row["EMA_21"]
    ):
        return "SELL"

    return "HOLD"


# ---------------------------------------------------------
# HAUPTSCHLEIFE
# ---------------------------------------------------------
print("🚀 XAUUSD Telegram-Signal-Bot gestartet! Warte auf Markt-Signale...")
send_telegram_message(
    "🤖 *Bot Gestartet:* Der XAUUSD Signal-Bot läuft jetzt und überwacht den Markt."
)

last_sent_signal = None

try:
    while True:
        signal = check_trade_signal()

        # Prüfen, ob ein neues Signal da ist (Spam-Schutz)
        if signal in ["BUY", "SELL"] and signal != last_sent_signal:
            tick = mt5.symbol_info_tick(symbol)
            price = tick.ask if signal == "BUY" else tick.bid
            current_time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

            # Nachricht für Telegram formatieren
            msg = (
                f"🚨 *NEUES SIGNAL ERKANNT*\n\n"
                f"📈 *Typ:* `{signal}`\n"
                f"🪙 *Symbol:* `{symbol}`\n"
                f"💰 *Aktueller Kurs:* `{price}`\n"
                f"⏰ *Zeit:* `{current_time}`"
            )

            print(f"\n[SIGNAL ERKANNT] {signal} bei {price}")

            # Signal direkt an Telegram senden
            send_telegram_message(msg)

            last_sent_signal = signal

        elif signal == "HOLD":
            last_sent_signal = "HOLD"

        time.sleep(60)  # Alle 60 Sekunden prüfen

except KeyboardInterrupt:
    print("Bot beendet.")
    send_telegram_message("🛑 *Bot Beendet:* Der Signal-Bot wurde gestoppt.")
    mt5.shutdown()
