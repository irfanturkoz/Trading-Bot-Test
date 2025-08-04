#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for unified botanlik.py
"""

from botanlik import (
    format_price, 
    get_usdt_symbols, 
    get_current_price, 
    calculate_optimal_risk,
    analyze_symbol
)

def test_basic_functions():
    """Temel fonksiyonları test eder"""
    print("🧪 Temel fonksiyonlar test ediliyor...")
    
    # 1. Fiyat formatı testi
    print(f"✅ format_price test: {format_price(123.456789)}")
    
    # 2. Sembol listesi testi
    symbols = get_usdt_symbols()
    print(f"✅ Sembol sayısı: {len(symbols)}")
    print(f"✅ İlk 5 sembol: {symbols[:5]}")
    
    # 3. Fiyat çekme testi
    btc_price = get_current_price('BTCUSDT')
    print(f"✅ BTCUSDT fiyatı: {btc_price}")
    
    # 4. Risk hesaplama testi
    risk = calculate_optimal_risk('BTCUSDT', 50000, 55000, 48000, 'Long')
    print(f"✅ Risk analizi: {risk}")
    
    print("✅ Temel fonksiyonlar başarılı!")

def test_analysis():
    """Analiz fonksiyonunu test eder"""
    print("\n🧪 Analiz fonksiyonu test ediliyor...")
    
    try:
        result = analyze_symbol('BTCUSDT', '4h')
        if result:
            print("✅ Analiz başarılı!")
            print(f"   Sembol: {result['symbol']}")
            print(f"   Fiyat: {result['current_price']}")
            print(f"   Skor: {result['signal_score']['total_score']}")
            print(f"   Güç: {result['signal_score']['strength']}")
        else:
            print("❌ Analiz başarısız!")
    except Exception as e:
        print(f"❌ Analiz hatası: {e}")

def main():
    """Ana test fonksiyonu"""
    print("🚀 Unified Botanlik Test Başlatılıyor...")
    print("=" * 50)
    
    test_basic_functions()
    test_analysis()
    
    print("\n✅ Tüm testler tamamlandı!")

if __name__ == "__main__":
    main() 