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
    df["rsi"] = df["Close"].rolling(14).apply(lambda x: (x[-1] - x.mean()) / x.std(), raw=True)
    df["macd"] = df["Close"].
