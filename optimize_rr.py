#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
from tp_sl_calculator import calculate_strict_tp_sl

def optimize_tp_sl_simple(entry_price, current_tp, current_sl, direction, fibo_levels, bb_data=None):
    """
    Standardized TP ve SL optimizasyonu - Kullanıcının katı kurallarına göre
    """
    try:
        # Standardized TP/SL hesaplama kullan
        levels = calculate_strict_tp_sl(entry_price, direction)
        return levels['tp1'], levels['sl'], levels['rr_ratio']
    except Exception as e:
        # Fallback - eski mantık
        if direction == 'Long':
            sl = entry_price * 0.97  # %3 altında
            tp = entry_price * 1.045  # %4.5 yukarıda
            rr = (tp - entry_price) / (entry_price - sl)
            return tp, sl, rr
        else:
            sl = entry_price * 1.03  # %3 üstünde
            tp = entry_price * 0.955  # %4.5 aşağıda
            rr = (entry_price - tp) / (sl - entry_price)
            return tp, sl, rr


# Test fonksiyonu
def test_rr():
    print("🧪 R/R Test")
    print("=" * 30)
    
    # Test verileri
    entry = 100
    tp = 110
    sl = 95
    fibo = {'0.382': 105, '0.5': 110, '0.618': 115}
    
    tp_new, sl_new, rr = optimize_tp_sl_simple(entry, tp, sl, 'Long', fibo)
    print(f"Long: TP={tp_new:.2f}, SL={sl_new:.2f}, R/R={rr:.2f}")
    
    tp_new, sl_new, rr = optimize_tp_sl_simple(entry, tp, sl, 'Short', fibo)
    print(f"Short: TP={tp_new:.2f}, SL={sl_new:.2f}, R/R={rr:.2f}")

if __name__ == "__main__":
    test_rr() 