#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 GELİŞMİŞ TEKNİK ANALİZ FORMASYONLARI
Yeni formasyon tespit fonksiyonları
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List

def linear_regression(x, y):
    """Basit lineer regresyon (scipy yerine)"""
    x = np.array(x)
    y = np.array(y)
    
    n = len(x)
    if n < 2:
        return 0, 0, 0
    
    # Slope ve intercept hesapla
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)
    
    if denominator == 0:
        return 0, y_mean, 0
    
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    
    # Korelasyon katsayısı
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y_mean) ** 2)
    
    if ss_tot == 0:
        r_squared = 1.0
    else:
        r_squared = 1 - (ss_res / ss_tot)
    
    correlation = np.sqrt(abs(r_squared)) * (1 if slope > 0 else -1)
    
    return slope, intercept, correlation

def detect_symmetric_triangle(df: pd.DataFrame, min_touches: int = 4, lookback: int = 50) -> Optional[Dict]:
    """
    Simetrik Üçgen (Symmetric Triangle) formasyonu tespit eder
    
    Args:
        df: OHLCV DataFrame
        min_touches: Minimum dokunma sayısı
        lookback: Geriye bakış periyodu
        
    Returns:
        Dict: Formasyon bilgileri veya None
    """
    try:
        if len(df) < lookback:
            return None
            
        highs = df['high'].values[-lookback:]
        lows = df['low'].values[-lookback:]
        closes = df['close'].values[-lookback:]
        
        # Tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, len(highs)-2):
            # Tepe noktası
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and 
                highs[i] > highs[i+1] and highs[i] > highs[i+2]):
                peaks.append((i, highs[i]))
            
            # Dip noktası
            if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and 
                lows[i] < lows[i+1] and lows[i] < lows[i+2]):
                troughs.append((i, lows[i]))
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # En son tepe ve dipleri al
        recent_peaks = sorted(peaks, key=lambda x: x[0])[-3:]
        recent_troughs = sorted(troughs, key=lambda x: x[0])[-3:]
        
        if len(recent_peaks) < 2 or len(recent_troughs) < 2:
            return None
        
        # Trend çizgilerini hesapla
        peak_x = [p[0] for p in recent_peaks]
        peak_y = [p[1] for p in recent_peaks]
        trough_x = [t[0] for t in recent_troughs]
        trough_y = [t[1] for t in recent_troughs]
        
        # Üst trend çizgisi (azalan)
        upper_slope, upper_intercept, upper_r = linear_regression(peak_x, peak_y)
        
        # Alt trend çizgisi (yükselen)
        lower_slope, lower_intercept, lower_r = linear_regression(trough_x, trough_y)
        
        # Simetrik üçgen kontrolü
        if upper_slope >= 0 or lower_slope <= 0:  # Üst azalmalı, alt yükselmelidir
            return None
        
        if abs(upper_r) < 0.7 or abs(lower_r) < 0.7:  # Zayıf korelasyon
            return None
        
        # Kesişim noktası
        intersection_x = (lower_intercept - upper_intercept) / (upper_slope - lower_slope)
        intersection_y = upper_slope * intersection_x + upper_intercept
        
        current_price = closes[-1]
        current_index = len(closes) - 1
        
        # Breakout kontrolü
        upper_line_current = upper_slope * current_index + upper_intercept
        lower_line_current = lower_slope * current_index + lower_intercept
        
        breakout_direction = None
        if current_price > upper_line_current * 1.01:  # %1 üstünde
            breakout_direction = 'upward'
        elif current_price < lower_line_current * 0.99:  # %1 altında
            breakout_direction = 'downward'
        
        return {
            'pattern': 'symmetric_triangle',
            'start_index': min(peak_x[0], trough_x[0]),
            'end_index': current_index,
            'upper_slope': upper_slope,
            'lower_slope': lower_slope,
            'upper_intercept': upper_intercept,
            'lower_intercept': lower_intercept,
            'intersection_point': (intersection_x, intersection_y),
            'current_upper_line': upper_line_current,
            'current_lower_line': lower_line_current,
            'breakout_direction': breakout_direction,
            'confidence': min(abs(upper_r), abs(lower_r)),
            'peaks': recent_peaks,
            'troughs': recent_troughs
        }
        
    except Exception as e:
        return None

