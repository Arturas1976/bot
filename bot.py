import os
import time
import requests
import yfinance as yf
import pandas as pd

# Telegram miljövariabler
TOKEN = os.getenv("8011911124:AAE54JLc8CVfWX-yI7vmzwfLgdwPzNuSd3Q")  # t.ex. '123456789:ABC...'
CHAT_IDS = os.getenv("7515400567", "5114921471").split(",")  # flera ID med komma

# Valutapar
forex_pairs = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "AUDUSD=X", "NZDUSD=X",
    "USDCAD=X", "EURGBP=X", "EURJPY=X", "GBPJPY=X", "AUDJPY=X", "CHFJPY=X"
]

# Råvaror
commodities = [
    "GC=F",   # Gold
    "SI=F",   # Silver
    "CL=F",   # Crude Oil
    "HG=F",   # Copper
    "PL=F",   # Platinum
    "PA=F"    # Palladium
]

# Index
indices = [
    "^GSPC", "^DJI", "^IXIC", "^FTSE", "^N225", "^GDAXI", "^FCHI", "^STOXX50E"
]

# Kombinera alla
symbols = forex_pairs + commodities + indices


def send_telegram_message(text):
    for chat_id in CHAT_IDS:
        if not chat_id:
            continue
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": chat_id.strip(), "text": text, "parse_mode": "Markdown"}
        try:
            requests.post(url, data=payload)
        except Exception as e:
            print(f"[Telegram] Fel: {e}")


def get_data(symbol, interval="1h", period="7d"):
    try:
        df = yf.download(tickers=symbol, interval=interval, period=period)
        return df[['Open', 'High', 'Low', 'Close']]
    except Exception as e:
        print(f"[Data] Fel för {symbol}: {e}")
        return None


def calculate_indicators(df):
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()

    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    exp1 = df["Close"].ewm(span=12, adjust=False).mean()
    exp2 = df["Close"].ewm(span=26, adjust=False).mean()
    df["macd"] = exp1 - exp2
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    return df

# Analysera varje symbol och skicka signaler
def analyze_symbol(symbol):
    df = get_price_data(symbol, interval='1h', period='1mo')
    if df is None or df.empty:
        return None

    df = calculate_indicators(df)
    latest = df.iloc[-1]

    if latest['rsi'] < 30 and latest['macd'] > latest['macd_signal']:
        return "💰 *KÖP-signal!* RSI översålt och MACD bullish"
    elif latest['rsi'] > 70 and latest['macd'] < latest['macd_signal']:
        return "🚨 *SÄLJ-signal!* RSI överköpt och MACD bearish"
    else:
        return None

# Huvudanalysfunktionen som körs för alla symboler
def analyze_symbols():
    for symbol in symbols:
        try:
            signal = analyze_symbol(symbol)
            if signal:
                send_signal(symbol, signal)
        except Exception as e:
            send_error_signal(f"Fel vid {symbol}: {str(e)}")

# Skicka ett meddelande när boten startar
def notify_start():
    send_message("✅ *Signalboten är igång* – analyserar varje timme.")

# Huvudloop som körs för att analysera varje timme
if __name__ == "__main__":
    try:
        notify_start()
        while True:
            analyze_symbols()
            time.sleep(3600)  # Väntar 1 timme innan nästa analys
    except Exception as e:
        send_error_signal(f"Fel: {str(e)}")

