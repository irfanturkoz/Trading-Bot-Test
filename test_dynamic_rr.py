#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 Gelişmiş Dinamik R/R Sistemi Test Dosyası
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from botanlik import optimize_tp_sl_fixed, fetch_ohlcv, get_current_price
import pandas as pd
import numpy as np

def create_test_data():
    """Test için örnek OHLCV verisi oluştur"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='4H')
    
    # Volatil coin simülasyonu
    np.random.seed(42)
    base_price = 100
    prices = [base_price]
    
    for i in range(99):
        change = np.random.normal(0, 0.03)  # %3 volatilite
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1))  # Minimum 1
    
    # OHLCV verisi oluştur
    data = []
    for i, price in enumerate(prices):
        high = price * (1 + abs(np.random.normal(0, 0.01)))
        low = price * (1 - abs(np.random.normal(0, 0.01)))
        volume = np.random.uniform(1000000, 5000000)
        
        data.append({
            'timestamp': dates[i],
            'open': prices[i-1] if i > 0 else price,
            'high': high,
            'low': low,
            'close': price,
            'volume': volume
        })
    
    return pd.DataFrame(data)

def test_dynamic_rr():
    """Dinamik R/R sistemini test et"""
    print("GELISMIS DINAMIK R/R SISTEMI TESTI")
    print("=" * 60)
    
    # Test verisi oluştur
    df = create_test_data()
    current_price = df['close'].iloc[-1]
    
    # Test parametreleri
    entry_price = current_price
    current_tp = current_price * 1.05  # %5 yukarı
    current_sl = current_price * 0.97  # %3 aşağı
    
    # Fibonacci seviyeleri
    fibo_levels = {
        '0.236': current_price * 1.02,
        '0.382': current_price * 1.04,
        '0.5': current_price * 1.06,
        '0.618': current_price * 1.08,
        '0.786': current_price * 1.10,
        '1.0': current_price * 1.12,
        '1.272': current_price * 1.15
    }
    
    # Bollinger Bands
    bb_data = {
        'upper_band': current_price * 1.08,
        'lower_band': current_price * 0.92,
        'middle_band': current_price
    }
    
    print(f"Test Parametreleri:")
    print(f"   Entry: ${current_price:.4f}")
    print(f"   Mevcut TP: ${current_tp:.4f}")
    print(f"   Mevcut SL: ${current_sl:.4f}")
    print()
    
    # Farklı formasyon türleri ile test
    formations = ['TOBO', 'OBO', 'WEDGE', 'TRIANGLE', 'FLAG', 'CUP']
    
    print("FORMASYON BAZLI R/R TESTLERI:")
    print("-" * 60)
    
    for formation in formations:
        print(f"\n{formation} Formasyonu:")
        
        # 5 farklı test yap
        for i in range(5):
            try:
                optimized_tp, optimized_sl, optimized_rr = optimize_tp_sl_fixed(
                    entry_price=entry_price,
                    current_tp=current_tp,
                    current_sl=current_sl,
                    direction='Long',
                    fibo_levels=fibo_levels,
                    bb_data=bb_data,
                    df=df,
                    formation_type=formation
                )
                
                # Sonuçları göster
                tp_gain = (optimized_tp - entry_price) / entry_price * 100
                sl_loss = (entry_price - optimized_sl) / entry_price * 100
                
                print(f"   Test {i+1}: R/R={optimized_rr:.2f} | TP=+%{tp_gain:.1f} | SL=-%{sl_loss:.1f}")
                
            except Exception as e:
                print(f"   Test {i+1}: HATA - {e}")
    
    print("\n" + "=" * 60)
    print("Test tamamlandi!")
    
    # Ozet istatistikler
    print(f"\nSISTEM OZELLIKLERI:")
    print(f"   - Volatilite bazli dinamik hesaplama")
    print(f"   - Trend gucu analizi (ADX + MA)")
    print(f"   - Momentum skoru (RSI + MACD)")
    print(f"   - Formasyon bazli carpanlar")
    print(f"   - Akilli teknik seviye secimi")
    print(f"   - R/R Araligi: 1.1 - 3.5 (dinamik)")

if __name__ == "__main__":
    test_dynamic_rr()
