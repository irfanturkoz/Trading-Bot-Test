# test_multitimeframe.py
import pandas as pd
import numpy as np
from formation_detector import (
    detect_tobo, detect_obo, detect_falling_wedge,
    analyze_multiple_timeframes, get_multiple_timeframe_data, 
    format_multitimeframe_analysis_result
)
from data_fetcher import fetch_ohlcv

def test_multitimeframe_analysis():
    """
    Çoklu zaman dilimi analiz fonksiyonlarını test eder
    """
    print("🔍 Çoklu Zaman Dilimi Analizi Test Ediliyor...")
    print("📊 Zaman Dilimleri: 1h, 4h, 1d, 1w")
    print("🎯 Kriter: En az 2 zaman diliminde onay")
    print("=" * 70)
    
    # Test için örnek veri oluştur
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    for symbol in test_symbols:
        print(f"\n📊 {symbol} Çoklu Zaman Dilimi Analizi:")
        print("=" * 50)
        
        try:
            # Çoklu zaman dilimi verisi çek
            df_dict = get_multiple_timeframe_data(symbol, ['1h', '4h', '1d', '1w'])
            
            # Veri kontrolü
            valid_timeframes = [tf for tf, df in df_dict.items() if df is not None and not df.empty]
            print(f"✅ Veri çekildi: {len(valid_timeframes)}/4 zaman dilimi")
            print(f"📈 Mevcut zaman dilimleri: {valid_timeframes}")
            
            if len(valid_timeframes) < 2:
                print(f"❌ Yetersiz veri - en az 2 zaman dilimi gerekli")
                continue
            
            # Her formasyon tipi için çoklu zaman dilimi analizi
            formation_types = ['TOBO', 'OBO', 'FALLING_WEDGE']
            
            for formation_type in formation_types:
                print(f"\n🎯 {formation_type} Formasyonu Analizi:")
                
                # Çoklu zaman dilimi analizi
                result = analyze_multiple_timeframes(df_dict, formation_type, symbol)
                
                if result['final_decision']:
                    print(f"✅ ONEYLENDİ! {formation_type} formasyonu")
                    print(f"📊 Onay Sayısı: {result['total_confirmations']}/4")
                    print(f"📈 Ortalama Skor: %{result['avg_score']:.1f}")
                    print(f"🎯 Sinyal Yönü: {result['final_signal']}")
                    print(f"🔒 Güven Seviyesi: {result['confidence_level']}")
                    
                    # Detaylı sonuç
                    print("\n📋 Zaman Dilimi Detayları:")
                    for tf, tf_result in result['timeframe_results'].items():
                        if tf_result['detected']:
                            status = "✅" if tf_result['confirmed'] else "⚠️"
                            print(f"   {status} {tf}: %{tf_result['score_percentage']:.1f} ({tf_result['confidence']})")
                        else:
                            print(f"   ❌ {tf}: {tf_result['confidence']}")
                    
                    # Formatlanmış sonuç
                    print("\n📝 Formatlanmış Sonuç:")
                    formatted_result = format_multitimeframe_analysis_result(result)
                    print(formatted_result)
                    
                else:
                    print(f"❌ REDDEDİLDİ! {formation_type} formasyonu")
                    print(f"📊 Onay Sayısı: {result['total_confirmations']}/4 (minimum 2 gerekli)")
                    print(f"📈 Ortalama Skor: %{result['avg_score']:.1f}")
                    
                    # Hata varsa göster
                    if 'error' in result:
                        print(f"❌ Hata: {result['error']}")
            
            print("\n" + "=" * 50)
            
        except Exception as e:
            print(f"❌ {symbol} analizi sırasında hata: {str(e)}")
    
    print("\n✅ Test tamamlandı!")
    print("\n🎯 Yeni Özellikler:")
    print("   • 4 farklı zaman dilimi analizi (1h, 4h, 1d, 1w)")
    print("   • En az 2 zaman diliminde onay kriteri")
    print("   • Çoğunluk kuralı ile sinyal yönü belirleme")
    print("   • Güvenilirlik seviyesi (2/3/4 onay)")
    print("   • Detaylı zaman dilimi raporlama")

if __name__ == "__main__":
    test_multitimeframe_analysis() 