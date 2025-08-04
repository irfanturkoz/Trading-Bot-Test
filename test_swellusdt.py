#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SWELLUSDT Short pozisyon testi - Kullanicinin bildirdigi hatali sinyal
"""

from tp_sl_calculator import calculate_strict_tp_sl

def test_swellusdt_short():
    print("SWELLUSDT Short pozisyon test ediliyor...")
    print("=" * 50)
    
    # Kullanicinin bildirdigi veriler
    entry_price = 0.008620
    direction = "Short"
    
    print(f"Giris fiyati: {entry_price}")
    print(f"Pozisyon: {direction}")
    print()
    
    # Standardize edilmis hesaplayici ile dogru degerler
    levels = calculate_strict_tp_sl(entry_price, direction)
    
    print("DOGRU SEVIYELER (Standardize hesaplayici):")
    
    # Short pozisyon icin yuzde hesaplamalari
    sl_percent = ((levels['sl'] - entry_price) / entry_price) * 100
    tp1_percent = abs(((levels['tp1'] - entry_price) / entry_price) * 100)  # Pozitif goster
    tp2_percent = abs(((levels['tp2'] - entry_price) / entry_price) * 100)  # Pozitif goster
    tp3_percent = abs(((levels['tp3'] - entry_price) / entry_price) * 100)  # Pozitif goster
    
    print(f"SL: {levels['sl']:.6f} ({sl_percent:+.1f}%)")
    print(f"TP1: {levels['tp1']:.6f} (+{tp1_percent:.1f}%)")
    print(f"TP2: {levels['tp2']:.6f} (+{tp2_percent:.1f}%)")
    print(f"TP3: {levels['tp3']:.6f} (+{tp3_percent:.1f}%)")
    print(f"R/R: {levels['rr_ratio']:.2f}:1")
    print()
    
    print("HATALI SEVIYELER (Kullanicinin bildirdigi):")
    print("TP1: 0.009397 USDT (+9.0%)")
    print("TP2: 0.009176 USDT (+6.5%)")
    print("TP3: 0.008856 USDT (+2.7%)")
    print("SL: 0.010135 USDT (17.6%)")
    print()
    
    print("SORUN ANALIZI:")
    print("- TP seviyeleri giris fiyatindan YUKSEK (Short icin yanlis!)")
    print("- SL yuzde hesabi yanlis")
    print("- TP siralaması yanlis")
    print("- R/R orani dogru ama TP/SL seviyeler yanlis")

if __name__ == "__main__":
    test_swellusdt_short()
