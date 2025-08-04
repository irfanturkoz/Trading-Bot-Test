#!/usr/bin/env python3
"""
TP/SL Calculator - Strict Rules Implementation
==============================================

Bu modül, kullanıcının belirlediği katı kurallara göre TP/SL hesaplaması yapar.
Hiçbir durumda bu kurallardan sapma yapılmaz.

🔁 GENEL KURALLAR:
- Giriş fiyatı ile SL ve TP oranlarını yönüne göre doğru hesapla:
  - Long işlemlerde: TP > Giriş > SL
  - Short işlemlerde: TP < Giriş < SL
- Stop Loss (SL) seviyesi her zaman **giriş fiyatının %3 uzağında** olacak.
- Risk/Ödül (R/R) oranı **sadece TP1 ile SL arasındaki fark** kullanılarak hesaplanacak.
- TP1, TP2, TP3 sırasıyla giriş fiyatına göre **%4.5 / %6.75 / %10.0** uzaklıkta olacak.
- Yön: "Long" ise TP'ler giriş fiyatının üstünde, "Short" ise TP'ler girişin altında olacak.
- Tüm oranları yüzde (%) olarak belirt, örnek: +4.5%, –3.0% gibi.
- TP seviyelerinin sıralaması yönle uyumlu olacak:
  - Long: TP1 < TP2 < TP3
  - Short: TP1 > TP2 > TP3

⛔ HATALI YAPILMAMASI GEREKENLER:
- TP'ler long pozisyonda girişin altında olamaz.
- TP'ler short pozisyonda girişin üstünde olamaz.
- SL oranı asla %3 dışında olamaz.
- TP'lerin sırası yönle ters olamaz.
- R/R oranı **yalnızca TP1 ile SL arasından** hesaplanmalı. Diğer TP'ler R/R için dikkate alınmaz.
"""

def calculate_strict_tp_sl(entry_price, direction):
    """
    Katı kurallara göre TP/SL hesaplama - KULLANICI KURALLARI
    
    Kurallar:
    - SL her zaman %3.0 zarar (giriş seviyesinin %3 aşağısı)
    - TP1: %4.5 kar
    - TP2: %6.0 kar
    - TP3: %9.0 kar
    - R/R hesabı TP3 ve SL arasında yapılır (9.0/3.0 = 3.0:1)
    
    Args:
        entry_price (float): Giriş fiyatı
        direction (str): 'Long' veya 'Short'
        
    Returns:
        dict: TP/SL seviyeleri ve R/R oranı
    """
    if not isinstance(entry_price, (int, float)) or entry_price <= 0:
        raise ValueError("Geçersiz giriş fiyatı")
    
    if direction not in ['Long', 'Short']:
        raise ValueError("Geçersiz yön - 'Long' veya 'Short' olmalı")
    
    # SL her zaman %3 uzaklıkta (kullanıcı %3 zarar)
    sl_percent = 3.0
    
    # Kullanıcının belirlediği TP yüzdeleri
    tp1_percent = 4.5  # TP1: %4.5 kar
    tp2_percent = 6.0  # TP2: %6.0 kar
    tp3_percent = 9.0  # TP3: %9.0 kar
    
    if direction == 'Long':
        # Long: SL girişin altında, TP'ler girişin üstünde
        sl = entry_price * (1 - sl_percent / 100)  # %3 aşağı (zarar)
        tp1 = entry_price * (1 + tp1_percent / 100)  # %4.5 yukarı (kar)
        tp2 = entry_price * (1 + tp2_percent / 100)  # %3.0 yukarı (kar)
        tp3 = entry_price * (1 + tp3_percent / 100)  # %1.5 yukarı (kar)
        
        # R/R hesaplama (TP1 ve SL arası - kullanıcı isteği)
        tp1_distance = tp1 - entry_price  # TP1 mesafesi (%4.5)
        sl_distance = entry_price - sl    # SL mesafesi (%3.0)
        rr_ratio = tp1_distance / sl_distance  # 4.5/3.0 = 1.5:1
        
    else:  # Short
        # Short: SL girişin üstünde, TP'ler girişin altında
        sl = entry_price * (1 + sl_percent / 100)  # %3 yukarı (zarar)
        tp1 = entry_price * (1 - tp1_percent / 100)  # %4.5 aşağı (kar)
        tp2 = entry_price * (1 - tp2_percent / 100)  # %3.0 aşağı (kar)
        tp3 = entry_price * (1 - tp3_percent / 100)  # %1.5 aşağı (kar)
        
        # R/R hesaplama (TP1 ve SL arası - kullanıcı isteği)
        tp1_distance = entry_price - tp1  # TP1 mesafesi (%4.5)
        sl_distance = sl - entry_price    # SL mesafesi (%3.0)
        rr_ratio = tp1_distance / sl_distance  # 4.5/3.0 = 1.5:1
    
    return {
        'entry_price': round(entry_price, 6),
        'tp1': round(tp1, 6),
        'tp2': round(tp2, 6),
        'tp3': round(tp3, 6),
        'sl': round(sl, 6),
        'rr_ratio': round(rr_ratio, 2),
        'direction': direction,
        'percentages': {
            'sl': sl_percent,
            'tp1': tp1_percent,
            'tp2': tp2_percent,
            'tp3': tp3_percent
        }
    }

