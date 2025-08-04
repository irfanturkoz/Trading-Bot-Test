#!/usr/bin/env python3
"""
Kullanıcının verdiği örneği test et
Giriş: 3.37, Short pozisyon
"""

from tp_sl_calculator import calculate_strict_tp_sl, format_signal_levels

def test_user_example():
    print("Kullanicinin verdigi ornek test ediliyor...")
    print("=" * 50)
    
    # Kullanıcının örneği
    entry_price = 3.37
    direction = 'Short'
    
    print(f"Giris fiyati: {entry_price}")
    print(f"Pozisyon: {direction}")
    print()
    
    # TP/SL hesapla
    levels = calculate_strict_tp_sl(entry_price, direction)
    
    print("HESAPLANAN SEVIYELER:")
    print(f"SL: {levels['sl']:.2f} ({levels['percentages']['sl']:+.1f}%)")
    print(f"TP1: {levels['tp1']:.2f} ({levels['percentages']['tp1']:+.1f}%)")
    print(f"TP2: {levels['tp2']:.2f} ({levels['percentages']['tp2']:+.1f}%)")
    print(f"TP3: {levels['tp3']:.2f} ({levels['percentages']['tp3']:+.1f}%)")
    print(f"R/R: {levels['rr_ratio']:.2f}:1")
    print()
    
    print("KULLANICININ BEKLENTISI:")
    print("SL: 3.47 (%3 yukari)")
    print("TP3: 3.22 (giris - 1.5 * %3)")
    print("TP2: 3.26")
    print("TP1: 3.30")
    print()
    
    # Karşılaştırma
    expected_sl = 3.47
    expected_tp3 = 3.22
    expected_tp2 = 3.26
    expected_tp1 = 3.30
    
    print("KARSILASTIRMA:")
    print(f"SL - Beklenen: {expected_sl:.2f}, Hesaplanan: {levels['sl']:.2f} - {'OK' if abs(levels['sl'] - expected_sl) < 0.01 else 'HATA'}")
    print(f"TP1 - Beklenen: {expected_tp1:.2f}, Hesaplanan: {levels['tp1']:.2f} - {'OK' if abs(levels['tp1'] - expected_tp1) < 0.01 else 'HATA'}")
    print(f"TP2 - Beklenen: {expected_tp2:.2f}, Hesaplanan: {levels['tp2']:.2f} - {'OK' if abs(levels['tp2'] - expected_tp2) < 0.01 else 'HATA'}")
    print(f"TP3 - Beklenen: {expected_tp3:.2f}, Hesaplanan: {levels['tp3']:.2f} - {'OK' if abs(levels['tp3'] - expected_tp3) < 0.01 else 'HATA'}")

if __name__ == "__main__":
    test_user_example()
