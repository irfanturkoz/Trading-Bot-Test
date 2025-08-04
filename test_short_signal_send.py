#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GERÇEK SHORT SİNYAL GÖNDERİMİ TEST
====================================

Bu script gerçek bir SHORT sinyal oluşturur ve Telegram'a gönderir.
"""

from signal_visualizer import SignalVisualizer
from utils import format_price
import pandas as pd
import numpy as np

def test_short_signal_send():
    """Gerçek SHORT sinyal gönderimi testi"""
    
    print("🔻 GERÇEK SHORT SİNYAL GÖNDERİMİ TESTİ")
    print("=" * 50)
    
    visualizer = SignalVisualizer()
    
    # Test verisi oluştur
    symbol = "STOUSDT"
    entry_price = 0.085970
    direction = "Short"
    formation_type = "OBO"
    
    # Sahte OHLCV verisi oluştur
    dates = pd.date_range(start='2025-08-01', periods=100, freq='1H')
    np.random.seed(42)  # Tekrarlanabilir sonuçlar için
    
    # Düşen trend için veri
    base_price = 0.09
    trend = np.linspace(base_price, entry_price, 100)
    noise = np.random.normal(0, 0.002, 100)
    close_prices = trend + noise
    
    # OHLCV verisi oluştur
    data = []
    for i in range(100):
        close = close_prices[i]
        high = close + abs(np.random.normal(0, 0.001))
        low = close - abs(np.random.normal(0, 0.001))
        open_price = close + np.random.normal(0, 0.0005)
        volume = np.random.uniform(1000, 5000)
        
        data.append({
            'timestamp': dates[i],
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    
    # Formasyon verisi
    formation_data = {
        'type': formation_type,
        'direction': direction,
        'quality_score': 345,
        'entry_price': entry_price,
        'neckline': entry_price * 0.99,  # Boyun çizgisi
        'sol_omuz': entry_price * 1.02,
        'bas': entry_price * 0.98,
        'sag_omuz': entry_price * 1.01
    }
    
    print(f"📊 Sembol: {symbol}")
    print(f"💰 Giriş Fiyatı: {format_price(entry_price)}")
    print(f"🔴 Yön: {direction}")
    print(f"🔍 Formasyon: {formation_type}")
    print()
    
    # Grafik oluştur
    filename = visualizer.create_candlestick_chart(df, formation_type, formation_data, 
                                                 entry_price, direction, symbol)
    
    if filename:
        print(f"✅ Grafik oluşturuldu: {filename}")
        
        # Telegram mesajı oluştur
        levels = visualizer.calculate_target_levels(entry_price, direction, formation_data)
        message = visualizer.create_signal_message(symbol, formation_type, entry_price, direction, levels, formation_data)
        
        print("📱 Telegram mesajı hazırlandı!")
        print("-" * 30)
        print(message[:200] + "...")  # İlk 200 karakter
        print("-" * 30)
        
        # Telegram'a gönder
        try:
            from telegram_notifier import send_telegram_message
            send_telegram_message(message, filename)
            print(f"✅ SHORT sinyali Telegram'a gönderildi!")
        except Exception as e:
            print(f"❌ Telegram gönderim hatası: {e}")
    else:
        print("❌ Grafik oluşturulamadı!")
    
    print()
    print("🎯 TEST TAMAMLANDI!")

if __name__ == "__main__":
    test_short_signal_send() 