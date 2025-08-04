#!/usr/bin/env python3
"""
Falling Wedge Formasyon Tespit Testi

Bu dosya, is_falling_wedge fonksiyonunun nasıl çalıştığını gösterir
ve tüm kriterleri test eder.
"""

import pandas as pd
import numpy as np
import requests
from formation_detector import is_falling_wedge

def fetch_test_data(symbol: str = 'BTCUSDT', interval: str = '1h', limit: int = 200) -> pd.DataFrame:
    """
    Test için veri çeker
    """
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df
        
    except Exception as e:
        print(f"❌ Veri alınamadı: {e}")
        return pd.DataFrame()

def test_falling_wedge_detection():
    """
    Falling Wedge tespit fonksiyonunu test eder
    """
    print("🔍 Falling Wedge Formasyon Tespit Testi")
    print("=" * 50)
    
    # Test sembolleri
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT']
    
    for symbol in test_symbols:
        print(f"\n📊 {symbol} analiz ediliyor...")
        
        # Veri çek
        df = fetch_test_data(symbol)
        if df.empty:
            print(f"❌ {symbol} için veri alınamadı")
            continue
        
        print(f"✅ {len(df)} mum verisi alındı")
        
        # Falling Wedge tespiti (debug modu açık)
        result = is_falling_wedge(df, debug_mode=True)
        
        if result:
            print(f"✅ {symbol} için Falling Wedge tespit edildi!")
            print(f"   📈 Giriş Fiyatı: {result['entry_price']:.4f}")
            print(f"   🎯 TP: {result['tp']:.4f}")
            print(f"   🛑 SL: {result['sl']:.4f}")
            print(f"   📊 R/R Oranı: {result['rr_ratio']:.2f}:1")
            print(f"   🏆 Kalite Skoru: {result['quality_score']}/400")
            print(f"   💪 Formasyon Gücü: {result['score']}/100")
        else:
            print(f"❌ {symbol} için Falling Wedge tespit edilmedi")
        
        print("-" * 30)

def demonstrate_function_criteria():
    """
    Fonksiyonun kriterlerini açıklar
    """
    print("\n📋 Falling Wedge Tespit Kriterleri:")
    print("=" * 50)
    
    criteria = [
        "1. Lower highs kontrolü - Her yüksek bir öncekinden düşük olmalı",
        "2. Lower lows kontrolü - Her düşük bir öncekinden düşük olmalı", 
        "3. Üst trend çizgisi - Yüksekleri birleştiren çizgi hesaplanır",
        "4. Alt trend çizgisi - Düşükleri birleştiren çizgi hesaplanır",
        "5. Daralan kanal kontrolü - İki çizgi birbirine yakınsamalı",
        "6. Hacim düşüşü kontrolü - Formasyon boyunca hacim azalmalı",
        "7. Kırılım kontrolü - Fiyat üst trend çizgisini yukarı kırmalı",
        "8. Minimum güç skoru - En az 60/100 puan gerekli",
        "9. Kalite skoru - 400 puanlık sistemde değerlendirilir"
    ]
    
    for criterion in criteria:
        print(f"   {criterion}")
    
    print("\n🎯 Fonksiyon Özellikleri:")
    print("   ✅ Modüler tasarım - Yardımcı fonksiyonlar kullanır")
    print("   ✅ Debug modu - Detaylı analiz bilgileri")
    print("   ✅ Esnek parametreler - min_touches, volume_confirmation, breakout_check")
    print("   ✅ Kapsamlı skorlama - Formasyon gücü ve kalite skoru")
    print("   ✅ TP/SL hesaplama - Otomatik hedef seviyeleri")
    print("   ✅ R/R oranı - Risk/Ödül hesaplaması")

def main():
    """
    Ana test fonksiyonu
    """
    print("🚀 Falling Wedge Formasyon Tespit Sistemi")
    print("=" * 60)
    
    # Kriterleri açıkla
    demonstrate_function_criteria()
    
    # Test yap
    test_falling_wedge_detection()
    
    print("\n✅ Test tamamlandı!")
    print("\n📝 Not: Bu fonksiyon mevcut sistemde kullanılmaktadır.")
    print("   - advanced_formation_analyzer.py içinde entegre edilmiştir")
    print("   - signal_visualizer.py içinde görselleştirme desteği vardır")
    print("   - botanlik.py içinde ana analiz döngüsünde kullanılır")

if __name__ == "__main__":
    main() 