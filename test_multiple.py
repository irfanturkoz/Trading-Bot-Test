#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from botanlik import analyze_symbol

def test_multiple_formations():
    print("🔍 Çoklu formasyon testi başlatılıyor...")
    
    try:
        result = analyze_symbol('BTCUSDT', '4h', debug_mode=True)
        print("✅ Test tamamlandı!")
        return result
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        return None

if __name__ == "__main__":
    test_multiple_formations() 