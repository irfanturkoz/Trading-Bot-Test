# data_fetcher.py
import requests
import pandas as pd
from datetime import datetime

def fetch_ohlcv(symbol: str, interval: str = '4h', limit: int = 100):
    """
    Binance Futures API'dan OHLCV verisi çeker ve pandas DataFrame olarak döndürür.
    """
    url = 'https://fapi.binance.com/fapi/v1/klines'
    params = {
        'symbol': symbol.upper(),
        'interval': interval,
        'limit': limit
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    # OHLCV verisini DataFrame'e çevir
    df = pd.DataFrame(data, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    # Tip dönüşümleri
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    return df[['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time']] 