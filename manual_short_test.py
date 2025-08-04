#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MANUEL SHORT SİNYAL TEST
=========================

Bu script manuel olarak bir SHORT sinyal oluşturur.
"""

from signal_visualizer import SignalVisualizer
from utils import format_price

def manual_short_test():
    """Manuel SHORT sinyal testi"""
    
    print("🔻 MANUEL SHORT SİNYAL TESTİ")
    print("=" * 50)
    
    visualizer = SignalVisualizer()
    
    # Manuel test verisi
    symbol = "STOUSDT"
    entry_price = 0.085970
    direction = "Short"
    formation_type = "OBO"
    
    # Formasyon verisi
    formation_data = {
        'type': formation_type,
        'direction': direction,
        'quality_score': 345,  # Yüksek kalite skoru
        'entry_price': entry_price
    }
    
    print(f"📊 Sembol: {symbol}")
    print(f"💰 Giriş Fiyatı: {format_price(entry_price)}")
    print(f"🔴 Yön: {direction}")
    print(f"🔍 Formasyon: {formation_type}")
    print()
    
    # Hedef seviyeleri hesapla
    levels = visualizer.calculate_target_levels(entry_price, direction, formation_data)
    
    print("📋 HEDEF SEVİYELER:")
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
    
    # Telegram mesajı oluştur
    message = visualizer.create_signal_message(symbol, formation_type, entry_price, direction, levels, formation_data)
    
    print("📱 TELEGRAM MESAJI:")
    print("-" * 50)
    print(message)
    print("-" * 50)
    
    print()
    print("✅ MANUEL TEST TAMAMLANDI!")

if __name__ == "__main__":
    manual_short_test() 