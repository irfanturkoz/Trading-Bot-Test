#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHORT SİNYAL TEST SCRIPT
========================

Bu script SHORT sinyal hesaplamalarının doğru çalışıp çalışmadığını test eder.
"""

from signal_visualizer import SignalVisualizer
from utils import format_price

def test_short_signal_calculations():
    """SHORT sinyal hesaplamalarını test eder"""
    
    print("🔻 SHORT SİNYAL HESAPLAMA TESTİ")
    print("=" * 50)
    
    visualizer = SignalVisualizer()
    
    # Test verisi - STOUSDT sinyali
    symbol = "STOUSDT"
    entry_price = 0.085970  # Giriş fiyatı
    direction = "Short"
    formation_data = {}
    
    print(f"📊 Sembol: {symbol}")
    print(f"💰 Giriş Fiyatı: {format_price(entry_price)}")
    print(f"🔴 Yön: {direction}")
    print()
    
    # Hedef seviyeleri hesapla
    levels = visualizer.calculate_target_levels(entry_price, direction, formation_data)
    
    print("📋 HESAPLAMA SONUÇLARI:")
    print(f"🛑 SL: {format_price(levels['sl'])} USDT")
    print(f"🎯 TP1: {format_price(levels['tp1'])} USDT")
    print(f"🎯 TP2: {format_price(levels['tp2'])} USDT")
    print(f"🎯 TP3: {format_price(levels['tp3'])} USDT")
    print(f"📈 R/R Oranı: {levels['rr_ratio']:.2f}:1")
    print()
    
    # Yüzde hesaplamaları
    tp1_percent = ((entry_price/levels['tp1']-1)*100)
    tp2_percent = ((entry_price/levels['tp2']-1)*100)
    tp3_percent = ((entry_price/levels['tp3']-1)*100)
    sl_percent = ((levels['sl']/entry_price-1)*100)
    
    print("📊 YÜZDE HESAPLAMALARI:")
    print(f"🎯 TP1: {tp1_percent:+.1f}%")
    print(f"🎯 TP2: {tp2_percent:+.1f}%")
    print(f"🎯 TP3: {tp3_percent:+.1f}%")
    print(f"🛑 SL: {sl_percent:+.1f}%")
    print()
    
    # Doğruluk kontrolleri
    print("✅ DOĞRULUK KONTROLLERİ:")
    
    # SL girişin üstünde olmalı (Short)
    if levels['sl'] > entry_price:
        print("✅ SL giriş fiyatının üstünde")
    else:
        print("❌ SL giriş fiyatının altında!")
    
    # TP'ler girişin altında olmalı (Short)
    if levels['tp1'] < entry_price and levels['tp2'] < entry_price and levels['tp3'] < entry_price:
        print("✅ Tüm TP'ler giriş fiyatının altında")
    else:
        print("❌ TP'ler giriş fiyatının üstünde!")
    
    # TP sıralaması doğru olmalı (Short: TP1 > TP2 > TP3)
    if levels['tp1'] > levels['tp2'] > levels['tp3']:
        print("✅ TP sıralaması doğru (TP1 > TP2 > TP3)")
    else:
        print("❌ TP sıralaması yanlış!")
    
    # R/R oranı mantıklı olmalı
    if levels['rr_ratio'] > 0:
        print(f"✅ R/R oranı mantıklı: {levels['rr_ratio']:.2f}:1")
    else:
        print("❌ R/R oranı mantıksız!")
    
    print()
    print("🎯 TEST TAMAMLANDI!")

if __name__ == "__main__":
    test_short_signal_calculations() 