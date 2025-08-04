#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNIFIED TRADING BOT ANALYSIS MODULE
===================================

Bu modül, tüm botanlik dosyalarının birleştirilmiş ve optimize edilmiş versiyonudur.
Ana özellikler:
- Çoklu zaman dilimi analizi (1h, 4h, 1d, 1w)
- Gelişmiş formasyon tespiti (TOBO, OBO, Cup&Handle, Falling Wedge, vb.)
- RSI, MACD, Volume, Breakout analizi
- Fibonacci seviyeleri ve Bollinger Bands
- Risk/Reward optimizasyonu
- Telegram bildirimleri
- Lisans yönetimi

Author: Trading Bot Team
Version: 2.0 (Unified)
"""

import requests
import time
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import random

# Local imports
from data_fetcher import fetch_ohlcv
from formation_detector import (
    find_all_tobo, find_all_obo, detect_falling_wedge, 
    calculate_fibonacci_levels, calculate_macd, calculate_bollinger_bands, 
    calculate_stochastic, calculate_adx, analyze_all_formations, 
    analyze_all_formations_advanced, detect_cup_and_handle, 
    detect_bullish_bearish_flag_advanced, detect_rising_wedge, 
    calculate_ichimoku, calculate_supertrend, calculate_vwap, 
    calculate_obv, calculate_heikin_ashi, analyze_rsi_formation_strength, 
    analyze_macd_breakout_signal, analyze_volume_pattern, 
    calculate_formation_score, analyze_breakout_candle, 
    calculate_formation_geometric_score, backtest_formation_success_rate, 
    analyze_multiple_timeframes, get_multiple_timeframe_data, 
    format_multitimeframe_analysis_result, filter_high_quality_formations,
    calculate_formation_quality_score
)
from telegram_notifier import send_telegram_message
from license_manager import LicenseManager
from signal_visualizer import SignalVisualizer

# Platform compatibility
try:
    import msvcrt
except ImportError:
    # Linux/Mac için msvcrt yok, dummy fonksiyon
    def msvcrt():
        return None


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

from utils import format_price


def get_usdt_symbols():
    """
    Binance Futures'tan USDT çiftlerini çeker
    
    Returns:
        list: USDT sembol listesi
    """
    try:
        url = 'https://fapi.binance.com/fapi/v1/exchangeInfo'
        response = requests.get(url, timeout=10)
        data = response.json()
        symbols = [s['symbol'] for s in data['symbols'] 
                  if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
        return symbols
    except Exception as e:
        print(f"❌ Sembol listesi alınamadı: {e}")
        return []


def get_current_price(symbol):
    """
    Sembolün anlık fiyatını çeker
    
    Args:
        symbol (str): Sembol adı
        
    Returns:
        float: Anlık fiyat veya None
    """
    try:
        url = f'https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}'
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data['price']) if 'price' in data else None
    except Exception as e:
        print(f"❌ {symbol} fiyatı alınamadı: {e}")
        return None


# ============================================================================
# RISK MANAGEMENT FUNCTIONS
# ============================================================================

def calculate_optimal_risk(symbol, current_price, tp, sl, direction):
    """
    ISOLATED işlemler için sabit 5x kaldıraç ile risk seviyesini hesaplar
    
    Args:
        symbol (str): Sembol adı
        current_price (float): Mevcut fiyat
        tp (float): Take Profit seviyesi
        sl (float): Stop Loss seviyesi
        direction (str): 'Long' veya 'Short'
        
    Returns:
        dict: Risk hesaplama sonuçları
    """
    if direction == 'Long':
        if current_price <= sl or tp <= current_price:
            return {
                'risk_level': 'Geçersiz',
                'leverage': '5x',
                'position_size': 'Kasanın %5\'i',
                'risk_reward': '0.0:1',
                'potential_gain': '%0.0',
                'margin_type': 'ISOLATED',
                'risk_amount': '%0.0',
                'max_loss': '%0.0'
            }
        risk_percent = (current_price - sl) / current_price
        reward_percent = (tp - current_price) / current_price
    else:
        if current_price >= sl or tp >= current_price:
            return {
                'risk_level': 'Geçersiz',
                'leverage': '5x',
                'position_size': 'Kasanın %5\'i',
                'risk_reward': '0.0:1',
                'potential_gain': '%0.0',
                'margin_type': 'ISOLATED',
                'risk_amount': '%0.0',
                'max_loss': '%0.0'
            }
        risk_percent = (sl - current_price) / current_price
        reward_percent = (current_price - tp) / current_price
    
    risk_reward_ratio = reward_percent / risk_percent if risk_percent > 0 else 0
    
    return {
        'risk_level': 'Sabit 5x',
        'leverage': '5x',
        'position_size': 'Kasanın %5\'i',
        'risk_reward': f'{risk_reward_ratio:.1f}:1',
        'potential_gain': f'%{reward_percent*5*100:.1f}',
        'margin_type': 'ISOLATED',
        'risk_amount': f'%{risk_percent*5*100:.1f}',
        'max_loss': f'%{risk_percent*5*100:.1f}'
    }


def optimize_tp_sl_fixed(entry_price, current_tp, current_sl, direction, fibo_levels, bb_data=None):
    """
    Düzeltilmiş TP ve SL optimizasyonu - Gerçekçi R/R oranları (1.2-1.8 arası)
    
    Args:
        entry_price (float): Giriş fiyatı
        current_tp (float): Mevcut Take Profit
        current_sl (float): Mevcut Stop Loss
        direction (str): 'Long' veya 'Short'
        fibo_levels (dict): Fibonacci seviyeleri
        bb_data (dict): Bollinger Bands verisi
        
    Returns:
        tuple: (optimized_tp, optimized_sl, rr_ratio)
    """
    if direction == 'Long':
        # Mantık kontrolü
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
                best_option = random.choice(all_options)
                return best_option['tp'], best_option['sl'], best_option['rr']
            
            return current_tp, current_sl, current_rr
        else:
            # Mevcut R/R'yi kontrol et
            if current_rr > 1.8:
                new_tp = entry_price - (current_sl - entry_price) * 1.8
                return new_tp, current_sl, 1.8
            return current_tp, current_sl, current_rr


# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def check_neckline_breakout(symbol, neckline_price, direction, timeframes=['4h', '1d']):
    """
    4H ve 1D grafiklerde boyun çizgisi kırılımını kontrol eder
    
    Args:
        symbol (str): Sembol adı
        neckline_price (float): Boyun çizgisi fiyatı
        direction (str): 'Long' veya 'Short'
        timeframes (list): Kontrol edilecek zaman dilimleri
        
    Returns:
        dict: Kırılım bilgileri
    """
    breakout_info = {}
    
    for timeframe in timeframes:
        try:
            df = fetch_ohlcv(symbol, timeframe)
            if df is None or df.empty:
                continue
                
            # Son 5 mumu kontrol et
            recent_candles = df.tail(5)
            current_price = df['close'].iloc[-1]
            
            # Hacim analizi
            avg_volume = df['volume'].tail(20).mean()
            current_volume = df['volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Kırılım kontrolü
            breakout_confirmed = False
            breakout_strength = 0
            
            if direction == 'Long':  # TOBO - yukarı kırılım
                if current_price > neckline_price:
                    candles_above = sum(1 for price in recent_candles['close'] if price > neckline_price)
                    if candles_above >= 2:  # En az 2 mum üstte
                        breakout_confirmed = True
                        breakout_strength = (current_price - neckline_price) / neckline_price * 100
            else:  # OBO - aşağı kırılım
                if current_price < neckline_price:
                    candles_below = sum(1 for price in recent_candles['close'] if price < neckline_price)
                    if candles_below >= 2:  # En az 2 mum altta
                        breakout_confirmed = True
                        breakout_strength = (neckline_price - current_price) / neckline_price * 100
            
            breakout_info[timeframe] = {
                'confirmed': breakout_confirmed,
                'strength': breakout_strength,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'volume_confirmed': volume_ratio > 1.5,
                'neckline_price': neckline_price
            }
            
        except Exception as e:
            print(f"❌ {timeframe} analizi hatası: {e}")
                continue
            
    return breakout_info


def analyze_volume_confirmation(symbol, timeframes=['4h', '1d']):
    """
    Hacim teyidi analizi
    
    Args:
        symbol (str): Sembol adı
        timeframes (list): Kontrol edilecek zaman dilimleri
        
    Returns:
        dict: Hacim analizi sonuçları
    """
    volume_analysis = {}
    
    for timeframe in timeframes:
        try:
            df = fetch_ohlcv(symbol, timeframe)
                if df is None or df.empty:
                continue
            
            # Son 20 mumun hacim ortalaması
            recent_volume = df['volume'].tail(20)
            avg_volume = recent_volume.mean()
            current_volume = df['volume'].iloc[-1]
            
            # Hacim artış oranı
            volume_increase = (current_volume - avg_volume) / avg_volume * 100 if avg_volume > 0 else 0
            
            # Son 5 mumun hacim trendi
            recent_5_volume = df['volume'].tail(5)
            volume_trend = 'Yükselen' if recent_5_volume.iloc[-1] > recent_5_volume.iloc[0] else 'Düşen'
            
            volume_analysis[timeframe] = {
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'volume_increase': volume_increase,
                'volume_trend': volume_trend,
                'volume_confirmed': volume_increase > 50  # %50'den fazla artış
            }
            
        except Exception as e:
            print(f"❌ {timeframe} hacim analizi hatası: {e}")
            continue
    
    return volume_analysis


def calculate_signal_score(df, formation_type, formation_data, macd_data, bb_data, stoch_data, adx_data, ma_trend):
    """
    Sinyal gücünü hesaplar
    
    Args:
        df (DataFrame): OHLCV verisi
        formation_type (str): Formasyon tipi
        formation_data (dict): Formasyon verisi
        macd_data (dict): MACD verisi
        bb_data (dict): Bollinger Bands verisi
        stoch_data (dict): Stochastic verisi
        adx_data (dict): ADX verisi
        ma_trend (str): MA trendi
        
    Returns:
        dict: Sinyal skoru ve detayları
    """
    score = 0
    details = {}
    
    # Formasyon gücü (0-30 puan)
    if formation_data and 'score' in formation_data:
        formation_score = formation_data['score']
        score += formation_score
        details['formation_score'] = formation_score
    
    # MACD analizi (0-20 puan)
    if macd_data:
        macd_score = 0
        if macd_data.get('signal_crossover', False):
            macd_score += 10
        if macd_data.get('histogram_positive', False):
            macd_score += 5
        if macd_data.get('trend_alignment', False):
            macd_score += 5
        score += macd_score
        details['macd_score'] = macd_score
    
    # Bollinger Bands analizi (0-15 puan)
    if bb_data:
        bb_score = 0
        current_price = df['close'].iloc[-1]
        if bb_data.get('price_position') == 'upper_band':
            bb_score += 8
        elif bb_data.get('price_position') == 'middle_band':
            bb_score += 5
        if bb_data.get('band_squeeze', False):
            bb_score += 7
        score += bb_score
        details['bb_score'] = bb_score
    
    # Stochastic analizi (0-15 puan)
    if stoch_data:
        stoch_score = 0
        if stoch_data.get('oversold', False):
            stoch_score += 8
        elif stoch_data.get('overbought', False):
            stoch_score += 3
        if stoch_data.get('signal_crossover', False):
            stoch_score += 7
        score += stoch_score
        details['stoch_score'] = stoch_score
    
    # ADX trend gücü (0-10 puan)
    if adx_data:
        adx_score = 0
        adx_value = adx_data.get('adx', 0)
        if adx_value > 25:
            adx_score += 5
        if adx_value > 30:
            adx_score += 5
        score += adx_score
        details['adx_score'] = adx_score
    
    # MA trend uyumu (0-10 puan)
    ma_score = 0
    if ma_trend == 'Bullish':
        ma_score += 10
    elif ma_trend == 'Neutral':
        ma_score += 5
    score += ma_score
    details['ma_score'] = ma_score
    
    # Toplam skor (0-100)
    total_score = min(score, 100)
    
    return {
        'total_score': total_score,
        'details': details,
        'strength': 'Güçlü' if total_score >= 70 else 'Orta' if total_score >= 50 else 'Zayıf'
    }


# ============================================================================
# MAIN ANALYSIS FUNCTION
# ============================================================================

def analyze_symbol(symbol, interval='4h', debug_mode=False):
    """
    Tek sembol için kapsamlı analiz yapar
    
    Args:
        symbol (str): Sembol adı
        interval (str): Zaman dilimi
        debug_mode (bool): Debug modu
        
    Returns:
        dict: Analiz sonuçları
    """
    try:
        # Veri çekme
                    df = fetch_ohlcv(symbol, interval)
                    if df is None or df.empty:
                        return None
                    
        current_price = df['close'].iloc[-1]
        
        if debug_mode:
            print(f"\n🔍 {symbol} analizi başlatılıyor...")
            print(f"📊 Mevcut fiyat: {format_price(current_price)}")
        
        # ÇOKLU FORMASYON TESPİTİ
        all_formations = []
        
        # TOBO formasyonları
        tobo_formations = find_all_tobo(df)
        if tobo_formations:
            for formation in tobo_formations:
                if formation and isinstance(formation, dict):
                    formation['type'] = 'TOBO'
                    formation['direction'] = 'Long'
                    all_formations.append(formation)
        
        # OBO formasyonları
        obo_formations = find_all_obo(df)
        if obo_formations:
            for formation in obo_formations:
                if formation and isinstance(formation, dict):
                    formation['type'] = 'OBO'
                    formation['direction'] = 'Short'
                    all_formations.append(formation)
        
        # Cup & Handle formasyonları
        cup_handle_formations = detect_cup_and_handle(df)
        if cup_handle_formations:
            for formation in cup_handle_formations:
                if formation and isinstance(formation, dict):
                    formation['type'] = 'CUP_HANDLE'
                    formation['direction'] = 'Long'
                    all_formations.append(formation)
        
        # Falling Wedge formasyonları
        falling_wedge_formations = detect_falling_wedge(df)
        if falling_wedge_formations:
            for formation in falling_wedge_formations:
                if formation and isinstance(formation, dict):
                    formation['type'] = 'FALLING_WEDGE'
                    formation['direction'] = 'Long'
                    all_formations.append(formation)
        
        # Bullish/Bearish Flag formasyonları
        flag_formations = detect_bullish_bearish_flag_advanced(df)
        if flag_formations:
            for formation in flag_formations:
                if formation and isinstance(formation, dict):
                    if formation.get('type') == 'Bullish Flag':
                        formation['type'] = 'BULLISH_FLAG'
                        formation['direction'] = 'Long'
                    elif formation.get('type') == 'Bearish Flag':
                        formation['type'] = 'BEARISH_FLAG'
                        formation['direction'] = 'Short'
                    all_formations.append(formation)
        
        if debug_mode:
            print(f"📈 Tespit edilen formasyon sayısı: {len(all_formations)}")
            for formation in all_formations:
                print(f"   - {formation.get('type', 'UNKNOWN')} (Skor: {formation.get('score', 'N/A')})")
        
        # KALİTE FİLTRESİ - Sadece güçlü formasyonları al
        if all_formations:
            filtered_formations = filter_high_quality_formations(df, all_formations, debug_mode)
            
            if debug_mode:
                print(f"🎯 Kalite filtresi sonrası: {len(filtered_formations)} güçlü formasyon")
                for formation in filtered_formations:
                    print(f"   ✅ {formation.get('type', 'UNKNOWN')} (Kalite Skor: {formation.get('quality_score', 'N/A')})")
                        else:
            filtered_formations = []
        
        # ÇOKLU FORMASYON BİLDİRİMİ - Tüm güçlü formasyonları al
        strong_formations = []
        for formation in filtered_formations:
            quality_score = formation.get('quality_score', 0)
            if quality_score >= 80:  # Güçlü formasyon kriteri
                strong_formations.append(formation)
        
        # En iyi formasyonu seç (kalite skoruna göre) - Ana analiz için
        best_formation = None
        best_score = 0
        
        for formation in filtered_formations:
            quality_score = formation.get('quality_score', 0)
            if quality_score > best_score:
                best_score = quality_score
                best_formation = formation
        
        # Çoklu zaman dilimi analizi
        timeframes = ['1h', '4h', '1d', '1w']
        multi_timeframe_data = get_multiple_timeframe_data(symbol, timeframes)
        
        # Çoklu zaman dilimi analizi (sadece formasyon varsa)
        multi_timeframe_analysis = None
        if best_formation and multi_timeframe_data:
            formation_type = best_formation.get('type', 'TOBO')
            multi_timeframe_analysis = analyze_multiple_timeframes(multi_timeframe_data, formation_type, symbol)
        
        # İndikatör hesaplamaları
        fibo_levels = calculate_fibonacci_levels(df)
                            macd_data = calculate_macd(df)
                            bb_data = calculate_bollinger_bands(df)
                            stoch_data = calculate_stochastic(df)
                            adx_data = calculate_adx(df)
        ichimoku_data = calculate_ichimoku(df)
        supertrend_data = calculate_supertrend(df)
        vwap_data = calculate_vwap(df)
        obv_data = calculate_obv(df)
        heikin_ashi_data = calculate_heikin_ashi(df)
        
        # MA trend analizi
        ma_20 = df['close'].rolling(window=20).mean().iloc[-1]
        ma_50 = df['close'].rolling(window=50).mean().iloc[-1]
        
        if current_price > ma_20 > ma_50:
            ma_trend = 'Bullish'
        elif current_price < ma_20 < ma_50:
            ma_trend = 'Bearish'
        else:
            ma_trend = 'Neutral'
        
        # Sinyal skoru hesapla
        signal_score = calculate_signal_score(
            df, 
            best_formation['type'] if best_formation else None,
            best_formation,
            macd_data,
            bb_data,
            stoch_data,
            adx_data,
            ma_trend
        )
        
        # Risk hesaplama
        if best_formation:
            tp = best_formation.get('tp', current_price * 1.02)
            sl = best_formation.get('sl', current_price * 0.98)
            direction = best_formation.get('direction', 'Long')
            
            risk_analysis = calculate_optimal_risk(symbol, current_price, tp, sl, direction)
            
            # TP/SL optimizasyonu
            optimized_tp, optimized_sl, rr_ratio = optimize_tp_sl_fixed(
                current_price, tp, sl, direction, fibo_levels, bb_data
            )
        else:
            risk_analysis = None
            optimized_tp = optimized_sl = rr_ratio = None
        
        # EN İYİ FORMASYONU SEÇ VE GÖRSELLEŞTİR
        if strong_formations:
            # En yüksek kalite skoruna sahip formasyonu seç
            best_strong_formation = None
            best_quality_score = 0
            
            for formation in strong_formations:
                quality_score = formation.get('quality_score', 0)
                if quality_score > best_quality_score:
                    best_quality_score = quality_score
                    best_strong_formation = formation
            
            if best_strong_formation:
                try:
                    visualizer = SignalVisualizer()
                    
                    if debug_mode:
                        formation_type = best_strong_formation.get('type', 'UNKNOWN')
                        print(f"🎯 En iyi formasyon seçildi: {formation_type} (Skor: {best_quality_score})")
                    
                    # Sadece en iyi formasyonu görselleştir
                    visualizer.visualize_single_formation(symbol, interval, best_strong_formation, debug_mode)
                        
                except Exception as e:
                    print(f"❌ Görselleştirme hatası: {e}")
        elif best_formation and signal_score['total_score'] >= 60:
            # Eski yöntem - sadece en iyi formasyon
            try:
                visualizer = SignalVisualizer()
                visualizer.detect_and_visualize_formation(symbol, interval)
                except Exception as e:
                print(f"❌ Görselleştirme hatası: {e}")
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'interval': interval,
            'best_formation': best_formation,
            'signal_score': signal_score,
            'risk_analysis': risk_analysis,
            'optimized_tp': optimized_tp,
            'optimized_sl': optimized_sl,
            'rr_ratio': rr_ratio,
            'multi_timeframe_analysis': multi_timeframe_analysis,
            'indicators': {
                'macd': macd_data,
                'bollinger_bands': bb_data,
                'stochastic': stoch_data,
                'adx': adx_data,
                'ichimoku': ichimoku_data,
                'supertrend': supertrend_data,
                'vwap': vwap_data,
                'obv': obv_data,
                'heikin_ashi': heikin_ashi_data,
                'fibonacci': fibo_levels
            },
            'ma_trend': ma_trend,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ {symbol} analizi hatası: {e}")
        return None


def get_scan_results():
    """
    Tüm semboller için tarama yapar ve sonuçları döndürür
    
    Returns:
        dict: Tarama sonuçları
    """
    try:
        # Sembol listesini al
        symbols = get_usdt_symbols()
        if not symbols:
            return {'error': 'Sembol listesi alınamadı'}
        
        print(f"🔍 {len(symbols)} sembol taranıyor...")
        
        # Çoklu thread ile analiz
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_symbol = {executor.submit(analyze_symbol, symbol): symbol for symbol in symbols}
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    if result and result.get('signal_score', {}).get('total_score', 0) >= 50:
                        results.append(result)
    except Exception as e:
                    print(f"❌ {symbol} analizi hatası: {e}")
        
        # Sonuçları skora göre sırala
        results.sort(key=lambda x: x.get('signal_score', {}).get('total_score', 0), reverse=True)
                
                return {
            'total_symbols': len(symbols),
            'found_opportunities': len(results),
            'results': results,
            'scan_time': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Tarama hatası: {e}")
        return {'error': str(e)}


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """
    Ana fonksiyon - Bot'u başlatır
    """
    print("🚀 Unified Trading Bot başlatılıyor...")
    
        # Lisans yöneticisini başlat
        license_manager = LicenseManager()
        
    try:
        # Tarama yap
        scan_results = get_scan_results()
        
        if 'error' in scan_results:
            print(f"❌ Tarama hatası: {scan_results['error']}")
            return
        
        print(f"✅ Tarama tamamlandı!")
        print(f"📊 Toplam sembol: {scan_results['total_symbols']}")
        print(f"🎯 Bulunan fırsat: {scan_results['found_opportunities']}")
        
        # Sonuçları göster
        for i, result in enumerate(scan_results['results'][:10], 1):
            symbol = result['symbol']
            score = result['signal_score']['total_score']
            formation = result['best_formation']['type'] if result['best_formation'] else 'Yok'
            
            print(f"{i}. {symbol} - Skor: {score} - Formasyon: {formation}")
        
    except KeyboardInterrupt:
        print("\n👋 Bot durduruldu.")
            except Exception as e:
        print(f"❌ Ana fonksiyon hatası: {e}")


if __name__ == "__main__":
    main()