def format_signal_levels(entry_price, direction):
    """
    Sinyal seviyelerini formatlanmış string olarak döndürür
    
    Args:
        entry_price (float): Giriş fiyatı
        direction (str): 'Long' veya 'Short'
        
    Returns:
        str: Formatlanmış sinyal seviyeleri
    """
    levels = calculate_strict_tp_sl(entry_price, direction)
    
    direction_symbol = "LONG" if direction == "Long" else "SHORT"
    
    signal_text = f"""
{direction_symbol} ISLEM:
Giris: {levels['entry_price']:.6f}
SL: {levels['sl']:.6f} ({levels['percentages']['sl']:+.1f}%)
TP1: {levels['tp1']:.6f} ({levels['percentages']['tp1']:+.1f}%)
TP2: {levels['tp2']:.6f} ({levels['percentages']['tp2']:+.1f}%)
TP3: {levels['tp3']:.6f} ({levels['percentages']['tp3']:+.1f}%)
R/R: {levels['rr_ratio']:.2f}:1
"""
    
    return signal_text.strip()

def validate_tp_sl_rules(entry_price, sl, tp1, tp2, tp3, direction):
    """
    TP/SL seviyelerinin kurallara uygunluğunu kontrol eder
    
    Args:
        entry_price (float): Giriş fiyatı
        sl (float): Stop Loss
        tp1, tp2, tp3 (float): Take Profit seviyeleri
        direction (str): 'Long' veya 'Short'
        
    Returns:
        dict: Doğrulama sonuçları
    """
    errors = []
    
    if direction == 'Long':
        # Long işlem kontrolleri
        if sl >= entry_price:
            errors.append("SL giriş fiyatının altında olmalı (Long)")
        if tp1 <= entry_price:
            errors.append("TP1 giriş fiyatının üstünde olmalı (Long)")
        if tp2 <= entry_price:
            errors.append("TP2 giriş fiyatının üstünde olmalı (Long)")
        if tp3 <= entry_price:
            errors.append("TP3 giriş fiyatının üstünde olmalı (Long)")
        if not (tp1 < tp2 < tp3):
            errors.append("TP sıralaması yanlış (Long: TP1 < TP2 < TP3)")
    else:
        # Short işlem kontrolleri
        if sl <= entry_price:
            errors.append("SL giriş fiyatının üstünde olmalı (Short)")
        if tp1 >= entry_price:
            errors.append("TP1 giriş fiyatının altında olmalı (Short)")
        if tp2 >= entry_price:
            errors.append("TP2 giriş fiyatının altında olmalı (Short)")
        if tp3 >= entry_price:
            errors.append("TP3 giriş fiyatının altında olmalı (Short)")
        if not (tp1 > tp2 > tp3):
            errors.append("TP sıralaması yanlış (Short: TP1 > TP2 > TP3)")
    
    # SL yüzdesi kontrolü
    if direction == 'Long':
        sl_percent = ((sl - entry_price) / entry_price) * 100
        if abs(sl_percent + 3.0) > 0.01:  # %3 tolerans
            errors.append(f"SL yüzdesi %3 olmalı, mevcut: {sl_percent:.2f}%")
    else:
        sl_percent = ((sl - entry_price) / entry_price) * 100
        if abs(sl_percent - 3.0) > 0.01:  # %3 tolerans
            errors.append(f"SL yüzdesi %3 olmalı, mevcut: {sl_percent:.2f}%")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

# Test fonksiyonu
def test_tp_sl_calculator():
    """TP/SL hesaplayıcısını test eder"""
    print("TEST: TP/SL Hesaplayici Test Baslatiliyor...")
    print("=" * 50)
    
    # Long test
    print("\nLONG TEST:")
    long_result = calculate_strict_tp_sl(1.0000, 'Long')
    print(format_signal_levels(1.0000, 'Long'))
    
    # Short test
    print("\nSHORT TEST:")
    short_result = calculate_strict_tp_sl(1.0000, 'Short')
    print(format_signal_levels(1.0000, 'Short'))
    
    # Doğrulama testleri
    print("\nDOGRULAMA TESTLERI:")
    long_validation = validate_tp_sl_rules(
        1.0000, long_result['sl'], long_result['tp1'], 
        long_result['tp2'], long_result['tp3'], 'Long'
    )
    print(f"Long dogrulama: {'GECERLI' if long_validation['valid'] else 'GECERSIZ'}")
    if not long_validation['valid']:
        for error in long_validation['errors']:
            print(f"  - {error}")
    
    short_validation = validate_tp_sl_rules(
        1.0000, short_result['sl'], short_result['tp1'], 
        short_result['tp2'], short_result['tp3'], 'Short'
    )
    print(f"Short dogrulama: {'GECERLI' if short_validation['valid'] else 'GECERSIZ'}")
    if not short_validation['valid']:
        for error in short_validation['errors']:
            print(f"  - {error}")
    
    print("\nTest tamamlandi!")

if __name__ == "__main__":
    test_tp_sl_calculator()
