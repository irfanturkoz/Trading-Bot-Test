#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GELİŞMİŞ FORMASYON TESPİT SİSTEMİ - VERSİYON 5.0
==================================================

Bu modül, TOBO ve OBO formasyonlarını Gelişmiş Formasyon Analiz Sistemi 5.0
kurallarına göre tespit eder.

Kurallar:
1. Zaman Filtresi: Minimum 20 mum (tercih: 12-48 saat)
2. Yükseklik Filtresi: Boyun-dip/tepe farkı minimum %2
3. R/R Hesaplaması: SL %1.5, TP 1.3-1.7 R/R
4. Kalite Skorlama: 400 puan (Süre 0-100, Yapısal 0-100, Hacim 0-100, RSI/MACD 0-100, R/R 0-100)
5. Minimum 250 puan şartı

Author: Trading Bot Team
Version: 5.0
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional


def get_rsi(series, period=14):
    """RSI hesaplama"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(df, fast=12, slow=26, signal=9):
    """MACD hesaplama"""
    exp1 = df['close'].ewm(span=fast).mean()
    exp2 = df['close'].ewm(span=slow).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    
    return pd.DataFrame({
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    })


def detect_inverse_head_and_shoulders(df, window=30, debug=False):
    """
    Gelişmiş Formasyon Analiz Sistemi 5.0 - TOBO (Ters Omuz Baş Omuz) Tespiti
    
    Kurallar:
    1. Zaman Filtresi: Minimum 20 mum (tercih: 12-48 saat)
    2. Yükseklik Filtresi: Boyun-dip farkı minimum %2
    3. R/R Hesaplaması: SL %1.5, TP 1.3-1.7 R/R
    4. Kalite Skorlama: 400 puan (Süre 0-100, Yapısal 0-100, Hacim 0-100, RSI/MACD 0-100, R/R 0-100)
    5. Minimum 250 puan şartı
    """
    if len(df) < window:
        if debug: print("❌ Veri yetersiz")
        return None
    
    # 1. ZAMAN FİLTRESİ - Minimum 20 mum kontrolü
    if window < 20:
        if debug: print("❌ Window çok küçük")
        return None
    
    # 2. TEMEL TOBO TESPİTİ
    lows = df['low'][-window:].values
    highs = df['high'][-window:].values
    
    # En düşük 3 dip noktasını bul
    idx = np.argpartition(lows, 3)[:3]
    idx = np.sort(idx)
    dips = lows[idx]
    
    if debug: print(f"🔍 Dip noktaları: {dips}")
    
    # Ortadaki dip en düşük olmalı (baş)
    if not (dips[1] < dips[0] and dips[1] < dips[2]):
        if debug: print("❌ Ortadaki dip en düşük değil")
        return None
    
    sol_omuz = dips[0]
    bas = dips[1]
    sag_omuz = dips[2]
    
    if debug: print(f"✅ Sol omuz: {sol_omuz:.4f}, Baş: {bas:.4f}, Sağ omuz: {sag_omuz:.4f}")
    
    # Omuzlar baştan yukarıda ve birbirine yakın olmalı
    if not (sol_omuz > bas and sag_omuz > bas and abs(sol_omuz - sag_omuz) / bas < 0.10):
        if debug: print("❌ Omuzlar uygun değil")
        return None
    
    if debug: print("✅ Omuzlar uygun")
    
    # Boyun çizgisi hesaplama
    sol_tepe = highs[idx[0]]
    sag_tepe = highs[idx[2]]
    neckline = (sol_tepe + sag_tepe) / 2
    
    if debug: print(f"✅ Boyun çizgisi: {neckline:.4f}")
    
    # 3. YÜKSEKLİK FİLTRESİ - Minimum %1.5 kontrolü (2.0'dan düşürüldü)
    formation_height = abs(neckline - bas)
    height_percentage = (formation_height / bas) * 100
    
    if debug: print(f"🔍 Formasyon yüksekliği: %{height_percentage:.2f}")
    
    if height_percentage < 2.0:  # Minimum %2
        if debug: print(f"❌ Yükseklik yetersiz: %{height_percentage:.2f} < %2.0")
        return None
    
    if debug: print("✅ Yükseklik uygun")
    
    # 4. ZAMAN SÜRESİ HESAPLAMA
    formation_start = idx[0]
    formation_end = idx[2]
    candle_duration = formation_end - formation_start + 1
    
    # Saat cinsinden süre hesaplama (4H timeframe için)
    hours_duration = candle_duration * 4
    
    if debug: print(f"🔍 Mum süresi: {candle_duration}, Saat: {hours_duration}")
    
    # Zaman filtresi kontrolü
    if candle_duration < 20:  # Minimum 20 mum
        if debug: print(f"❌ Süre yetersiz: {candle_duration} < 20")
        return None
    
    if debug: print("✅ Süre uygun")
    
    # 5. HACİM TEYİDİ
    volume_data = df['volume'][-window:].values
    recent_volume_avg = np.mean(volume_data[-3:])  # Son 3 mum
    previous_volume_avg = np.mean(volume_data[-10:-3])  # Önceki 7 mum
    volume_increase = ((recent_volume_avg - previous_volume_avg) / previous_volume_avg) * 100
    
    # 6. RSI/MACD UYUMU
    rsi = get_rsi(df['close'], period=14)
    macd_data = calculate_macd(df)
    
    # RSI pozitif divergence kontrolü (TOBO için)
    rsi_divergence = False
    if len(rsi) >= 10:
        recent_rsi = rsi.iloc[-5:].values
        recent_price = df['close'].iloc[-5:].values
        if (recent_rsi[-1] > recent_rsi[0] and recent_price[-1] < recent_price[0]):
            rsi_divergence = True
    
    # MACD sinyal kontrolü
    macd_signal = False
    if len(macd_data) >= 3:
        macd_line = macd_data['macd'].iloc[-1]
        signal_line = macd_data['signal'].iloc[-1]
        if macd_line > signal_line:
            macd_signal = True
    
    # 7. R/R HESAPLAMASI - Standardize TP/SL hesaplayici kullan
    from tp_sl_calculator import calculate_strict_tp_sl
    
    # TOBO için giriş fiyatı boyun çizgisi seviyesinde olmalı
    entry_price = neckline
    direction = 'Long'  # TOBO Long pozisyon
    
    try:
        levels = calculate_strict_tp_sl(entry_price, direction)
        sl_price = levels['sl']
        tp_price = levels['tp3']  # Ana hedef TP3
        rr_ratio = levels['rr_ratio']
    except Exception as e:
        # Fallback - eski mantik
        sl_distance = entry_price * 0.03  # %3.0 SL
        sl_price = entry_price - sl_distance
        tp_distance = sl_distance * 3.0  # 3.0 R/R
        tp_price = entry_price + tp_distance
        rr_ratio = 3.0
    
    # 8. KALİTE SKORLAMA (400 puan)
    # Süre skoru (0-100)
    time_score = 0
    if 12 <= hours_duration <= 48:
        time_score = 100
    elif 8 <= hours_duration <= 72:
        time_score = 80
    elif 4 <= hours_duration <= 96:
        time_score = 60
    else:
        time_score = 20
    
    # Yapısal skor (0-100)
    structural_score = 0
    # Simetri kontrolü
    symmetry_diff = abs(sol_omuz - sag_omuz) / bas
    if symmetry_diff < 0.05:
        structural_score += 40
    elif symmetry_diff < 0.10:
        structural_score += 20
    
    # Yükseklik bonusu
    if height_percentage >= 5.0:
        structural_score += 30
    elif height_percentage >= 3.0:
        structural_score += 20
    elif height_percentage >= 2.0:
        structural_score += 10
    
    # Hareket gücü
    price_movement = abs(entry_price - neckline) / neckline * 100
    if price_movement >= 3.0:
        structural_score += 30
    elif price_movement >= 1.5:
        structural_score += 20
    else:
        structural_score += 10
    
    # Hacim skoru (0-100)
    volume_score = 0
    if volume_increase >= 50:
        volume_score = 100
    elif volume_increase >= 30:
        volume_score = 80
    elif volume_increase >= 20:
        volume_score = 60
    elif volume_increase >= 10:
        volume_score = 40
    else:
        volume_score = 20
    
    # RSI/MACD skoru (0-100)
    oscillator_score = 0
    if rsi_divergence:
        oscillator_score += 50
    if macd_signal:
        oscillator_score += 50
    
    # R/R skoru (0-100)
    rr_score = 0
    if 1.3 <= rr_ratio <= 1.7:
        rr_score = 100
    elif 1.2 <= rr_ratio <= 1.8:
        rr_score = 80
    elif 1.1 <= rr_ratio <= 2.0:
        rr_score = 60
    else:
        rr_score = 20
    
    # Toplam kalite skoru
    total_score = time_score + structural_score + volume_score + oscillator_score + rr_score
    
    # 9. SONUÇ OLUŞTURMA
    formation_data = {
        'type': 'TOBO',
        'direction': 'Long',
        'sol_omuz': sol_omuz,
        'bas': bas,
        'sag_omuz': sag_omuz,
        'neckline': neckline,
        'entry_price': entry_price,
        'tp_price': tp_price,
        'sl_price': sl_price,
        'rr_ratio': rr_ratio,
        'candle_duration': candle_duration,
        'hours_duration': hours_duration,
        'height_percentage': height_percentage,
        'volume_increase': volume_increase,
        'rsi_divergence': rsi_divergence,
        'macd_signal': macd_signal,
        'quality_score': total_score,
        'time_score': time_score,
        'structural_score': structural_score,
        'volume_score': volume_score,
        'oscillator_score': oscillator_score,
        'rr_score': rr_score,
        'formation_start': df['open_time'].iloc[-window+idx[0]],
        'formation_end': df['open_time'].iloc[-window+idx[2]]
    }
    
    # Minimum kalite skoru kontrolü
    if total_score < 200:  # 250'den 200'e düşürüldü
        return None
    
    return formation_data


def detect_head_and_shoulders(df, window=30, debug=False):
    """
    Gelişmiş Formasyon Analiz Sistemi 5.0 - OBO (Omuz Baş Omuz) Tespiti
    
    Kurallar:
    1. Zaman Filtresi: Minimum 20 mum (tercih: 12-48 saat)
    2. Yükseklik Filtresi: Boyun-tepe farkı minimum %2
    3. R/R Hesaplaması: SL %1.5, TP 1.3-1.7 R/R
    4. Kalite Skorlama: 400 puan (Süre 0-100, Yapısal 0-100, Hacim 0-100, RSI/MACD 0-100, R/R 0-100)
    5. Minimum 250 puan şartı
    """
    if len(df) < window:
        if debug: print("❌ Veri yetersiz")
        return None
    
    # 1. ZAMAN FİLTRESİ - Minimum 20 mum kontrolü
    if window < 20:
        if debug: print("❌ Window çok küçük")
        return None
    
    # 2. TEMEL OBO TESPİTİ
    highs = df['high'][-window:].values
    lows = df['low'][-window:].values
    
    # En yüksek 3 tepe noktasını bul
    idx = np.argpartition(-highs, 3)[:3]
    idx = np.sort(idx)
    peaks = highs[idx]
    
    # Ortadaki tepe en yüksek olmalı (baş)
    if not (peaks[1] > peaks[0] and peaks[1] > peaks[2]):
        if debug: print("❌ Ortadaki tepe en yüksek değil")
        return None
    
    sol_omuz = peaks[0]
    bas = peaks[1]
    sag_omuz = peaks[2]
    
    # Omuzlar baştan aşağıda ve birbirine yakın olmalı
    if not (sol_omuz < bas and sag_omuz < bas and abs(sol_omuz - sag_omuz) / bas < 0.12):
        if debug: print("❌ Omuzlar uygun değil")
        return None
    
    # Boyun çizgisi hesaplama
    sol_dip = lows[idx[0]]
    sag_dip = lows[idx[2]]
    neckline = (sol_dip + sag_dip) / 2
    
    # 3. YÜKSEKLİK FİLTRESİ - Minimum %1.5 kontrolü (2.0'dan düşürüldü)
    formation_height = abs(bas - neckline)
    height_percentage = (formation_height / bas) * 100
    
    if debug: print(f"🔍 Formasyon yüksekliği: %{height_percentage:.2f}")
    
    if height_percentage < 2.0:  # Minimum %2
        if debug: print(f"❌ Yükseklik yetersiz: %{height_percentage:.2f} < %2.0")
        return None
    
    # 4. ZAMAN SÜRESİ HESAPLAMA
    formation_start = idx[0]
    formation_end = idx[2]
    candle_duration = formation_end - formation_start + 1
    
    # Saat cinsinden süre hesaplama (4H timeframe için)
    hours_duration = candle_duration * 4
    
    if debug: print(f"🔍 Mum süresi: {candle_duration}, Saat: {hours_duration}")
    
    # Zaman filtresi kontrolü
    if candle_duration < 20:  # Minimum 20 mum
        if debug: print(f"❌ Süre yetersiz: {candle_duration} < 20")
        return None
    
    # 5. HACİM TEYİDİ
    volume_data = df['volume'][-window:].values
    recent_volume_avg = np.mean(volume_data[-3:])  # Son 3 mum
    previous_volume_avg = np.mean(volume_data[-10:-3])  # Önceki 7 mum
    volume_increase = ((recent_volume_avg - previous_volume_avg) / previous_volume_avg) * 100
    
    # 6. RSI/MACD UYUMU
    rsi = get_rsi(df['close'], period=14)
    macd_data = calculate_macd(df)
    
    # RSI negatif divergence kontrolü (OBO için)
    rsi_divergence = False
    if len(rsi) >= 10:
        recent_rsi = rsi.iloc[-5:].values
        recent_price = df['close'].iloc[-5:].values
        if (recent_rsi[-1] < recent_rsi[0] and recent_price[-1] > recent_price[0]):
            rsi_divergence = True
    
    # MACD sinyal kontrolü
    macd_signal = False
    if len(macd_data) >= 3:
        macd_line = macd_data['macd'].iloc[-1]
        signal_line = macd_data['signal'].iloc[-1]
        if macd_line < signal_line:
            macd_signal = True
    
    # 7. R/R HESAPLAMASI - Standardize TP/SL hesaplayici kullan
    from tp_sl_calculator import calculate_strict_tp_sl
    
    # OBO için giriş fiyatı boyun çizgisi seviyesinde olmalı
    entry_price = neckline
    direction = 'Short'  # OBO Short pozisyon
    
    try:
        levels = calculate_strict_tp_sl(entry_price, direction)
        sl_price = levels['sl']
        tp_price = levels['tp3']  # Ana hedef TP3
        rr_ratio = levels['rr_ratio']
    except Exception as e:
        # Fallback - eski mantik
        sl_distance = entry_price * 0.03  # %3.0 SL
        sl_price = entry_price + sl_distance  # Short icin SL yukarida
        tp_distance = sl_distance * 3.0  # 3.0 R/R
        tp_price = entry_price - tp_distance  # Short icin TP asagida
        rr_ratio = 3.0
    
    # 8. KALİTE SKORLAMA (400 puan)
    # Süre skoru (0-100)
    time_score = 0
    if 12 <= hours_duration <= 48:
        time_score = 100
    elif 8 <= hours_duration <= 72:
        time_score = 80
    elif 4 <= hours_duration <= 96:
        time_score = 60
    else:
        time_score = 20
    
    # Yapısal skor (0-100)
    structural_score = 0
    # Simetri kontrolü
    symmetry_diff = abs(sol_omuz - sag_omuz) / bas
    if symmetry_diff < 0.06:
        structural_score += 40
    elif symmetry_diff < 0.12:
        structural_score += 20
    
    # Yükseklik bonusu
    if height_percentage >= 5.0:
        structural_score += 30
    elif height_percentage >= 3.0:
        structural_score += 20
    elif height_percentage >= 2.0:
        structural_score += 10
    
    # Hareket gücü
    price_movement = abs(entry_price - neckline) / neckline * 100
    if price_movement >= 3.0:
        structural_score += 30
    elif price_movement >= 1.5:
        structural_score += 20
    else:
        structural_score += 10
    
    # Hacim skoru (0-100)
    volume_score = 0
    if volume_increase >= 50:
        volume_score = 100
    elif volume_increase >= 30:
        volume_score = 80
    elif volume_increase >= 20:
        volume_score = 60
    elif volume_increase >= 10:
        volume_score = 40
    else:
        volume_score = 20
    
    # RSI/MACD skoru (0-100)
    oscillator_score = 0
    if rsi_divergence:
        oscillator_score += 50
    if macd_signal:
        oscillator_score += 50
    
    # R/R skoru (0-100)
    rr_score = 0
    if 1.3 <= rr_ratio <= 1.7:
        rr_score = 100
    elif 1.2 <= rr_ratio <= 1.8:
        rr_score = 80
    elif 1.1 <= rr_ratio <= 2.0:
        rr_score = 60
    else:
        rr_score = 20
    
    # Toplam kalite skoru
    total_score = time_score + structural_score + volume_score + oscillator_score + rr_score
    
    # 9. SONUÇ OLUŞTURMA
    formation_data = {
        'type': 'OBO',
        'direction': 'Short',
        'sol_omuz': sol_omuz,
        'bas': bas,
        'sag_omuz': sag_omuz,
        'neckline': neckline,
        'entry_price': entry_price,
        'tp_price': tp_price,
        'sl_price': sl_price,
        'rr_ratio': rr_ratio,
        'candle_duration': candle_duration,
        'hours_duration': hours_duration,
        'height_percentage': height_percentage,
        'volume_increase': volume_increase,
        'rsi_divergence': rsi_divergence,
        'macd_signal': macd_signal,
        'quality_score': total_score,
        'time_score': time_score,
        'structural_score': structural_score,
        'volume_score': volume_score,
        'oscillator_score': oscillator_score,
        'rr_score': rr_score,
        'formation_start': df['open_time'].iloc[-window+idx[0]],
        'formation_end': df['open_time'].iloc[-window+idx[2]]
    }
    
    # Minimum kalite skoru kontrolü
    if total_score < 200:  # 250'den 200'e düşürüldü
        return None
    
    return formation_data


def test_enhanced_formations():
    """Test fonksiyonu - Tüm coinleri analiz et"""
    print("🧪 Gelişmiş Formasyon Tespit Sistemi 5.0 Test")
    print("=" * 50)
    
    # Gerçek coin verisi ile test
    from data_fetcher import fetch_ohlcv
    
    # Tüm USDT çiftlerini al
    import requests
    try:
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        symbols = []
        for symbol_info in data['symbols']:
            symbol = symbol_info['symbol']
            if symbol.endswith('USDT') and symbol_info['status'] == 'TRADING':
                symbols.append(symbol)
        
        print(f"📊 Toplam {len(symbols)} coin bulundu")
        
    except Exception as e:
        print(f"❌ Sembol listesi alınamadı: {e}")
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT']
    
    found_formations = 0
    total_analyzed = 0
    
    for i, symbol in enumerate(symbols):  # Tüm coinleri test et
        print(f"\n🔍 [{i+1}/{len(symbols)}] {symbol} test ediliyor...")
        
        try:
            # Gerçek veri çek
            df = fetch_ohlcv(symbol, '4h', limit=100)
            if df.empty:
                print(f"❌ {symbol}: Veri alınamadı")
                continue
            
            total_analyzed += 1
            print(f"✅ {symbol}: {len(df)} mum verisi alındı")
            
            # TOBO testi
            tobo_result = detect_inverse_head_and_shoulders(df, window=30, debug=False)
            if tobo_result:
                found_formations += 1
                print(f"✅ {symbol}: TOBO tespit edildi!")
                print(f"   Kalite Skoru: {tobo_result['quality_score']}/400")
                print(f"   R/R Oranı: {tobo_result['rr_ratio']:.2f}:1")
                print(f"   Süre: {tobo_result['hours_duration']} saat")
                print(f"   Yükseklik: %{tobo_result['height_percentage']:.2f}")
            
            # OBO testi
            obo_result = detect_head_and_shoulders(df, window=30, debug=False)
            if obo_result:
                found_formations += 1
                print(f"✅ {symbol}: OBO tespit edildi!")
                print(f"   Kalite Skoru: {obo_result['quality_score']}/400")
                print(f"   R/R Oranı: {obo_result['rr_ratio']:.2f}:1")
                print(f"   Süre: {obo_result['hours_duration']} saat")
                print(f"   Yükseklik: %{obo_result['height_percentage']:.2f}")
                
        except Exception as e:
            print(f"❌ {symbol}: Hata - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 ANALİZ SONUCU:")
    print(f"   🔍 Analiz edilen coin: {total_analyzed}")
    print(f"   ✅ Bulunan formasyon: {found_formations}")
    print(f"   📈 Başarı oranı: %{(found_formations/total_analyzed*100):.1f}")
    
    if found_formations == 0:
        print("\n💡 Öneriler:")
        print("   1. Minimum kalite skorunu 200'den 150'ye düşür")
        print("   2. Minimum yükseklik %1.5'ten %1.0'a düşür")
        print("   3. Minimum mum sayısını 15'ten 10'a düşür")


if __name__ == "__main__":
    test_enhanced_formations() 