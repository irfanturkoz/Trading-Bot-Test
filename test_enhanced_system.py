#!/usr/bin/env python3
"""
GELİŞMİŞ FORMASYON ANALİZ SİSTEMİ TEST DOSYASI
================================================

Bu dosya, geliştirilmiş formasyon analiz sisteminin tüm yeni özelliklerini test eder:

1. Zaman Filtresi
2. Yükseklik Filtresi  
3. Gelişmiş R/R Hesaplama
4. 400 Puanlık Kalite Skorlama
5. Gelişmiş Log Sistemi
6. Sinyal Üretimi

Author: Trading Bot Team
Version: 5.0
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime
from advanced_formation_analyzer import AdvancedFormationAnalyzer

def fetch_test_data(symbol: str = 'BTCUSDT', interval: str = '4h', limit: int = 200) -> pd.DataFrame:
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

def test_time_filter():
    """
    Zaman filtresi testi
    """
    print("🔍 ZAMAN FİLTRESİ TESTİ")
    print("=" * 40)
    
    analyzer = AdvancedFormationAnalyzer()
    
    # Test verisi oluştur
    test_data = pd.DataFrame({
        'open': [100] * 50,
        'high': [105] * 50,
        'low': [95] * 50,
        'close': [102] * 50,
        'volume': [1000] * 50
    })
    
    # Farklı formasyon tipleri için test
    formation_types = ['TOBO', 'FALLING_WEDGE', 'CUP_HANDLE']
    
    for formation_type in formation_types:
        print(f"\n📊 {formation_type} zaman filtresi testi:")
        
        # Test formasyon verisi
        test_formation = {
            'type': formation_type,
            'sol_omuz_index': 0,
            'sag_omuz_index': 25,  # 25 mum
            'high_points': [0, 10, 20],
            'low_points': [5, 15, 25],
            'cup_start': 0,
            'handle_end': 30
        }
        
        # Zaman doğrulama testi
        time_validation = analyzer.validate_formation_time_duration(test_data, test_formation)
        
        print(f"   ⏰ Mum sayısı: {time_validation['details'].get('candle_count', 0)}")
        print(f"   🕐 Saat süresi: {time_validation['details'].get('hours_duration', 0)}")
        print(f"   ✅ Geçerli mi: {time_validation['is_valid']}")
        print(f"   📊 Zaman skoru: {time_validation['score']}/100")
        
        if not time_validation['is_valid']:
            print(f"   ❌ Reddetme nedeni: {time_validation['rejection_reason']}")

def test_height_filter():
    """
    Yükseklik filtresi testi
    """
    print("\n🔍 YÜKSEKLİK FİLTRESİ TESTİ")
    print("=" * 40)
    
    analyzer = AdvancedFormationAnalyzer()
    
    # Test verisi
    test_data = pd.DataFrame({
        'open': [100] * 50,
        'high': [105] * 50,
        'low': [95] * 50,
        'close': [102] * 50,
        'volume': [1000] * 50
    })
    
    # Farklı yükseklik testleri
    height_tests = [
        {'name': 'Küçük formasyon (%1)', 'height': 1.0, 'expected': False},
        {'name': 'Minimum formasyon (%2)', 'height': 2.0, 'expected': True},
        {'name': 'Orta formasyon (%3)', 'height': 3.0, 'expected': True},
        {'name': 'Büyük formasyon (%5)', 'height': 5.0, 'expected': True}
    ]
    
    for test in height_tests:
        print(f"\n📊 {test['name']} testi:")
        
        # Test formasyon verisi
        test_formation = {
            'type': 'TOBO',
            'bas': 100 - test['height'],  # Baş fiyatı
            'boyun': 100,  # Boyun fiyatı
            'sol_omuz': 100.5,
            'sag_omuz': 100.5
        }
        
        # Boyut doğrulama testi
        size_validation = analyzer.validate_formation_size(test_data, test_formation)
        
        print(f"   📏 Yükseklik: %{test['height']:.1f}")
        print(f"   ✅ Geçerli mi: {size_validation['is_valid']}")
        print(f"   📊 Yapısal skor: {size_validation['score']}/100")
        
        if size_validation['is_valid'] != test['expected']:
            print(f"   ⚠️ Beklenen: {test['expected']}, Gerçek: {size_validation['is_valid']}")

def test_rr_calculation():
    """
    R/R hesaplama testi
    """
    print("\n🔍 R/R HESAPLAMA TESTİ")
    print("=" * 40)
    
    analyzer = AdvancedFormationAnalyzer()
    
    entry_price = 100.0
    
    # Farklı formasyon tipleri için R/R testi
    formation_types = ['TOBO', 'FALLING_WEDGE', 'CUP_HANDLE']
    
    for formation_type in formation_types:
        print(f"\n📊 {formation_type} R/R testi:")
        
        test_formation = {'type': formation_type}
        
        # R/R hesaplama
        rr_levels = analyzer.calculate_rr_levels(entry_price, formation_type, test_formation)
        
        print(f"   💰 Giriş fiyatı: {entry_price}")
        print(f"   🎯 TP: {rr_levels['tp']:.4f}")
        print(f"   🛑 SL: {rr_levels['sl']:.4f}")
        print(f"   📊 R/R oranı: {rr_levels['rr_ratio']:.2f}:1")
        
        # Hedef aralık kontrolü
        target_rr = analyzer.rr_targets[formation_type]
        rr_ratio = rr_levels['rr_ratio']
        
        if target_rr['min'] <= rr_ratio <= target_rr['max']:
            print(f"   ✅ Hedef aralıkta: {target_rr['min']}-{target_rr['max']}")
        else:
            print(f"   ❌ Hedef aralık dışında: {target_rr['min']}-{target_rr['max']}")

def test_quality_scoring():
    """
    Kalite skorlama testi
    """
    print("\n🔍 KALİTE SKORLAMA TESTİ")
    print("=" * 40)
    
    analyzer = AdvancedFormationAnalyzer()
    
    # Test verisi
    test_data = pd.DataFrame({
        'open': [100] * 50,
        'high': [105] * 50,
        'low': [95] * 50,
        'close': [102] * 50,
        'volume': [1000] * 50
    })
    
    # Test formasyon verisi
    test_formation = {
        'type': 'TOBO',
        'bas': 98,  # %2 yükseklik
        'boyun': 100,
        'sol_omuz': 100.5,
        'sag_omuz': 100.5,
        'sol_omuz_index': 0,
        'sag_omuz_index': 25
    }
    
    # Kalite skoru hesaplama
    quality_result = analyzer.calculate_quality_score(test_data, 'TOBO', test_formation)
    
    print(f"📊 Toplam kalite skoru: {quality_result['total_score']}/400")
    print(f"✅ Yüksek kaliteli mi: {quality_result['is_high_quality']}")
    
    # Detay skorları
    score_details = quality_result['score_details']
    print(f"\n📋 Detay Skorları:")
    print(f"   ⏰ Zaman: {score_details.get('time_score', 0)}/100")
    print(f"   📊 Yapısal: {score_details.get('structural_score', 0)}/100")
    print(f"   📈 Hacim: {score_details.get('volume_score', 0)}/100")
    print(f"   📉 Osilatör: {score_details.get('oscillator_score', 0)}/100")
    print(f"   🎯 R/R: {score_details.get('rr_score', 0)}/100")
    
    # Reddetme nedenleri
    if not quality_result['is_high_quality']:
        print(f"\n❌ Reddetme Nedenleri:")
        for reason in quality_result['rejection_reasons']:
            print(f"   🚫 {reason}")

def test_signal_generation():
    """
    Sinyal üretimi testi
    """
    print("\n🔍 SİNYAL ÜRETİMİ TESTİ")
    print("=" * 40)
    
    analyzer = AdvancedFormationAnalyzer()
    
    # Test sembolleri
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    for symbol in test_symbols:
        print(f"\n📊 {symbol} sinyal testi:")
        
        # Veri çek
        df = fetch_test_data(symbol, '4h', 100)
        if df.empty:
            print(f"   ❌ {symbol} için veri alınamadı")
            continue
        
        # Sembol analizi
        result = analyzer.analyze_symbol(symbol, '4h')
        
        if result['success']:
            print(f"   ✅ Sinyal üretildi!")
            print(f"   🎯 Kalite skoru: {result.get('quality_score', 0)}/400")
            
            # Sinyal mesajını göster
            if 'signal_message' in result:
                print("\n" + "="*50)
                print("🚨 TEST SİNYALİ")
                print("="*50)
                print(result['signal_message'])
                print("="*50)
        else:
            print(f"   ❌ Sinyal üretilemedi: {result.get('error', 'Bilinmeyen hata')}")

def demonstrate_system_features():
    """
    Sistem özelliklerini gösterir
    """
    print("🚀 GELİŞMİŞ FORMASYON ANALİZ SİSTEMİ 5.0")
    print("=" * 60)
    print("📋 YENİ ÖZELLİKLER:")
    print()
    print("1. 🔍 ZAMAN FİLTRESİ:")
    print("   ✅ TOBO/OBO: Minimum 20 mum / 12-48 saat")
    print("   ✅ Wedge/Flag: Minimum 25 mum / 15-60 saat")
    print("   ✅ Cup and Handle: Minimum 30 mum / 20-72 saat")
    print("   ✅ 5-10 mum arası kısa formasyonlar geçersiz")
    print()
    print("2. 📏 YÜKSEKLİK FİLTRESİ:")
    print("   ✅ Minimum %2 formasyon boyutu zorunlu")
    print("   ✅ Küçük yapay formasyonlar filtrelenir")
    print("   ✅ Formasyon yüksekliği skorlamaya dahil")
    print()
    print("3. 📊 R/R HESAPLAMA:")
    print("   ✅ TOBO/OBO: 1.3-1.7 arası")
    print("   ✅ Wedge/Flag: 1.5-2.0 arası")
    print("   ✅ Cup and Handle: 1.8-2.5 arası")
    print("   ✅ SL sabit %1.5 mesafede")
    print()
    print("4. 🎯 KALİTE SKORLAMA (400 puan):")
    print("   ✅ Zaman süresi: 0-100 puan")
    print("   ✅ Yapısal doğruluk: 0-100 puan")
    print("   ✅ Hacim teyidi: 0-100 puan")
    print("   ✅ Osilatör uyumu: 0-100 puan")
    print("   ✅ R/R doğruluğu: 0-100 puan")
    print("   ✅ Minimum 250/400 puan zorunlu")
    print()
    print("5. 📝 GELİŞMİŞ LOG SİSTEMİ:")
    print("   ✅ Detaylı analiz bilgileri")
    print("   ✅ Reddetme nedenleri")
    print("   ✅ Skor detayları")
    print("   ✅ Sinyal üretimi")
    print()
    print("6. 🚨 SİNYAL ÜRETİMİ:")
    print("   ✅ Formasyon tipi ve yönü")
    print("   ✅ Süre bilgileri")
    print("   ✅ Hacim artış oranı")
    print("   ✅ RSI/MACD uyumu")
    print("   ✅ TP1, TP2, TP3 ve SL seviyeleri")
    print("   ✅ R/R oranı")
    print("   ✅ Kalite skoru")
    print("=" * 60)

def main():
    """
    Ana test fonksiyonu
    """
    print("🧪 GELİŞMİŞ FORMASYON ANALİZ SİSTEMİ TESTİ")
    print("=" * 60)
    
    # Sistem özelliklerini göster
    demonstrate_system_features()
    
    # Testleri çalıştır
    print("\n🔬 TESTLER BAŞLATILIYOR...")
    print("=" * 60)
    
    # 1. Zaman filtresi testi
    test_time_filter()
    
    # 2. Yükseklik filtresi testi
    test_height_filter()
    
    # 3. R/R hesaplama testi
    test_rr_calculation()
    
    # 4. Kalite skorlama testi
    test_quality_scoring()
    
    # 5. Sinyal üretimi testi
    test_signal_generation()
    
    print("\n✅ TÜM TESTLER TAMAMLANDI!")
    print("📝 Not: Bu sistem gerçek trading için kullanılmamalıdır.")

if __name__ == "__main__":
    main() 