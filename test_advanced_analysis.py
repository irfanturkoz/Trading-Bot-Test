# test_advanced_analysis.py
import pandas as pd
import numpy as np
from formation_detector import (
    detect_tobo, detect_obo, detect_falling_wedge,
    analyze_rsi_formation_strength, analyze_macd_breakout_signal, 
    analyze_volume_pattern, calculate_formation_score,
    analyze_breakout_candle, calculate_formation_geometric_score, backtest_formation_success_rate
)
from data_fetcher import fetch_ohlcv

def test_advanced_analysis():
    """
    Yeni RSI, MACD, hacim, breakout, geometrik skor ve backtest analiz fonksiyonlarını test eder
    """
    print("🔍 Gelişmiş Analiz Fonksiyonları Test Ediliyor...")
    print("📊 Yeni Özellikler: Breakout Analizi, Geometrik Skor, Backtest")
    print("=" * 70)
    
    # Test için örnek veri oluştur
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    for symbol in test_symbols:
        print(f"\n📊 {symbol} Analizi:")
        print("=" * 50)
        
        try:
            # Veri çek
            df = fetch_ohlcv(symbol, '4h')
            if df is None or df.empty:
                print(f"❌ {symbol} için veri çekilemedi")
                continue
            
            print(f"✅ Veri çekildi: {len(df)} mum")
            
            # Formasyonları tespit et
            tobo = detect_tobo(df)
            obo = detect_obo(df)
            falling_wedge = detect_falling_wedge(df)
            
            # Her formasyon için detaylı analiz
            formations = [
                ('TOBO', tobo),
                ('OBO', obo),
                ('FALLING_WEDGE', falling_wedge)
            ]
            
            for formation_type, formation_data in formations:
                if formation_data:
                    print(f"\n🎯 {formation_type} Formasyonu Tespit Edildi!")
                    
                    # Yeni skorlama sistemi
                    if 'total_score' in formation_data:
                        print(f"📈 Toplam Skor: {formation_data['total_score']}/{formation_data['max_score']}")
                        print(f"📊 Skor Yüzdesi: {formation_data['score_percentage']:.1f}%")
                        print(f"🎯 Güven Seviyesi: {formation_data['confidence']}")
                        print(f"📈 Sinyal Yönü: {formation_data['signal_direction']}")
                        
                        # RSI Analizi
                        if 'rsi_analysis' in formation_data:
                            rsi = formation_data['rsi_analysis']
                            print(f"📉 RSI: {rsi['current_rsi']:.1f} ({rsi['rsi_signal']})")
                            for signal in rsi['rsi_signals']:
                                print(f"   {signal}")
                        
                        # MACD Analizi
                        if 'macd_analysis' in formation_data:
                            macd = formation_data['macd_analysis']
                            print(f"📊 MACD: {macd['macd_trend']} ({macd['macd_momentum']})")
                            print(f"   MACD Skoru: {macd['total_macd_score']}")
                        
                        # Hacim Analizi
                        if 'volume_analysis' in formation_data:
                            volume = formation_data['volume_analysis']
                            print(f"📈 Hacim: {volume['volume_ratio']:.1f}x ortalama")
                            print(f"   Hacim Skoru: {volume['total_volume_score']}")
                            for signal in volume['volume_signals']:
                                print(f"   {signal}")
                        
                        # YENİ: Breakout Analizi
                        if 'breakout_analysis' in formation_data:
                            breakout = formation_data['breakout_analysis']
                            print(f"🔥 Breakout: {breakout['quality']} ({breakout['candle_color']} mum)")
                            print(f"   Gövde Oranı: {breakout['body_ratio']:.2f}")
                            print(f"   Hacim Oranı: {breakout['volume_ratio']:.1f}x")
                            print(f"   Fiyat Değişimi: %{breakout['price_change']:.2f}")
                            print(f"   Momentum: {breakout['momentum']}")
                            print(f"   Breakout Skoru: {breakout['breakout_strength']}")
                            for signal in breakout['breakout_signals']:
                                print(f"   {signal}")
                        
                        # YENİ: Geometrik Skor Analizi
                        if 'geometric_analysis' in formation_data:
                            geometric = formation_data['geometric_analysis']
                            print(f"📐 Geometrik Skor: {geometric['geometric_score']} ({geometric['quality']})")
                            for signal in geometric['geometric_signals']:
                                print(f"   {signal}")
                        
                        # YENİ: Backtest Analizi
                        if 'backtest_analysis' in formation_data:
                            backtest = formation_data['backtest_analysis']
                            print(f"📈 Backtest: %{backtest['success_rate']:.1f} başarı oranı")
                            print(f"   Test Sayısı: {backtest['total_tests']}")
                            print(f"   Başarılı: {backtest['successful_tests']}")
                            print(f"   Ortalama Kâr: %{backtest['avg_profit']:.1f}")
                            print(f"   Maksimum Kâr: %{backtest['max_profit']:.1f}")
                            print(f"   Maksimum Zarar: %{backtest['max_loss']:.1f}")
                            for signal in backtest['backtest_signals']:
                                print(f"   {signal}")
                        
                        # Tüm sinyaller
                        if 'all_signals' in formation_data:
                            print("\n📋 Tüm Sinyaller:")
                            for signal in formation_data['all_signals']:
                                print(f"   • {signal}")
                    
                    else:
                        print("⚠️ Eski formasyon formatı - yeni skorlama yok")
                
                else:
                    print(f"❌ {formation_type} formasyonu tespit edilmedi")
            
            print("\n" + "=" * 50)
            
        except Exception as e:
            print(f"❌ {symbol} analizi sırasında hata: {str(e)}")
    
    print("\n✅ Test tamamlandı!")
    print("\n🎯 Yeni Özellikler:")
    print("   • Breakout mum analizi (gövde boyu, hacim, momentum)")
    print("   • Geometrik skor (simetri, derinlik, sıkışma)")
    print("   • Backtest başarı oranı (geçmiş performans)")
    print("   • Gelişmiş skorlama sistemi (250 puan maksimum)")

if __name__ == "__main__":
    test_advanced_analysis() 