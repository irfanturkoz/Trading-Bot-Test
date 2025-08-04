#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
from tp_sl_calculator import calculate_strict_tp_sl

def optimize_tp_sl_fixed(entry_price, current_tp, current_sl, direction, fibo_levels, bb_data=None):
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
        if entry_price <= current_sl or current_tp <= entry_price:
            return entry_price, entry_price * 0.99, 0
        
        # Mevcut R/R hesapla
        current_reward = (current_tp - entry_price) / entry_price
        current_risk = (entry_price - current_sl) / entry_price
        current_rr = current_reward / current_risk if current_risk > 0 else 0
        
        # R/R < 1.2 ise optimize et
        if current_rr < 1.2:
            # Daha yakın Fibonacci seviyeleri
            tp_options = []
            for level in ['0.236', '0.382', '0.5']:
                if level in fibo_levels and fibo_levels[level] > entry_price:
                    tp_options.append(fibo_levels[level])
            
            sl_options = []
            for level in ['0.5', '0.618']:
                if level in fibo_levels and fibo_levels[level] < entry_price:
                    sl_options.append(fibo_levels[level])
            
            if bb_data and bb_data['lower_band'] < entry_price:
                sl_options.append(bb_data['lower_band'])
            
            # Tüm kombinasyonları topla
            all_options = []
            for tp in tp_options:
                for sl in sl_options:
                    if sl >= entry_price:
                        continue
                    
                    reward = (tp - entry_price) / entry_price
                    risk = (entry_price - sl) / entry_price
                    rr = reward / risk if risk > 0 else 0
                    
                    # 1.2-1.8 arası
                    if 1.2 <= rr <= 1.8:
                        all_options.append({
                            'tp': tp,
                            'sl': sl,
                            'rr': rr
                        })
            
            # Rastgele seçim yap
            if all_options:
                import random
                best_option = random.choice(all_options)
                return best_option['tp'], best_option['sl'], best_option['rr']
            
            return current_tp, current_sl, current_rr
        else:
            # Mevcut R/R'yi kontrol et
            if current_rr > 1.8:
                new_tp = entry_price + (entry_price - current_sl) * 1.8
                return new_tp, current_sl, 1.8
            return current_tp, current_sl, current_rr
    
    else:  # Short
        # Mantık kontrolü
        if entry_price >= current_sl or current_tp >= entry_price:
            return entry_price, entry_price * 1.01, 0
        
        # Mevcut R/R hesapla
        current_reward = (entry_price - current_tp) / entry_price
        current_risk = (current_sl - entry_price) / entry_price
        current_rr = current_reward / current_risk if current_risk > 0 else 0
        
        # R/R < 1.2 ise optimize et
        if current_rr < 1.2:
            # Daha yakın Fibonacci seviyeleri
            tp_options = []
            for level in ['0.5', '0.382', '0.236']:
                if level in fibo_levels and fibo_levels[level] < entry_price:
                    tp_options.append(fibo_levels[level])
            
            sl_options = []
            for level in ['0.618', '0.5']:
                if level in fibo_levels and fibo_levels[level] > entry_price:
                    sl_options.append(fibo_levels[level])
            
            if bb_data and bb_data['upper_band'] > entry_price:
                sl_options.append(bb_data['upper_band'])
            
            # Tüm kombinasyonları topla
            all_options = []
            for tp in tp_options:
                for sl in sl_options:
                    if sl <= entry_price:
                        continue
                    
                    reward = (entry_price - tp) / entry_price
                    risk = (sl - entry_price) / entry_price
                    rr = reward / risk if risk > 0 else 0
                    
                    # 1.2-1.8 arası
                    if 1.2 <= rr <= 1.8:
                        all_options.append({
                            'tp': tp,
                            'sl': sl,
                            'rr': rr
                        })
            
            # Rastgele seçim yap
            if all_options:
                import random
                best_option = random.choice(all_options)
                return best_option['tp'], best_option['sl'], best_option['rr']
            
            return current_tp, current_sl, current_rr
        else:
            # Mevcut R/R'yi kontrol et
            if current_rr > 1.8:
                new_tp = entry_price - (current_sl - entry_price) * 1.8
                return new_tp, current_sl, 1.8
            return current_tp, current_sl, current_rr

# Test fonksiyonu
def test_fixed_rr():
    print("🧪 Düzeltilmiş R/R Test")
    print("=" * 40)
    
    # Test verileri
    entry = 100
    tp = 110
    sl = 95
    fibo = {'0.236': 105, '0.382': 108, '0.5': 110, '0.618': 112}
    
    print("Long Test:")
    for i in range(5):
        tp_new, sl_new, rr = optimize_tp_sl_fixed(entry, tp, sl, 'Long', fibo)
        print(f"  Test {i+1}: TP={tp_new:.2f}, SL={sl_new:.2f}, R/R={rr:.2f}")
    
    print("\nShort Test:")
    for i in range(5):
        tp_new, sl_new, rr = optimize_tp_sl_fixed(entry, tp, sl, 'Short', fibo)
        print(f"  Test {i+1}: TP={tp_new:.2f}, SL={sl_new:.2f}, R/R={rr:.2f}")

if __name__ == "__main__":
    test_fixed_rr() 