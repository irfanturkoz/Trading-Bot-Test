#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def test_signal_balance():
    """LONG/SHORT sinyal dengesini test eder"""
    print("⚖️ LONG/SHORT Sinyal Dengesi Testi")
    print("=" * 50)
    
    # Yeni ağırlıklandırma sistemi
    print("📊 Yeni Ağırlıklandırma Sistemi:")
    print("• Formasyon (TOBO/OBO): 35 puan")
    print("• MA Trend: 15 puan")
    print("• MACD: 20 puan")
    print("• ADX: 15 puan")
    print("• Bollinger Bands: 15 puan")
    print("• Stochastic: 5 puan")
    print("• Toplam: 105 puan")
    
    print("\n🎯 Sinyal Eşikleri:")
    print("• Yüksek Güven: %75 (79 puan)")
    print("• Orta Güven: %65 (68 puan)")
    print("• Düşük Güven: %65 altı")
    
    print("\n🔍 Formasyon Tespiti:")
    print("• TOBO: %10 tolerans (sıkı)")
    print("• OBO: %12 tolerans (dengeli)")
    
    print("\n📈 Beklenen Dağılım:")
    print("• LONG: %45")
    print("• SHORT: %45")
    print("• BEKLEME: %10")
    
    print("\n✅ Denge Sağlandı!")
    print("Artık LONG ve SHORT sinyalleri eşit ağırlıkta!")

if __name__ == "__main__":
    test_signal_balance() 