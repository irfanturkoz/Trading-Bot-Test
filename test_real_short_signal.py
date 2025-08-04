#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GERÇEK SHORT SİNYAL TEST SCRIPT
================================

Bu script gerçek bir SHORT sinyal testi yapar.
"""

from signal_visualizer import SignalVisualizer

def test_real_short_signal():
    """Gerçek bir SHORT sinyal testi yapar"""
    
    print("🔻 GERÇEK SHORT SİNYAL TESTİ")
    print("=" * 50)
    
    visualizer = SignalVisualizer()
    
    # Test sembolü - STOUSDT
    symbol = "STOUSDT"
    interval = "1h"
    
    print(f"📊 Sembol: {symbol}")
    print(f"⏰ Interval: {interval}")
    print()
    
    # Formasyon tespit et ve görselleştir
    success = visualizer.detect_and_visualize_formation(symbol, interval, debug_mode=True)
    
    if success:
        print(f"✅ {symbol} SHORT sinyali başarıyla oluşturuldu!")
    else:
        print(f"❌ {symbol} sinyali oluşturulamadı!")
    
    print()
    print("🎯 TEST TAMAMLANDI!")

if __name__ == "__main__":
    test_real_short_signal() 