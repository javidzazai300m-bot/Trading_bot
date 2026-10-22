import os
import requests
import yfinance as yf

# Deine Zugangsdaten (sicher in deinem privaten Repo)
TELEGRAM_TOKEN = "8909211837:AAGrhWS1umeFkIFkzbQlnuvmaP6eCGhiLVc"
TELEGRAM_CHAT_ID = "6551623158"


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Fehler beim Senden: {e}")


def check_live_markets():
    # Zu überwachende Assets (Beispiele: Gold Futures, Bitcoin, Ethereum)
    # Yahoo Finance Symbole: Gold = "GC=F", Bitcoin = "BTC-USD", Ethereum = "ETH-USD", XRP = "XRP-USD"
    assets = {
        "Gold (XAU/USD)": "GC=F",
        "Bitcoin (BTC)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "XRP (XRP)": "XRP-USD",
    }

    message = "🤖 <b>LIVE TRADING SIGNAL UPDATE</b>\n\n"

    for name, ticker_symbol in assets.items():
        try:
            ticker = yf.Ticker(ticker_symbol)
            df = ticker.history(period="5d", interval="1h")

            if df.empty:
                continue

            current_price = df["Close"].iloc[-1]
            prev_price = df["Close"].iloc[-2]

            # Einfache Trend-Logik (Vergleich zum vorherigen Stundenkerzen-Schlusskurs)
            is_bullish = current_price > prev_price
            status_text = (
                "🟢 <b>BULLISH TREND</b>" if is_bullish else "🔴 <b>BEARISH TREND</b>"
            )

            # Beispielhafte Zonen-Berechnung basierend auf dem aktuellen Preis
            bullish_entry = current_price * 0.995
            bullish_target = current_price * 1.015
            bearish_entry = current_price * 1.005
            bearish_target = current_price * 0.985

            message += (
                f"📊 <b>Markt-Signal: {name}</b>\n"
                f"💵 <b>Aktueller Preis:</b> {current_price:.2f}\n"
                f"📈 <b>Status:</b> {status_text}\n\n"
                f"🚀 <b>BULLISH ZONE (Kaufen):</b>\n"
                f"• Einstieg ab: `{bullish_entry:.2f}`\n"
                f"• Zielbereich: bis `{bullish_target:.2f}`\n\n"
                f"📉 <b>BEARISH ZONE (Verkaufen):</b>\n"
                f"• Einstieg ab: `{bearish_entry:.2f}`\n"
                f"• Zielbereich: bis `{bearish_target:.2f}`\n\n"
                f"----------------------------------\n"
            )
        except Exception as e:
            print(f"Fehler bei {name}: {e}")

    # Nachricht an Telegram senden
    send_telegram_message(message)


if __name__ == "__main__":
    check_live_markets()