def detect_flag_pattern(df: pd.DataFrame, trend_period: int = 20, flag_period: int = 10) -> Optional[Dict]:
    """
    Bayrak (Flag) formasyonu tespit eder
    
    Args:
        df: OHLCV DataFrame
        trend_period: Trend periyodu
        flag_period: Bayrak periyodu
        
    Returns:
        Dict: Formasyon bilgileri veya None
    """
    try:
        if len(df) < trend_period + flag_period:
            return None
        
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        volumes = df['volume'].values
        
        # Güçlü trend kontrolü (flagpole)
        trend_start = len(closes) - trend_period - flag_period
        trend_end = len(closes) - flag_period
        
        trend_change = (closes[trend_end] - closes[trend_start]) / closes[trend_start]
        
        if abs(trend_change) < 0.05:  # En az %5 hareket
            return None
        
        trend_direction = 'bullish' if trend_change > 0 else 'bearish'
        
        # Bayrak kısmı (konsolidasyon)
        flag_start = trend_end
        flag_end = len(closes) - 1
        
        flag_highs = highs[flag_start:flag_end+1]
        flag_lows = lows[flag_start:flag_end+1]
        flag_closes = closes[flag_start:flag_end+1]
        flag_volumes = volumes[flag_start:flag_end+1]
        
        # Bayrak eğimi (trend tersine hafif eğim)
        flag_x = list(range(len(flag_closes)))
        flag_slope, flag_intercept, flag_r, _, _ = stats.linregress(flag_x, flag_closes)
        
        # Hacim azalması kontrolü
        avg_trend_volume = np.mean(volumes[trend_start:trend_end])
        avg_flag_volume = np.mean(flag_volumes)
        volume_decrease = avg_flag_volume < avg_trend_volume * 0.8
        
        # Bayrak kriterleri
        flag_range = (np.max(flag_highs) - np.min(flag_lows)) / np.mean(flag_closes)
        
        if flag_range > 0.08:  # Bayrak çok geniş
            return None
        
        # Breakout kontrolü
        current_price = closes[-1]
        flag_high = np.max(flag_highs)
        flag_low = np.min(flag_lows)
        
        breakout_direction = None
        if trend_direction == 'bullish' and current_price > flag_high * 1.01:
            breakout_direction = 'upward'
        elif trend_direction == 'bearish' and current_price < flag_low * 0.99:
            breakout_direction = 'downward'
        
        return {
            'pattern': 'flag',
            'start_index': trend_start,
            'trend_end_index': trend_end,
            'end_index': flag_end,
            'trend_direction': trend_direction,
            'trend_change': trend_change,
            'flag_slope': flag_slope,
            'flag_range': flag_range,
            'volume_decrease': volume_decrease,
            'breakout_direction': breakout_direction,
            'flag_high': flag_high,
            'flag_low': flag_low,
            'confidence': abs(flag_r) if abs(flag_r) > 0.3 else 0.3
        }
        
    except Exception as e:
        return None

