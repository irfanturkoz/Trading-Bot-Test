#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RPLUSDT Short pozisyon testi - Yeni hatalı sinyal
"""

from tp_sl_calculator import calculate_strict_tp_sl

def test_rplusdt_short():
    print("RPLUSDT Short pozisyon test ediliyor...")
    print("=" * 50)
    
    # Kullanicinin bildirdigi veriler
    entry_price = 6.77
    direction = "Short"
    
    print(f"Giris fiyati: {entry_price}")
    print(f"Pozisyon: {direction}")
    print()
    
    # Standardize edilmis hesaplayici ile dogru degerler
    levels = calculate_strict_tp_sl(entry_price, direction)
    
    print("DOGRU SEVIYELER (Standardize hesaplayici):")
    
    # Short pozisyon icin yuzde hesaplamalari
    sl_percent = -3.0  # SL her zaman -%3.0 zarar gosterilmeli
    tp1_percent = 4.5  # TP1 %4.5 kar
    tp2_percent = 6.0  # TP2 %6.0 kar  
    tp3_percent = 9.0  # TP3 %9.0 kar
    
    print(f"SL: {levels['sl']:.4f} ({sl_percent:.1f}%)")
    print(f"TP1: {levels['tp1']:.4f} (+{tp1_percent:.1f}%)")
    print(f"TP2: {levels['tp2']:.4f} (+{tp2_percent:.1f}%)")
    print(f"TP3: {levels['tp3']:.4f} (+{tp3_percent:.1f}%)")
    print(f"R/R: {levels['rr_ratio']:.2f}:1")
    print()
    
    print("HATALI SEVIYELER (Kullanicinin bildirdigi):")
    print("TP1: 7.76 USDT (+14.7%)")
    print("TP2: 7.64 USDT (+12.9%)")
    print("TP3: 7.40 USDT (+9.3%)")
    print("SL: 8.37 USDT (23.7%)")
    print()
    
    print("SORUN ANALIZI:")
    print("- TP seviyeleri giris fiyatindan YUKSEK (Short icin yanlis!)")
    print("- SL yuzde hesabi yanlis")
    print("- Sistem hala eski kodu kullaniyor")
    print("- Standardize hesaplayici kullanilmiyor")

if __name__ == "__main__":
    test_rplusdt_short()
