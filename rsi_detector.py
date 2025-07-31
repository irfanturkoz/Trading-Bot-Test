# rsi_detector.py
import pandas as pd

def check_rsi(df, threshold=30, period=14):
    """
    RSI değeri belirtilen eşikten düşükse True döndürür, aksi halde False.
    """
    if len(df) < period + 1:
        return False
    close = df['close']
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    last_rsi = rsi.iloc[-1]
    return last_rsi < threshold 