def detect_pennant_pattern(df: pd.DataFrame, trend_period: int = 20, pennant_period: int = 10) -> Optional[Dict]:
    """
    Flama (Pennant) formasyonu tespit eder
    
    Args:
        df: OHLCV DataFrame
        trend_period: Trend periyodu
        pennant_period: Flama periyodu
        
    Returns:
        Dict: Formasyon bilgileri veya None
    """
    try:
        if len(df) < trend_period + pennant_period:
            return None
        
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        volumes = df['volume'].values
        
        # Güçlü trend kontrolü
        trend_start = len(closes) - trend_period - pennant_period
        trend_end = len(closes) - pennant_period
        
        trend_change = (closes[trend_end] - closes[trend_start]) / closes[trend_start]
        
        if abs(trend_change) < 0.08:  # En az %8 hareket (bayraktan daha güçlü)
            return None
        
        trend_direction = 'bullish' if trend_change > 0 else 'bearish'
        
        # Flama kısmı (küçük üçgen)
        pennant_start = trend_end
        pennant_end = len(closes) - 1
        
        pennant_highs = highs[pennant_start:pennant_end+1]
        pennant_lows = lows[pennant_start:pennant_end+1]
        pennant_closes = closes[pennant_start:pennant_end+1]
        
        # Flama tepe ve diplerini bul
        peaks = []
        troughs = []
        
        for i in range(1, len(pennant_highs)-1):
            if pennant_highs[i] > pennant_highs[i-1] and pennant_highs[i] > pennant_highs[i+1]:
                peaks.append((i, pennant_highs[i]))
            if pennant_lows[i] < pennant_lows[i-1] and pennant_lows[i] < pennant_lows[i+1]:
                troughs.append((i, pennant_lows[i]))
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # Üst ve alt trend çizgileri
        peak_x = [p[0] for p in peaks]
        peak_y = [p[1] for p in peaks]
        trough_x = [t[0] for t in troughs]
        trough_y = [t[1] for t in troughs]
        
        upper_slope, upper_intercept, upper_r, _, _ = stats.linregress(peak_x, peak_y)
        lower_slope, lower_intercept, lower_r, _, _ = stats.linregress(trough_x, trough_y)
        
        # Flama kriterleri (daralan üçgen)
        if upper_slope >= 0 and lower_slope <= 0:  # Daralan pattern değil
            return None
        
        # Hacim azalması
        avg_trend_volume = np.mean(volumes[trend_start:trend_end])
        avg_pennant_volume = np.mean(volumes[pennant_start:pennant_end+1])
        volume_decrease = avg_pennant_volume < avg_trend_volume * 0.7
        
        # Breakout kontrolü
        current_price = closes[-1]
        current_index = len(pennant_closes) - 1
        
        upper_line_current = upper_slope * current_index + upper_intercept
        lower_line_current = lower_slope * current_index + lower_intercept
        
        breakout_direction = None
        if current_price > upper_line_current * 1.01:
            breakout_direction = 'upward'
        elif current_price < lower_line_current * 0.99:
            breakout_direction = 'downward'
        
        return {
            'pattern': 'pennant',
            'start_index': trend_start,
            'trend_end_index': trend_end,
            'end_index': pennant_end,
            'trend_direction': trend_direction,
            'trend_change': trend_change,
            'upper_slope': upper_slope,
            'lower_slope': lower_slope,
            'volume_decrease': volume_decrease,
            'breakout_direction': breakout_direction,
            'current_upper_line': upper_line_current,
            'current_lower_line': lower_line_current,
            'confidence': min(abs(upper_r), abs(lower_r)),
            'peaks': peaks,
            'troughs': troughs
        }
        
    except Exception as e:
        return None

