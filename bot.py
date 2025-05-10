import os
import requests
import pandas as pd
import time
from twelvedata import TDClient

# Hämta miljövariabler
TOKEN = os.getenv('8011911124:AAE54JLc8CVfWX-yI7vmzwfLgdwPzNuSd3Q')  # Telegram Bot Token
CHAT_ID_1 = os.getenv('7515400567')  # Telegram Chat ID för första användaren
CHAT_ID_2 = os.getenv('5114921471')  # Telegram Chat ID för andra användaren
API_KEY = os.getenv('462fd8d1d6c84883b1ab94b057702558')  # Twelve Data API Key

td = TDClient(apikey=API_KEY)

# Valutapar och metaller som ska analyseras
symbols = [
    'EUR/USD', 'GBP/USD', 'AUD/USD', 'NZD/USD', 'USD/CHF',
    'EUR/GBP', 'EURAUD', 'GBPAUD', 'GBPNZD', 'AUDNZD',
    'XAU/USD', 'XAG/USD'  # Guld & Silver
]

def get_price_data(symbol, interval='1h', limit=200):
    try:
        ts = td.time_series(
            symbol=symbol,
            interval=interval,
            outputsize=limit,
            order='ASC'
        )
        df = ts.as_pandas()
        df = df[['open', 'high', 'low', 'close']]
        return df
    except Exception as e:
        print(f"[data_provider] Fel: {e}")
        return None

def send_message(text):
    chat_ids = [CHAT_ID_1, CHAT_ID_2]  # Lägg till flera Chat ID här om du vill ha fler användare
    for chat_id in chat_ids:
        url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
        payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()  # Kontrollera om HTTP-anropet misslyckades
        except requests.exceptions.RequestException as e:
            print(f"Fel vid sändning av meddelande till {chat_id}: {e}")


def send_signal(symbol, signal):
    text = f"📊 [{symbol}]\n{signal}"
    send_message(text)

def send_error_signal(message):
    send_message(f"⚠️ *Fel:* {message}")

def analyze_symbol(symbol, interval='1h'):
    df = get_price_data(symbol, interval, limit=200)

    if df is None or df.empty:
        return None

    # RSI och MACD beräkningar
    df['rsi'] = df['close'].rolling(window=14).apply(lambda x: (x[-1] - x.mean()) / x.std(), raw=True)
    df['macd'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
    df['macd_signal'] = df['macd'].ewm(span=9).mean()

    latest = df.iloc[-1]

    if latest['rsi'] < 30 and latest['macd'] > latest['macd_signal']:
        return "💰 *KÖP-signal!* RSI översålt och MACD bullish"
    elif latest['rsi'] > 70 and latest['macd'] < latest['macd_signal']:
        return "🚨 *SÄLJ-signal!* RSI överköpt och MACD bearish"
    else:
        return None

def analyze_symbols():
    for symbol in symbols:
        try:
            signal = analyze_symbol(symbol, interval='1h')
            if signal:
                send_signal(symbol, signal)
        except Exception as e:
            send_error_signal(f"Fel vid {symbol}: {str(e)}")

if __name__ == "__main__":
    while True:
        try:
            send_message("✅ *Signalboten är igång* – analyserar varje timme.")
            analyze_symbols()
        except Exception as e:
            send_error_signal(str(e))

        ANALYSIS_INTERVAL = 3600  # 1 timme i sekunder
time.sleep(ANALYSIS_INTERVAL)

