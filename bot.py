import os
import requests
import pandas as pd
import yfinance as yf
import time

# Hämta miljövariabler
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID_1 = os.getenv('TELEGRAM_CHAT_ID_1')
CHAT_ID_2 = os.getenv('TELEGRAM_CHAT_ID_2')


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=payload)
    if not response.ok:
        print(f"Fel vid sändning av meddelande: {response.status_code}, {response.text}")


def send_error_signal(message):
    send_message(CHAT_ID_1, f"⚠️ *Fel:* {message}")
    send_message(CHAT_ID_2, f"⚠️ *Fel:* {message}")


# Valutapar, råvaror och index som ska analyseras
symbols = [
    'EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'NZDUSD=X', 'USDCHF=X',
    'EURGBP=X', 'EURAUD=X', 'GBPAUD=X', 'GBPNZD=X', 'AUDNZD=X',
    'GC=F', 'SI=F', 'BZ=F',  # Brent olja, Guld, Silver
    '^GSPC', '^DJI', '^IXIC'  # S&P500, Dow Jones, Nasdaq
]


def send_signal(symbol, signal):
    text = f"📊 [{symbol}]\n{signal}"
    send_message(CHAT_ID_1, text)
    send_message(CHAT_ID_2, text)


def get_price_data(symbol, interval='1h', period='1mo'):
    try:
        df = yf.download(symbol, interval=interval, period=period)
        df = df[['Open', 'High', 'Low', 'Close']]
        return df
    except Exception as e:
        send_error_signal(f"[data_provider] Fel: {e}")
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

    return df.dropna()


def analyze_symbol(symbol):
    df = get_price_data(symbol, interval='1h', period='1mo')
    if df is None or df.empty:
        return None

    if len(df) < 30:
        send_error_signal(f"[{symbol}] Fel: För lite data ({len(df)} rader)")
        return None

    df = calculate_indicators(df)
    if df.empty:
        send_error_signal(f"[{symbol}] Fel: Data saknar indikatorvärden (RSI/MACD)")
        return None

    latest = df.iloc[-1]

    try:
        rsi = latest['rsi']
        macd = latest['macd']
        macd_signal = latest['macd_signal']

        if pd.notna(rsi) and pd.notna(macd) and pd.notna(macd_signal):
            if rsi < 30 and macd > macd_signal:
                return "💰 *KÖP-signal!* RSI översålt och MACD bullish"
            elif rsi > 70 and macd < macd_signal:
                return "🚨 *SÄLJ-signal!* RSI överköpt och MACD bearish"
    except Exception as e:
        send_error_signal(f"[{symbol}] Fel vid analys: {str(e)}")

    return None


def analyze_symbols():
    for symbol in symbols:
        try:
            signal = analyze_symbol(symbol)
            if signal:
                send_signal(symbol, signal)
        except Exception as e:
            send_error_signal(f"Fel vid {symbol}: {str(e)}")


def notify_start():
    send_message(CHAT_ID_1, "✅ *Signalboten är igång* – analyserar varje timme.")
    send_message(CHAT_ID_2, "✅ *Signalboten är igång* – analyserar varje timme.")


if __name__ == "__main__":
    try:
        notify_start()
        while True:
            analyze_symbols()
            time.sleep(3600)  # Väntar 1 timme
    except Exception as e:
        send_error_signal(f"Fel: {str(e)}")