def detect_rectangle_pattern(df: pd.DataFrame, min_touches: int = 4, lookback: int = 50) -> Optional[Dict]:
    """
    Dikdörtgen (Rectangle) formasyonu tespit eder
    
    Args:
        df: OHLCV DataFrame
        min_touches: Minimum dokunma sayısı
        lookback: Geriye bakış periyodu
        
    Returns:
        Dict: Formasyon bilgileri veya None
    """
    try:
        if len(df) < lookback:
            return None
            
        highs = df['high'].values[-lookback:]
        lows = df['low'].values[-lookback:]
        closes = df['close'].values[-lookback:]
        volumes = df['volume'].values[-lookback:]
        
        # Tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, len(highs)-2):
            # Tepe noktası
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and 
                highs[i] > highs[i+1] and highs[i] > highs[i+2]):
                peaks.append((i, highs[i]))
            
            # Dip noktası
            if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and 
                lows[i] < lows[i+1] and lows[i] < lows[i+2]):
                troughs.append((i, lows[i]))
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # Direnç ve destek seviyelerini hesapla
        peak_prices = [p[1] for p in peaks]
        trough_prices = [t[1] for t in troughs]
        
        resistance_level = np.mean(peak_prices)
        support_level = np.mean(trough_prices)
        
        # Seviye toleransı
        resistance_tolerance = resistance_level * 0.02  # %2
        support_tolerance = support_level * 0.02
        
        # Dokunma sayılarını kontrol et
        resistance_touches = sum(1 for price in peak_prices 
                               if abs(price - resistance_level) <= resistance_tolerance)
        support_touches = sum(1 for price in trough_prices 
                            if abs(price - support_level) <= support_tolerance)
        
        if resistance_touches < 2 or support_touches < 2:
            return None
        
        # Dikdörtgen yüksekliği
        rectangle_height = resistance_level - support_level
        rectangle_height_pct = rectangle_height / support_level
        
        if rectangle_height_pct < 0.03 or rectangle_height_pct > 0.20:  # %3-20 arası
            return None
        
        # Mevcut fiyat pozisyonu
        current_price = closes[-1]
        current_index = len(closes) - 1
        
        # Breakout kontrolü
        breakout_direction = None
        breakout_threshold = rectangle_height * 0.02  # %2 kırılım eşiği
        
        if current_price > resistance_level + breakout_threshold:
            breakout_direction = 'upward'
        elif current_price < support_level - breakout_threshold:
            breakout_direction = 'downward'
        
        # Hacim analizi
        avg_volume = np.mean(volumes)
        recent_volume = np.mean(volumes[-5:])  # Son 5 periyod
        volume_increase = recent_volume > avg_volume * 1.2
        
        # Pattern başlangıç ve bitiş
        start_index = min([p[0] for p in peaks] + [t[0] for t in troughs])
        end_index = current_index
        
        return {
            'pattern': 'rectangle',
            'start_index': start_index,
            'end_index': end_index,
            'resistance_level': resistance_level,
            'support_level': support_level,
            'rectangle_height': rectangle_height,
            'rectangle_height_pct': rectangle_height_pct,
            'resistance_touches': resistance_touches,
            'support_touches': support_touches,
            'breakout_direction': breakout_direction,
            'volume_increase': volume_increase,
            'current_price': current_price,
            'confidence': min(resistance_touches, support_touches) / 4.0,
            'peaks': peaks,
            'troughs': troughs
        }
        
    except Exception as e:
        return None

