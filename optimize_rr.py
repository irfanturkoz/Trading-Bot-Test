#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def optimize_tp_sl_simple(entry_price, current_tp, current_sl, direction, fibo_levels, bb_data=None):
    """
    Basit TP ve SL optimizasyonu - R/R 1.0-2.0 arası
    """
    if direction == 'Long':
        # Mantık kontrolü
        if entry_price <= current_sl or current_tp <= entry_price:
            return entry_price, entry_price * 0.99, 0
        
        # Mevcut R/R hesapla
        current_reward = (current_tp - entry_price) / entry_price
        current_risk = (entry_price - current_sl) / entry_price
        current_rr = current_reward / current_risk if current_risk > 0 else 0
        
        # R/R < 1.0 ise optimize et
        if current_rr < 1.0:
            # Basit TP/SL seçimi
            tp_options = []
            for level in ['0.382', '0.5', '0.618']:
                if level in fibo_levels and fibo_levels[level] > entry_price:
                    tp_options.append(fibo_levels[level])
            
            sl_options = []
            for level in ['0.618', '0.5']:
                if level in fibo_levels and fibo_levels[level] < entry_price:
                    sl_options.append(fibo_levels[level])
            
            if bb_data and bb_data['lower_band'] < entry_price:
                sl_options.append(bb_data['lower_band'])
            
            # En iyi kombinasyonu bul
            best_rr = 0
            best_tp = current_tp
            best_sl = current_sl
            
            for tp in tp_options:
                for sl in sl_options:
                    if sl >= entry_price:
                        continue
                    
                    reward = (tp - entry_price) / entry_price
                    risk = (entry_price - sl) / entry_price
                    rr = reward / risk if risk > 0 else 0
                    
                    # 1.0-2.0 arası ve daha iyi
                    if 1.0 <= rr <= 2.0 and rr > best_rr:
                        best_tp = tp
                        best_sl = sl
                        best_rr = rr
            
            return best_tp, best_sl, best_rr
        else:
            # Mevcut R/R'yi kontrol et
            if current_rr > 2.0:
                new_tp = entry_price + (entry_price - current_sl) * 2.0
                return new_tp, current_sl, 2.0
            return current_tp, current_sl, current_rr
    
    else:  # Short
        # Mantık kontrolü
        if entry_price >= current_sl or current_tp >= entry_price:
            return entry_price, entry_price * 1.01, 0
        
        # Mevcut R/R hesapla
        current_reward = (entry_price - current_tp) / entry_price
        current_risk = (current_sl - entry_price) / entry_price
        current_rr = current_reward / current_risk if current_risk > 0 else 0
        
        # R/R < 1.0 ise optimize et
        if current_rr < 1.0:
            # Basit TP/SL seçimi
            tp_options = []
            for level in ['0.618', '0.5', '0.382']:
                if level in fibo_levels and fibo_levels[level] < entry_price:
                    tp_options.append(fibo_levels[level])
            
            sl_options = []
            for level in ['0.382', '0.5']:
                if level in fibo_levels and fibo_levels[level] > entry_price:
                    sl_options.append(fibo_levels[level])
            
            if bb_data and bb_data['upper_band'] > entry_price:
                sl_options.append(bb_data['upper_band'])
            
            # En iyi kombinasyonu bul
            best_rr = 0
            best_tp = current_tp
            best_sl = current_sl
            
            for tp in tp_options:
                for sl in sl_options:
                    if sl <= entry_price:
                        continue
                    
                    reward = (entry_price - tp) / entry_price
                    risk = (sl - entry_price) / entry_price
                    rr = reward / risk if risk > 0 else 0
                    
                    # 1.0-2.0 arası ve daha iyi
                    if 1.0 <= rr <= 2.0 and rr > best_rr:
                        best_tp = tp
                        best_sl = sl
                        best_rr = rr
            
            return best_tp, best_sl, best_rr
        else:
            # Mevcut R/R'yi kontrol et
            if current_rr > 2.0:
                new_tp = entry_price - (current_sl - entry_price) * 2.0
                return new_tp, current_sl, 2.0
            return current_tp, current_sl, current_rr

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