def detect_double_top_bottom(df: pd.DataFrame, lookback: int = 50, tolerance: float = 0.02) -> Optional[Dict]:
    """
    Çift Tepe / Çift Dip (Double Top/Bottom) formasyonu tespit eder
    
    Args:
        df: OHLCV DataFrame
        lookback: Geriye bakış periyodu
        tolerance: Fiyat toleransı (%)
        
    Returns:
        Dict: Formasyon bilgileri veya None
    """
    try:
        if len(df) < lookback:
            return None
            
        highs = df['high'].values[-lookback:]
        lows = df['low'].values[-lookback:]
        closes = df['close'].values[-lookback:]
        volumes = df['volume'].values[-lookback:]
        
        # Tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(3, len(highs)-3):
            # Güçlü tepe noktası
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i-3] and
                highs[i] > highs[i+1] and highs[i] > highs[i+2] and highs[i] > highs[i+3]):
                peaks.append((i, highs[i]))
            
            # Güçlü dip noktası
            if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i-3] and
                lows[i] < lows[i+1] and lows[i] < lows[i+2] and lows[i] < lows[i+3]):
                troughs.append((i, lows[i]))
        
        # Çift tepe kontrolü
        if len(peaks) >= 2:
            # Son iki tepeyi al
            last_two_peaks = sorted(peaks, key=lambda x: x[0])[-2:]
            peak1_idx, peak1_price = last_two_peaks[0]
            peak2_idx, peak2_price = last_two_peaks[1]
            
            # Fiyat benzerliği kontrolü
            price_diff = abs(peak1_price - peak2_price) / peak1_price
            
            if price_diff <= tolerance and peak2_idx > peak1_idx + 5:  # En az 5 periyod ara
                # Aradaki dip
                valley_start = peak1_idx
                valley_end = peak2_idx
                valley_lows = lows[valley_start:valley_end+1]
                valley_idx = valley_start + np.argmin(valley_lows)
                valley_price = np.min(valley_lows)
                
                # Neckline seviyesi
                neckline = valley_price
                
                # Breakout kontrolü
                current_price = closes[-1]
                breakout_direction = None
                
                if current_price < neckline * (1 - tolerance):
                    breakout_direction = 'downward'
                
                # Hacim analizi
                peak1_volume = volumes[peak1_idx]
                peak2_volume = volumes[peak2_idx]
                volume_divergence = peak2_volume < peak1_volume * 0.8  # İkinci tepede hacim azalması
                
                return {
                    'pattern': 'double_top',
                    'start_index': peak1_idx,
                    'end_index': len(closes) - 1,
                    'peak1_index': peak1_idx,
                    'peak1_price': peak1_price,
                    'peak2_index': peak2_idx,
                    'peak2_price': peak2_price,
                    'valley_index': valley_idx,
                    'valley_price': valley_price,
                    'neckline': neckline,
                    'price_similarity': 1 - price_diff,
                    'volume_divergence': volume_divergence,
                    'breakout_direction': breakout_direction,
                    'confidence': (1 - price_diff) * 0.7 + (0.3 if volume_divergence else 0)
                }
        
        # Çift dip kontrolü
        if len(troughs) >= 2:
            # Son iki dibi al
            last_two_troughs = sorted(troughs, key=lambda x: x[0])[-2:]
            trough1_idx, trough1_price = last_two_troughs[0]
            trough2_idx, trough2_price = last_two_troughs[1]
            
            # Fiyat benzerliği kontrolü
            price_diff = abs(trough1_price - trough2_price) / trough1_price
            
            if price_diff <= tolerance and trough2_idx > trough1_idx + 5:
                # Aradaki tepe
                peak_start = trough1_idx
                peak_end = trough2_idx
                peak_highs = highs[peak_start:peak_end+1]
                peak_idx = peak_start + np.argmax(peak_highs)
                peak_price = np.max(peak_highs)
                
                # Neckline seviyesi
                neckline = peak_price
                
                # Breakout kontrolü
                current_price = closes[-1]
                breakout_direction = None
                
                if current_price > neckline * (1 + tolerance):
                    breakout_direction = 'upward'
                
                # Hacim analizi
                trough1_volume = volumes[trough1_idx]
                trough2_volume = volumes[trough2_idx]
                volume_increase = trough2_volume > trough1_volume * 1.2  # İkinci dipte hacim artışı
                
                return {
                    'pattern': 'double_bottom',
                    'start_index': trough1_idx,
                    'end_index': len(closes) - 1,
                    'trough1_index': trough1_idx,
                    'trough1_price': trough1_price,
                    'trough2_index': trough2_idx,
                    'trough2_price': trough2_price,
                    'peak_index': peak_idx,
                    'peak_price': peak_price,
                    'neckline': neckline,
                    'price_similarity': 1 - price_diff,
                    'volume_increase': volume_increase,
                    'breakout_direction': breakout_direction,
                    'confidence': (1 - price_diff) * 0.7 + (0.3 if volume_increase else 0)
                }
        
        return None
        
    except Exception as e:
        return None

def analyze_all_advanced_patterns(df: pd.DataFrame) -> Dict[str, Optional[Dict]]:
    """
    Tüm gelişmiş formasyonları analiz eder
    
    Args:
        df: OHLCV DataFrame
        
    Returns:
        Dict: Tüm formasyon sonuçları
    """
    results = {}
    
    try:
        results['symmetric_triangle'] = detect_symmetric_triangle(df)
        results['flag'] = detect_flag_pattern(df)
        results['pennant'] = detect_pennant_pattern(df)
        results['rectangle'] = detect_rectangle_pattern(df)
        results['double_top_bottom'] = detect_double_top_bottom(df)
        
        # Aktif formasyonları filtrele
        active_patterns = {k: v for k, v in results.items() if v is not None}
        
        return {
            'all_results': results,
            'active_patterns': active_patterns,
            'pattern_count': len(active_patterns)
        }
        
    except Exception as e:
        return {'error': str(e), 'all_results': results}

if __name__ == "__main__":
    # Test fonksiyonu
    print("Gelismis Teknik Analiz Formasyonlari hazir!")
    print("Kullanilabilir fonksiyonlar:")
    print("- detect_symmetric_triangle()")
    print("- detect_flag_pattern()")
    print("- detect_pennant_pattern()")
    print("- detect_rectangle_pattern()")
    print("- detect_double_top_bottom()")
    print("- analyze_all_advanced_patterns()")
