import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from data_fetcher import fetch_ohlcv
from formation_detector import find_all_tobo, find_all_obo, detect_falling_wedge, calculate_fibonacci_levels, calculate_macd, calculate_bollinger_bands, calculate_stochastic, calculate_adx, analyze_all_formations, analyze_all_formations_advanced, detect_cup_and_handle, detect_bullish_bearish_flag_advanced, detect_rising_wedge, calculate_ichimoku, calculate_supertrend, calculate_vwap, calculate_obv, calculate_heikin_ashi
# from bot import format_price  # bot.py dosyası yok, bot_backup.py var
try:
    import msvcrt
except ImportError:
    # Linux/Mac için msvcrt yok, dummy fonksiyon
    def msvcrt():
        return None
import pandas as pd
import numpy as np
from telegram_notifier import send_telegram_message
from datetime import datetime
from license_manager import LicenseManager


def format_price(price):
    if price == 0:
        return '0'
    elif price < 0.0001:
        return f"{price:.8f}"
    elif price < 1:
        return f"{price:.6f}"
    elif price < 10:
        return f"{price:.4f}"
    elif price < 100:
        return f"{price:.3f}"
    else:
        return f"{price:.2f}"


def get_usdt_symbols():
    url = 'https://fapi.binance.com/fapi/v1/exchangeInfo'
    response = requests.get(url)
    data = response.json()
    symbols = [s['symbol'] for s in data['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
    return symbols


def get_current_price(symbol):
    url = f'https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}'
    response = requests.get(url)
    data = response.json()
    return float(data['price']) if 'price' in data else None


def calculate_optimal_risk(symbol, current_price, tp, sl, direction):
    """ISOLATED işlemler için sabit 5x kaldıraç ile risk seviyesini hesapla"""
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


def check_neckline_breakout(symbol, neckline_price, direction, timeframes=['4h', '1d']):
    """
    4H ve 1D grafiklerde boyun çizgisi kırılımını kontrol eder
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
                # Fiyat boyun çizgisinin üstünde mi?
                if current_price > neckline_price:
                    # Son 3 mumda kırılım var mı?
                    candles_above = sum(1 for price in recent_candles['close'] if price > neckline_price)
                    if candles_above >= 2:  # En az 2 mum üstte
                        breakout_confirmed = True
                        breakout_strength = (current_price - neckline_price) / neckline_price * 100
            else:  # OBO - aşağı kırılım
                # Fiyat boyun çizgisinin altında mı?
                if current_price < neckline_price:
                    # Son 3 mumda kırılım var mı?
                    candles_below = sum(1 for price in recent_candles['close'] if price < neckline_price)
                    if candles_below >= 2:  # En az 2 mum altta
                        breakout_confirmed = True
                        breakout_strength = (neckline_price - current_price) / neckline_price * 100
            
            breakout_info[timeframe] = {
                'confirmed': breakout_confirmed,
                'strength': breakout_strength,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'volume_confirmed': volume_ratio > 1.5,  # Hacim 1.5x üstünde
                'neckline_price': neckline_price
            }
            
        except Exception as e:
            continue
    
    return breakout_info


def analyze_volume_confirmation(symbol, timeframes=['4h', '1d']):
    """
    Hacim teyidi analizi
    """
    volume_analysis = {}
    
    for timeframe in timeframes:
        try:
            df = fetch_ohlcv(symbol, timeframe)
            if df is None or df.empty:
                continue
            
            # Son 20 mumun ortalama hacmi
            avg_volume = df['volume'].tail(20).mean()
            current_volume = df['volume'].iloc[-1]
            
            # Hacim trendi (son 5 mum)
            recent_volumes = df['volume'].tail(5)
            volume_trend = 'Yükselen' if recent_volumes.iloc[-1] > recent_volumes.iloc[0] else 'Düşen'
            
            # Hacim teyidi
            volume_confirmed = current_volume > avg_volume * 1.5  # 1.5x üstünde
            
            volume_analysis[timeframe] = {
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1,
                'volume_trend': volume_trend,
                'confirmed': volume_confirmed
            }
            
        except Exception as e:
            continue
    
    return volume_analysis


def calculate_signal_score(df, formation_type, formation_data, macd_data, bb_data, stoch_data, adx_data, ma_trend):
    """
    Sinyal ağırlıklandırma sistemi - Çelişkileri çözer
    """
    total_score = 0
    max_score = 100
    signals = []
    
    # 1. Formasyon Ağırlığı (35 puan) - Daha dengeli
    if formation_type == 'TOBO':
        formation_score = 35
        signals.append(f"TOBO Formasyonu: +{formation_score}")
    elif formation_type == 'OBO':
        formation_score = 35
        signals.append(f"OBO Formasyonu: +{formation_score}")
    else:
        formation_score = 0
    
    total_score += formation_score
    
    # 2. MA Trend Ağırlığı (15 puan) - Daha düşük ağırlık
    if 'Yükseliş' in ma_trend:
        ma_score = 15
        ma_signal = 'Long'
        signals.append(f"MA Trend (Yükseliş): +{ma_score}")
    elif 'Düşüş' in ma_trend:
        ma_score = 15
        ma_signal = 'Short'
        signals.append(f"MA Trend (Düşüş): +{ma_score}")
    else:
        ma_score = 0
        ma_signal = 'Neutral'
    
    total_score += ma_score
    
    # 3. MACD Ağırlığı (15 puan)
    if macd_data:
        if macd_data['trend'] == 'Bullish':
            macd_score = 15
            macd_signal = 'Long'
            signals.append(f"MACD (Bullish): +{macd_score}")
        else:
            macd_score = 15
            macd_signal = 'Short'
            signals.append(f"MACD (Bearish): +{macd_score}")
    else:
        macd_score = 0
        macd_signal = 'Neutral'
    
    total_score += macd_score
    
    # 4. ADX Ağırlığı (10 puan)
    if adx_data:
        if adx_data['trend_direction'] == 'Bullish':
            adx_score = 10
            adx_signal = 'Long'
            signals.append(f"ADX (Bullish): +{adx_score}")
        else:
            adx_score = 10
            adx_signal = 'Short'
            signals.append(f"ADX (Bearish): +{adx_score}")
    else:
        adx_score = 0
        adx_signal = 'Neutral'
    
    total_score += adx_score
    
    # 5. Bollinger Bands Ağırlığı (10 puan)
    if bb_data:
        if bb_data['signal'] == 'Oversold':
            bb_score = 10
            bb_signal = 'Long'
            signals.append(f"Bollinger (Oversold): +{bb_score}")
        elif bb_data['signal'] == 'Overbought':
            bb_score = 10
            bb_signal = 'Short'
            signals.append(f"Bollinger (Overbought): +{bb_score}")
        else:
            bb_score = 0
            bb_signal = 'Neutral'
    else:
        bb_score = 0
        bb_signal = 'Neutral'
    
    total_score += bb_score
    
    # 6. Stochastic Ağırlığı (5 puan)
    if stoch_data:
        if stoch_data['signal'] == 'Oversold':
            stoch_score = 5
            stoch_signal = 'Long'
            signals.append(f"Stochastic (Oversold): +{stoch_score}")
        elif stoch_data['signal'] == 'Overbought':
            stoch_score = 5
            stoch_signal = 'Short'
            signals.append(f"Stochastic (Overbought): +{stoch_score}")
        else:
            stoch_score = 0
            stoch_signal = 'Neutral'
    else:
        stoch_score = 0
        stoch_signal = 'Neutral'
    
    total_score += stoch_score
    
    # Sinyal yönü belirleme
    long_signals = sum(1 for signal in [ma_signal, macd_signal, adx_signal, bb_signal, stoch_signal] if signal == 'Long')
    short_signals = sum(1 for signal in [ma_signal, macd_signal, adx_signal, bb_signal, stoch_signal] if signal == 'Short')
    
    # Formasyon yönü
    formation_signal = 'Long' if formation_type == 'TOBO' else 'Short' if formation_type == 'OBO' else 'Neutral'
    
    # Genel sinyal yönü
    if formation_signal == 'Long':
        long_signals += 1
    elif formation_signal == 'Short':
        short_signals += 1
    
    # Çelişki analizi
    total_indicators = 6  # Formasyon + 5 indikatör
    long_percentage = (long_signals / total_indicators) * 100
    short_percentage = (short_signals / total_indicators) * 100
    
    # Final sinyal belirleme - Daha sıkı kriterler
    if long_percentage >= 75:
        final_signal = 'Long'
        confidence = 'Yüksek'
    elif short_percentage >= 75:
        final_signal = 'Short'
        confidence = 'Yüksek'
    elif long_percentage >= 65:
        final_signal = 'Long'
        confidence = 'Orta'
    elif short_percentage >= 65:
        final_signal = 'Short'
        confidence = 'Orta'
    else:
        final_signal = 'Bekleme'
        confidence = 'Düşük'
    
    # Çelişki durumu - Daha hassas
    if abs(long_percentage - short_percentage) < 15:
        conflict = 'Yüksek Çelişki'
    elif abs(long_percentage - short_percentage) < 30:
        conflict = 'Orta Çelişki'
    else:
        conflict = 'Düşük Çelişki'
    
    return {
        'total_score': total_score,
        'max_score': max_score,
        'long_percentage': long_percentage,
        'short_percentage': short_percentage,
        'final_signal': final_signal,
        'confidence': confidence,
        'conflict': conflict,
        'signals': signals,
        'formation_signal': formation_signal,
        'indicator_signals': {
            'ma': ma_signal,
            'macd': macd_signal,
            'adx': adx_signal,
            'bb': bb_signal,
            'stoch': stoch_signal
        }
    }


def calculate_three_tp_levels(entry_price, current_tp, current_sl, direction, fibo_levels, bb_data=None, formation_type=None):
    """
    3 farklı TP seviyesi hesaplar ve kâr yüzdesine göre küçükten büyüğe sıralar.
    - TP1: En düşük kâr (ana TP'den düşük olamaz)
    - TP2: Orta kâr
    - TP3: Maksimum kâr
    """
    tp_candidates = []
    
    # Ana TP'yi mutlaka ekle (en önemli)
    if direction == 'Long':
        if current_tp > entry_price:
            main_gain = (current_tp - entry_price) / entry_price * 100
            tp_candidates.append({'price': current_tp, 'level': 'Ana TP', 'gain': main_gain})
    else:  # Short
        if current_tp < entry_price:
            main_gain = (entry_price - current_tp) / entry_price * 100
            tp_candidates.append({'price': current_tp, 'level': 'Ana TP', 'gain': main_gain})
    
    if direction == 'Long':
        # TP adaylarını topla (sadece ana TP'den yüksek olanları)
        for level in ['0.382', '0.5', '0.618', '0.786']:
            if level in fibo_levels and fibo_levels[level] > entry_price and fibo_levels[level] > current_tp:
                gain = (fibo_levels[level] - entry_price) / entry_price * 100
                tp_candidates.append({'price': fibo_levels[level], 'level': level, 'gain': gain})
        
        # Formasyon hedefi (ana TP'den yüksek olmalı)
        if formation_type == 'TOBO' or formation_type == 'CUP_HANDLE':
            tp3_price = entry_price * 1.30
            if tp3_price > current_tp:
                tp_candidates.append({'price': tp3_price, 'level': 'Formasyon Hedefi', 'gain': (tp3_price - entry_price) / entry_price * 100})
        elif formation_type == 'FALLING_WEDGE':
            tp3_price = entry_price * 1.25
            if tp3_price > current_tp:
                tp_candidates.append({'price': tp3_price, 'level': 'Formasyon Hedefi', 'gain': (tp3_price - entry_price) / entry_price * 100})
        else:
            tp3_price = entry_price * 1.50
            if tp3_price > current_tp:
                tp_candidates.append({'price': tp3_price, 'level': 'Genel Hedef', 'gain': (tp3_price - entry_price) / entry_price * 100})
        
        # Bollinger üst bandı (ana TP'den yüksek olmalı)
        if bb_data and bb_data['upper_band'] > entry_price and bb_data['upper_band'] > current_tp:
            gain = (bb_data['upper_band'] - entry_price) / entry_price * 100
            tp_candidates.append({'price': bb_data['upper_band'], 'level': 'Bollinger Üst', 'gain': gain})
    
    else:  # Short
        # TP adaylarını topla (sadece ana TP'den düşük olanları)
        for level in ['0.618', '0.5', '0.382', '0.236']:
            if level in fibo_levels and fibo_levels[level] < entry_price and fibo_levels[level] < current_tp:
                gain = (entry_price - fibo_levels[level]) / entry_price * 100
                tp_candidates.append({'price': fibo_levels[level], 'level': level, 'gain': gain})
        
        if formation_type == 'OBO':
            tp3_price = entry_price * 0.70
            if tp3_price < current_tp:
                tp_candidates.append({'price': tp3_price, 'level': 'Formasyon Hedefi', 'gain': (entry_price - tp3_price) / entry_price * 100})
        else:
            tp3_price = entry_price * 0.50
            if tp3_price < current_tp:
                tp_candidates.append({'price': tp3_price, 'level': 'Genel Hedef', 'gain': (entry_price - tp3_price) / entry_price * 100})
        
        if bb_data and bb_data['lower_band'] < entry_price and bb_data['lower_band'] < current_tp:
            gain = (entry_price - bb_data['lower_band']) / entry_price * 100
            tp_candidates.append({'price': bb_data['lower_band'], 'level': 'Bollinger Alt', 'gain': gain})
    
    # Kâr yüzdesine göre sırala
    tp_candidates = sorted(tp_candidates, key=lambda x: x['gain'])
    
    # En iyi 3 TP'yi seç (ana TP mutlaka dahil olmalı)
    if len(tp_candidates) >= 3:
        tp1 = tp_candidates[0]  # En düşük kâr
        tp2 = tp_candidates[1]  # Orta kâr
        tp3 = tp_candidates[-1]  # En yüksek kâr
    elif len(tp_candidates) == 2:
        tp1 = tp_candidates[0]
        tp2 = tp_candidates[1]
        tp3 = tp_candidates[1]  # Aynı seviye
    elif len(tp_candidates) == 1:
        tp1 = tp_candidates[0]
        tp2 = tp_candidates[0]  # Aynı seviye
        tp3 = tp_candidates[0]  # Aynı seviye
    else:
        # Hiç TP bulunamadıysa ana TP'yi kullan
        if direction == 'Long':
            gain = (current_tp - entry_price) / entry_price * 100
        else:
            gain = (entry_price - current_tp) / entry_price * 100
        
        tp1 = {'price': current_tp, 'level': 'Ana TP', 'gain': gain}
        tp2 = {'price': current_tp, 'level': 'Ana TP', 'gain': gain}
        tp3 = {'price': current_tp, 'level': 'Ana TP', 'gain': gain}
    
    return {
        'tp1': tp1,
        'tp2': tp2,
        'tp3': tp3
    }


def optimize_tp_sl(entry_price, current_tp, current_sl, direction, fibo_levels, bb_data=None):
    """
    TP ve SL seviyelerini optimize eder - Gerçekçi R/R oranları (0.5-3.0 arası)
    """
    if direction == 'Long':
        # Mantık kontrolü: Long için entry > SL ve TP > entry olmalı
        if entry_price <= current_sl or current_tp <= entry_price:
            return entry_price, entry_price * 0.99, 0  # Geçersiz durum
        
        # Mevcut R/R hesapla
        current_reward = (current_tp - entry_price) / entry_price
        current_risk = (entry_price - current_sl) / entry_price
        current_rr = current_reward / current_risk if current_risk > 0 else 0
        
        # R/R < 0.5 ise optimize et, maksimum 3.0 olsun
        if current_rr < 0.5:
            # TP seçenekleri (Fibonacci seviyeleri)
            tp_options = []
            for level in ['0.236', '0.382', '0.5', '0.618']:
                if level in fibo_levels and fibo_levels[level] > entry_price:
                    tp_options.append((level, fibo_levels[level]))
            
            # SL seçenekleri (daha sıkı)
            sl_options = []
            for level in ['0.786', '0.618', '0.5']:
                if level in fibo_levels and fibo_levels[level] < entry_price:
                    sl_options.append((level, fibo_levels[level]))
            
            # Bollinger alt bandı da SL seçeneği olarak ekle
            if bb_data and bb_data['lower_band'] < entry_price:
                sl_options.append(('BB Lower', bb_data['lower_band']))
            
            best_tp = current_tp
            best_sl = current_sl
            best_rr = current_rr
            
            # En iyi kombinasyonu bul
            for tp_level, tp_price in tp_options:
                for sl_level, sl_price in sl_options:
                    # Minimum SL mesafesi kontrolü (%2'den az olmasın)
                    sl_distance = (entry_price - sl_price) / entry_price
                    if sl_distance < 0.02:  # %2'den az mesafe güvenli değil
                        continue
                    
                    reward = (tp_price - entry_price) / entry_price
                    risk = (entry_price - sl_price) / entry_price
                    rr = reward / risk if risk > 0 else 0
                    
                    # R/R 0.5-3.0 arası olsun
                    if 0.5 <= rr <= 3.0 and rr > best_rr:
                        best_tp = tp_price
                        best_sl = sl_price
                        best_rr = rr
            
            return best_tp, best_sl, best_rr
        else:
            # Mevcut R/R'yi kontrol et, 3.0'dan büyükse sınırla
            if current_rr > 3.0:
                # TP'yi düşür
                new_tp = entry_price + (entry_price - current_sl) * 3.0
                return new_tp, current_sl, 3.0
            return current_tp, current_sl, current_rr
    
    else:  # Short
        # Mantık kontrolü: Short için entry < SL ve TP < entry olmalı
        if entry_price >= current_sl or current_tp >= entry_price:
            return entry_price, entry_price * 1.01, 0  # Geçersiz durum
        
        # Mevcut R/R hesapla
        current_reward = (entry_price - current_tp) / entry_price
        current_risk = (current_sl - entry_price) / entry_price
        current_rr = current_reward / current_risk if current_risk > 0 else 0
        
        # R/R < 0.5 ise optimize et, maksimum 3.0 olsun
        if current_rr < 0.5:
            # TP seçenekleri (Fibonacci seviyeleri)
            tp_options = []
            for level in ['0.618', '0.5', '0.382', '0.236']:
                if level in fibo_levels and fibo_levels[level] < entry_price:
                    tp_options.append((level, fibo_levels[level]))
            
            # SL seçenekleri (daha sıkı)
            sl_options = []
            for level in ['0.236', '0.382', '0.5']:
                if level in fibo_levels and fibo_levels[level] > entry_price:
                    sl_options.append((level, fibo_levels[level]))
            
            # Bollinger üst bandı da SL seçeneği olarak ekle
            if bb_data and bb_data['upper_band'] > entry_price:
                sl_options.append(('BB Upper', bb_data['upper_band']))
            
            best_tp = current_tp
            best_sl = current_sl
            best_rr = current_rr
            
            # En iyi kombinasyonu bul
            for tp_level, tp_price in tp_options:
                for sl_level, sl_price in sl_options:
                    # Minimum SL mesafesi kontrolü (%2'den az olmasın)
                    sl_distance = (sl_price - entry_price) / entry_price
                    if sl_distance < 0.02:  # %2'den az mesafe güvenli değil
                        continue
                    
                    reward = (entry_price - tp_price) / entry_price
                    risk = (sl_price - entry_price) / entry_price
                    rr = reward / risk if risk > 0 else 0
                    
                    # R/R 0.5-3.0 arası olsun
                    if 0.5 <= rr <= 3.0 and rr > best_rr:
                        best_tp = tp_price
                        best_sl = sl_price
                        best_rr = rr
            
            return best_tp, best_sl, best_rr
        else:
            # Mevcut R/R'yi kontrol et, 3.0'dan büyükse sınırla
            if current_rr > 3.0:
                # TP'yi yükselt
                new_tp = entry_price - (current_sl - entry_price) * 3.0
                return new_tp, current_sl, 3.0
            return current_tp, current_sl, current_rr


def analyze_trading_scenarios(df, formation_type, formation_data, current_price, fibo_levels, bb_data, signal_score):
    """
    Kapsamlı trading senaryoları analizi
    """
    scenarios = []
    action_plan = {}
    
    # Senaryo 1: Formasyon kırılımı
    if formation_type == 'OBO':
        neckline = formation_data['neckline']
        if current_price > neckline:
            scenarios.append({
                'type': 'OBO Short Fırsatı',
                'condition': f'Fiyat {format_price(neckline)} altına düşerse',
                'entry': current_price,
                'tp': fibo_levels.get('0.618', current_price * 0.95),
                'sl': fibo_levels.get('0.382', current_price * 1.02),
                'probability': 'Orta',
                'risk': 'Yüksek (Trend boğa)',
                'volume_requirement': '1.5x+ hacim artışı gerekli'
            })
        else:
            scenarios.append({
                'type': 'OBO Short Aktif',
                'condition': 'Formasyon tamamlandı',
                'entry': current_price,
                'tp': fibo_levels.get('0.618', current_price * 0.95),
                'sl': fibo_levels.get('0.382', current_price * 1.02),
                'probability': 'Yüksek',
                'risk': 'Orta',
                'volume_requirement': 'Mevcut hacim yeterli'
            })
    
    elif formation_type == 'TOBO':
        neckline = formation_data['neckline']
        if current_price < neckline:
            scenarios.append({
                'type': 'TOBO Long Fırsatı',
                'condition': f'Fiyat {format_price(neckline)} üstüne çıkarsa',
                'entry': current_price,
                'tp': fibo_levels.get('0.382', current_price * 1.05),
                'sl': fibo_levels.get('0.618', current_price * 0.98),
                'probability': 'Orta',
                'risk': 'Yüksek (Trend ayı)',
                'volume_requirement': '1.5x+ hacim artışı gerekli'
            })
        else:
            scenarios.append({
                'type': 'TOBO Long Aktif',
                'condition': 'Formasyon tamamlandı',
                'entry': current_price,
                'tp': fibo_levels.get('0.382', current_price * 1.05),
                'sl': fibo_levels.get('0.618', current_price * 0.98),
                'probability': 'Yüksek',
                'risk': 'Orta',
                'volume_requirement': 'Mevcut hacim yeterli'
            })
    
    # Senaryo 2: Bollinger Bands kırılımı
    if bb_data:
        if bb_data['signal'] == 'Overbought':
            scenarios.append({
                'type': 'Bollinger Short',
                'condition': f'Fiyat {format_price(bb_data["upper_band"])} altına düşerse',
                'entry': current_price,
                'tp': bb_data['middle_band'],
                'sl': bb_data['upper_band'] * 1.01,
                'probability': 'Düşük',
                'risk': 'Orta',
                'volume_requirement': 'Normal hacim'
            })
        elif bb_data['signal'] == 'Oversold':
            scenarios.append({
                'type': 'Bollinger Long',
                'condition': f'Fiyat {format_price(bb_data["lower_band"])} üstüne çıkarsa',
                'entry': current_price,
                'tp': bb_data['middle_band'],
                'sl': bb_data['lower_band'] * 0.99,
                'probability': 'Düşük',
                'risk': 'Orta',
                'volume_requirement': 'Normal hacim'
            })
    
    # Senaryo 3: Fibonacci seviyeleri
    fibo_scenarios = []
    for level, price in fibo_levels.items():
        if abs(current_price - price) / current_price < 0.02:  # %2 yakınlık
            if current_price > price:
                fibo_scenarios.append({
                    'type': f'Fibonacci {level} Direnç',
                    'condition': f'Fiyat {format_price(price)} altına düşerse',
                    'entry': current_price,
                    'tp': price * 0.98,
                    'sl': price * 1.02,
                    'probability': 'Orta',
                    'risk': 'Düşük',
                    'volume_requirement': 'Normal hacim'
                })
            else:
                fibo_scenarios.append({
                    'type': f'Fibonacci {level} Destek',
                    'condition': f'Fiyat {format_price(price)} üstüne çıkarsa',
                    'entry': current_price,
                    'tp': price * 1.02,
                    'sl': price * 0.98,
                    'probability': 'Orta',
                    'risk': 'Düşük',
                    'volume_requirement': 'Normal hacim'
                })
    
    scenarios.extend(fibo_scenarios)
    
    # Aksiyon planı belirleme
    if signal_score['final_signal'] == 'Bekleme':
        action_plan = {
            'immediate_action': 'BEKLE',
            'reason': f'Çelişkili sinyaller: {signal_score["conflict"]}',
            'watch_levels': [
                f'Boyun çizgisi: {format_price(formation_data["neckline"]) if formation_data else "N/A"}',
                f'Bollinger üst: {format_price(bb_data["upper_band"]) if bb_data else "N/A"}',
                f'Bollinger alt: {format_price(bb_data["lower_band"]) if bb_data else "N/A"}'
            ],
            'entry_criteria': 'Daha net sinyal bekleyin',
            'risk_level': 'Yüksek (çelişkili sinyaller)'
        }
    elif signal_score['final_signal'] == 'Long':
        action_plan = {
            'immediate_action': 'LONG GİR',
            'reason': f'Güçlü long sinyali: %{signal_score["long_percentage"]:.1f}',
            'entry_price': current_price,
            'tp_price': scenarios[0]['tp'] if scenarios else current_price * 1.05,
            'sl_price': scenarios[0]['sl'] if scenarios else current_price * 0.98,
            'watch_levels': [
                f'TP: {format_price(scenarios[0]["tp"]) if scenarios else "N/A"}',
                f'SL: {format_price(scenarios[0]["sl"]) if scenarios else "N/A"}'
            ],
            'entry_criteria': 'Anlık fiyattan giriş',
            'risk_level': signal_score['confidence']
        }
    else:  # Short
        action_plan = {
            'immediate_action': 'SHORT GİR',
            'reason': f'Güçlü short sinyali: %{signal_score["short_percentage"]:.1f}',
            'entry_price': current_price,
            'tp_price': scenarios[0]['tp'] if scenarios else current_price * 0.95,
            'sl_price': scenarios[0]['sl'] if scenarios else current_price * 1.02,
            'watch_levels': [
                f'TP: {format_price(scenarios[0]["tp"]) if scenarios else "N/A"}',
                f'SL: {format_price(scenarios[0]["sl"]) if scenarios else "N/A"}'
            ],
            'entry_criteria': 'Anlık fiyattan giriş',
            'risk_level': signal_score['confidence']
        }
    
    return scenarios, action_plan


def main():
    # Lisans yöneticisini başlat
    license_manager = LicenseManager()
    
    print("\n" + "="*60)
    print("🎯 TRADING BOT - LİSANS KONTROLÜ")
    print("="*60)
    
    # Lisans durumunu kontrol et
    license_status, license_result = license_manager.check_license_status()
    
    if not license_status:
        print("❌ Lisans bulunamadı veya süresi dolmuş!")
        print(f"💬 İletişim: {license_manager.contact_telegram}")
        print()
        
        # Fiyatlandırma bilgilerini göster
        license_manager.show_pricing_info()
        
        # Lisans anahtarı iste
        while True:
            license_key = input("\n🔑 Lisans anahtarınızı girin (çıkmak için 'exit'): ").strip()
            
            if license_key.lower() == 'exit':
                print("👋 Çıkılıyor...")
                return
            
            if not license_key:
                print("❌ Lisans anahtarı boş olamaz!")
                continue
            
            # Lisans anahtarını doğrula
            is_valid, result = license_manager.validate_license(license_key)
            
            if is_valid:
                print("✅ Lisans doğrulandı!")
                license_info = result
                print(f"📦 Paket: {license_info['type'].upper()}")
                print(f"💰 Fiyat: ${license_info['price']}")
                print(f"📅 Aktifleştirme: {license_info['activated_date'][:10]}")
                
                if license_info['expiry_date']:
                    print(f"⏰ Bitiş: {license_info['expiry_date'][:10]}")
                else:
                    print("⏰ Bitiş: Sınırsız")
                
                print("🚀 Bot başlatılıyor...")
                break
            else:
                print(f"❌ {result}")
                print("💡 Doğru lisans anahtarını girdiğinizden emin olun.")
                print(f"💬 İletişim: {license_manager.contact_telegram}")
    else:
        # Mevcut lisans bilgilerini göster
        license_info = license_result
        print("✅ Lisans aktif!")
        print(f"📦 Paket: {license_info['type'].upper()}")
        print(f"💰 Fiyat: ${license_info['price']}")
        
        remaining_days = license_manager.get_remaining_days()
        if remaining_days == -1:
            print("⏰ Kalan süre: Sınırsız")
        else:
            print(f"⏰ Kalan süre: {remaining_days} gün")
        
        print("🚀 Bot başlatılıyor...")
    
    print("="*60)
    
    interval = '4h'
    print("\n🤖 Otomatik Tarama Botu Başlatılıyor...")
    print("📊 Bot her fırsat için en uygun risk seviyesini otomatik önerecek")
    print("💰 Risk seviyesi: Kaldıraç, pozisyon büyüklüğü ve potansiyel kazanç")
    print("🎯 R/R Filtresi: 0.5:1'den yüksek risk/ödül oranına sahip sinyaller gösterilecek")
    print("📱 Telegram Bildirimleri: Aktif")
    print("⏱️ Tarama Süresi: 80-90 saniye (tüm coinler analiz edilecek)")
    print("\nESC'ye basarak çıkabilirsiniz. Tarama her 3 saatte bir otomatik tekrar edecek.")
    
    # Bot başlangıç bildirimi
    try:
        # Lisans bilgilerini al
        license_info = license_manager.get_license_info()
        send_startup_notification(license_info)
    except Exception as e:
        print(f"❌ Başlangıç bildirimi gönderilemedi: {e}")
    
    while True:
        scan_start_time = time.time()
        symbols = get_usdt_symbols()
        print(f'\n🔍 Toplam {len(symbols)} USDT paritesine sahip coin taranacak...')
        firsatlar = []
        
        def analyze_symbol(symbol, interval='4h'):
            try:
                # Her coin için detaylı analiz yap
                current_price = get_current_price(symbol)
                if not current_price:
                    return None
                    
                df = fetch_ohlcv(symbol, interval)
                if df is None or df.empty:
                    return None
                
                # Minimum veri kontrolü
                if len(df) < 100:
                    return None
                
                # MA hesaplamaları (MA200 çıkarıldı)
                df['MA7'] = df['close'].rolling(window=7).mean()
                df['MA25'] = df['close'].rolling(window=25).mean()
                df['MA50'] = df['close'].rolling(window=50).mean()
                df['MA99'] = df['close'].rolling(window=99).mean()
                
                ma_trend = None
                if df['MA7'].iloc[-1] > df['MA25'].iloc[-1] > df['MA50'].iloc[-1] > df['MA99'].iloc[-1]:
                    ma_trend = 'Güçlü Yükseliş (Tüm kısa MA\'lar uzun MA\'ların üstünde)'
                elif df['MA7'].iloc[-1] < df['MA25'].iloc[-1] < df['MA50'].iloc[-1] < df['MA99'].iloc[-1]:
                    ma_trend = 'Güçlü Düşüş (Tüm kısa MA\'lar uzun MA\'ların altında)'
                else:
                    ma_trend = 'Kararsız veya yatay trend (MA\'lar karışık)'
                
                fibo_levels, fibo_high, fibo_low = calculate_fibonacci_levels(df)
                
                # Tüm gelişmiş formasyonları analiz et
                formation_signal = analyze_all_formations_advanced(df)
                
                # Yeni gelişmiş formasyonları göster
                if formation_signal:
                    formation_type = formation_signal['type']
                    formation_score = formation_signal['score']
                    formation_confidence = formation_signal['confidence']
                    
                    print(f"   🎯 GELİŞMİŞ FORMASYON: {formation_type}")
                    print(f"   🎯 Skor: {formation_score:.1f} | Güven: {formation_confidence}")
                    
                    # Formasyon tipine göre kısa bilgi
                    if 'DOUBLE_BOTTOM' in formation_type:
                        print(f"   📊 Double Bottom - Kırılım: {'✅' if formation_signal.get('breakout_confirmed', False) else '❌'}")
                    elif 'DOUBLE_TOP' in formation_type:
                        print(f"   📊 Double Top - Kırılım: {'✅' if formation_signal.get('breakout_confirmed', False) else '❌'}")
                    elif 'BULLISH_FLAG' in formation_type or 'BEARISH_FLAG' in formation_type:
                        print(f"   📊 Flag - Kırılım: {'✅' if formation_signal.get('breakout_confirmed', False) else '❌'}")
                    elif 'ASCENDING_TRIANGLE' in formation_type or 'DESCENDING_TRIANGLE' in formation_type:
                        print(f"   📊 Triangle - Kırılım: {'✅' if formation_signal.get('breakout_confirmed', False) else '❌'}")
                    elif 'SYMMETRICAL_TRIANGLE' in formation_type:
                        print(f"   📊 Symmetrical Triangle - Kırılım: {'✅' if formation_signal.get('breakout_confirmed', False) else '❌'}")
                    elif 'RISING_CHANNEL' in formation_type:
                        print(f"   📊 Rising Channel - Kırılım: {'✅' if formation_signal.get('breakout_confirmed', False) else '❌'}")
                    elif 'DIVERGENCE' in formation_type:
                        print(f"   📊 Divergence - Güç: {formation_signal.get('strength', 'N/A')}")

                # Flag & Pennant (Bayrak & Flama) formasyonu tespiti
                flag_signal = detect_bullish_bearish_flag_advanced(df)
                if flag_signal:
                    flag_type = flag_signal['type']
                    flag_score = flag_signal['score']
                    flag_confidence = flag_signal['confidence']
                    print(f"   🚩 FLAG FORMASYONU: {flag_type} | Skor: {flag_score} | Güven: {flag_confidence}")
                    # 3 TP seviyesi hesapla
                    try:
                        tp_levels = calculate_three_tp_levels(
                            current_price, flag_signal['tp'], flag_signal['sl'],
                            'Long' if flag_type == 'BULLISH_FLAG' else 'Short',
                            fibo_levels if 'fibo_levels' in locals() else {},
                            bb_data if 'bb_data' in locals() else None,
                            flag_type
                        )
                    except Exception:
                        tp_levels = None
                    # Fırsatlar listesine ekle
                    firsat = {
                        'symbol': symbol,
                        'yön': 'Long' if flag_type == 'BULLISH_FLAG' else 'Short',
                        'formasyon': flag_type,
                        'price': format_price(current_price),
                        'tp': format_price(flag_signal['tp']),
                        'sl': format_price(flag_signal['sl']),
                        'tpfark': abs(flag_signal['tp']-current_price)/current_price,
                        'risk_analysis': calculate_optimal_risk(symbol, current_price, flag_signal['tp'], flag_signal['sl'], 'Long' if flag_type == 'BULLISH_FLAG' else 'Short'),
                        'signal_strength': flag_score,
                        'rr_ratio': abs(flag_signal['tp']-current_price)/abs(current_price-flag_signal['sl']) if abs(current_price-flag_signal['sl']) > 0 else 0,
                        'tp_levels': tp_levels
                    }
                    firsatlar.append(firsat)
                
                # Eski formasyonları da ayrı ayrı kontrol et (geriye uyumluluk için)
                all_tobo = find_all_tobo(df)
                all_obo = find_all_obo(df)
                falling_wedge = detect_falling_wedge(df)
                tobo = all_tobo[-1] if all_tobo else None
                obo = all_obo[-1] if all_obo else None
                
                # En güçlü formasyonu belirle (bot.py ile aynı mantık)
                dominant_formation = None
                formation_scores = {}
                
                if tobo:
                    tobo_strength = abs(tobo['bas'] - tobo['neckline']) / tobo['neckline']
                    formation_scores['TOBO'] = tobo_strength * 100
                
                if obo:
                    obo_strength = abs(obo['bas'] - obo['neckline']) / obo['neckline']
                    formation_scores['OBO'] = obo_strength * 100
                
                if falling_wedge:
                    formation_scores['FALLING_WEDGE'] = falling_wedge['score']
                
                # En yüksek skora sahip formasyonu seç
                if formation_scores:
                    dominant_formation = max(formation_scores, key=formation_scores.get)
                else:
                    return None
                
                # Sadece dominant formasyonu analiz et (bot.py ile aynı mantık)
                if dominant_formation == 'TOBO' and current_price:
                    neckline = tobo['neckline']
                    tp = fibo_levels['0.382']
                    # SL'yi daha güvenli seviyede seç - Long için SL < Giriş olmalı
                    # Minimum %3 mesafe olmalı
                    min_sl_distance = current_price * 0.97  # %3 altı
                    
                    # Önce en düşük Fibonacci seviyesini dene
                    if '0.786' in fibo_levels and fibo_levels['0.786'] < min_sl_distance:
                        sl = fibo_levels['0.786']
                    elif '0.618' in fibo_levels and fibo_levels['0.618'] < min_sl_distance:
                        sl = fibo_levels['0.618']
                    elif '0.5' in fibo_levels and fibo_levels['0.5'] < min_sl_distance:
                        sl = fibo_levels['0.5']
                    else:
                        # Hiçbir Fibonacci seviyesi yeterince aşağıda değilse, %5 altını kullan
                        sl = current_price * 0.95
                    
                    # Her durumda anlık fiyattan giriş (bot.py ile aynı mantık)
                    entry = current_price
                    
                    if tp > entry > sl and (tp - entry) / entry >= 0.01 and sl < entry:
                        # Hızlı indikatör analizi (bot.py ile aynı)
                        macd_data = calculate_macd(df)
                        bb_data = calculate_bollinger_bands(df)
                        stoch_data = calculate_stochastic(df)
                        adx_data = calculate_adx(df)
                        
                        # Basit sinyal kontrolü (hızlı)
                        bullish_signals = 0
                        bearish_signals = 0
                        
                        # MA trend kontrolü
                        if 'Yükseliş' in ma_trend:
                            bullish_signals += 1
                        elif 'Düşüş' in ma_trend:
                            bearish_signals += 1
                        
                        # MACD kontrolü
                        if macd_data and macd_data['trend'] == 'Bullish':
                            bullish_signals += 1
                        elif macd_data and macd_data['trend'] == 'Bearish':
                            bearish_signals += 1
                        
                        # ADX kontrolü
                        if adx_data and adx_data['trend_direction'] == 'Bullish':
                            bullish_signals += 1
                        elif adx_data and adx_data['trend_direction'] == 'Bearish':
                            bearish_signals += 1
                        
                        # Bollinger kontrolü
                        if bb_data and bb_data['signal'] == 'Oversold':
                            bullish_signals += 1
                        elif bb_data and bb_data['signal'] == 'Overbought':
                            bearish_signals += 1
                        
                        # Stochastic kontrolü
                        if stoch_data and stoch_data['signal'] == 'Oversold':
                            bullish_signals += 1
                        elif stoch_data and stoch_data['signal'] == 'Overbought':
                            bearish_signals += 1
                        
                        # Formasyon kontrolü (TOBO = Long)
                        bullish_signals += 1
                        
                        # Hızlı sinyal değerlendirmesi (bot.py ile aynı)
                        total_signals = 6  # Formasyon + MA + MACD + ADX + Bollinger + Stochastic
                        long_percentage = (bullish_signals / total_signals) * 100
                        
                        # Farklı güç seviyelerinde sinyalleri kabul et
                        if long_percentage >= 40:  # %40+ long sinyali
                            # 3 TP seviyesi hesaplama
                            tp_levels = calculate_three_tp_levels(entry, tp, sl, 'Long', fibo_levels, bb_data, 'TOBO')
                            
                            # TP ve SL optimizasyonu
                            optimized_tp, optimized_sl, optimized_rr = optimize_tp_sl(entry, tp, sl, 'Long', fibo_levels, bb_data)
                            
                            # R/R oranı kontrolü - Daha esnek kriterler
                            if optimized_rr >= 0.5:  # 0.5:1'den yüksek olanları kabul et
                                risk_analysis = calculate_optimal_risk(symbol, entry, optimized_tp, optimized_sl, 'Long')
                                
                                firsat = {
                                    'symbol': symbol,
                                    'yön': 'Long',
                                    'formasyon': 'TOBO',
                                    'price': format_price(current_price),
                                    'tp': format_price(optimized_tp),
                                    'sl': format_price(optimized_sl),
                                    'tpfark': (optimized_tp-entry)/entry,
                                    'risk_analysis': risk_analysis,
                                    'signal_strength': long_percentage,
                                    'rr_ratio': optimized_rr,
                                    'tp_levels': tp_levels
                                }
                                return firsat
                
                elif dominant_formation == 'OBO' and current_price:
                    neckline = obo['neckline']
                    tp = fibo_levels['0.618']
                    # SL'yi daha güvenli seviyede seç - Short için SL > Giriş olmalı
                    # Minimum %3 mesafe olmalı
                    min_sl_distance = current_price * 1.03  # %3 üstü
                    
                    # Önce en yüksek Fibonacci seviyesini dene
                    if '0.236' in fibo_levels and fibo_levels['0.236'] > min_sl_distance:
                        sl = fibo_levels['0.236']
                    elif '0.382' in fibo_levels and fibo_levels['0.382'] > min_sl_distance:
                        sl = fibo_levels['0.382']
                    elif '0.5' in fibo_levels and fibo_levels['0.5'] > min_sl_distance:
                        sl = fibo_levels['0.5']
                    else:
                        # Hiçbir Fibonacci seviyesi yeterince yukarıda değilse, %5 üstünü kullan
                        sl = current_price * 1.05
                    
                    # Her durumda anlık fiyattan giriş (bot.py ile aynı mantık)
                    entry = current_price
                    
                    if tp < entry < sl and (entry - tp) / entry >= 0.01 and sl > entry:
                        # Hızlı indikatör analizi (bot.py ile aynı)
                        macd_data = calculate_macd(df)
                        bb_data = calculate_bollinger_bands(df)
                        stoch_data = calculate_stochastic(df)
                        adx_data = calculate_adx(df)
                        
                        # Basit sinyal kontrolü (hızlı)
                        bullish_signals = 0
                        bearish_signals = 0
                        
                        # MA trend kontrolü
                        if 'Yükseliş' in ma_trend:
                            bullish_signals += 1
                        elif 'Düşüş' in ma_trend:
                            bearish_signals += 1
                        
                        # MACD kontrolü
                        if macd_data and macd_data['trend'] == 'Bullish':
                            bullish_signals += 1
                        elif macd_data and macd_data['trend'] == 'Bearish':
                            bearish_signals += 1
                        
                        # ADX kontrolü
                        if adx_data and adx_data['trend_direction'] == 'Bullish':
                            bullish_signals += 1
                        elif adx_data and adx_data['trend_direction'] == 'Bearish':
                            bearish_signals += 1
                        
                        # Bollinger kontrolü
                        if bb_data and bb_data['signal'] == 'Oversold':
                            bullish_signals += 1
                        elif bb_data and bb_data['signal'] == 'Overbought':
                            bearish_signals += 1
                        
                        # Stochastic kontrolü
                        if stoch_data and stoch_data['signal'] == 'Oversold':
                            bullish_signals += 1
                        elif stoch_data and stoch_data['signal'] == 'Overbought':
                            bearish_signals += 1
                        
                        # Formasyon kontrolü (OBO = Short)
                        bearish_signals += 1
                        
                        # Hızlı sinyal değerlendirmesi (bot.py ile aynı)
                        total_signals = 6  # Formasyon + MA + MACD + ADX + Bollinger + Stochastic
                        short_percentage = (bearish_signals / total_signals) * 100
                        
                        # Farklı güç seviyelerinde sinyalleri kabul et
                        if short_percentage >= 40:  # %40+ short sinyali
                            # TP ve SL optimizasyonu
                            optimized_tp, optimized_sl, optimized_rr = optimize_tp_sl(entry, tp, sl, 'Short', fibo_levels, bb_data)
                            
                            # R/R oranı kontrolü - Daha esnek kriterler
                            if optimized_rr >= 0.5:  # 0.5:1'den yüksek olanları kabul et
                                risk_analysis = calculate_optimal_risk(symbol, entry, optimized_tp, optimized_sl, 'Short')
                                
                                firsat = {
                                    'symbol': symbol,
                                    'yön': 'Short',
                                    'formasyon': 'OBO',
                                    'price': format_price(current_price),
                                    'tp': format_price(optimized_tp),
                                    'sl': format_price(optimized_sl),
                                    'tpfark': (entry-optimized_tp)/entry,
                                    'risk_analysis': risk_analysis,
                                    'signal_strength': short_percentage,
                                    'rr_ratio': optimized_rr
                                }
                                return firsat
                
                elif dominant_formation == 'FALLING_WEDGE' and current_price and falling_wedge:
                    # Falling Wedge için risk analizi
                    entry = falling_wedge['entry_price']
                    tp = falling_wedge['tp']
                    sl = falling_wedge['sl']
                    
                    if tp > entry > sl and (tp - entry) / entry >= 0.01:
                        # Hızlı indikatör analizi (bot.py ile aynı)
                        macd_data = calculate_macd(df)
                        bb_data = calculate_bollinger_bands(df)
                        stoch_data = calculate_stochastic(df)
                        adx_data = calculate_adx(df)
                        
                        # Basit sinyal kontrolü (hızlı)
                        bullish_signals = 0
                        bearish_signals = 0
                        
                        # MA trend kontrolü
                        if 'Yükseliş' in ma_trend:
                            bullish_signals += 1
                        elif 'Düşüş' in ma_trend:
                            bearish_signals += 1
                        
                        # MACD kontrolü
                        if macd_data and macd_data['trend'] == 'Bullish':
                            bullish_signals += 1
                        elif macd_data and macd_data['trend'] == 'Bearish':
                            bearish_signals += 1
                        
                        # ADX kontrolü
                        if adx_data and adx_data['trend_direction'] == 'Bullish':
                            bullish_signals += 1
                        elif adx_data and adx_data['trend_direction'] == 'Bearish':
                            bearish_signals += 1
                        
                        # Bollinger kontrolü
                        if bb_data and bb_data['signal'] == 'Oversold':
                            bullish_signals += 1
                        elif bb_data and bb_data['signal'] == 'Overbought':
                            bearish_signals += 1
                        
                        # Stochastic kontrolü
                        if stoch_data and stoch_data['signal'] == 'Oversold':
                            bullish_signals += 1
                        elif stoch_data and stoch_data['signal'] == 'Overbought':
                            bearish_signals += 1
                        
                        # Formasyon kontrolü (Falling Wedge = Long)
                        bullish_signals += 1
                        
                        # Hızlı sinyal değerlendirmesi (bot.py ile aynı)
                        total_signals = 6  # Formasyon + MA + MACD + ADX + Bollinger + Stochastic
                        long_percentage = (bullish_signals / total_signals) * 100
                        
                        # Farklı güç seviyelerinde sinyalleri kabul et
                        if long_percentage >= 40:  # %40+ long sinyali
                            # TP ve SL optimizasyonu
                            optimized_tp, optimized_sl, optimized_rr = optimize_tp_sl(entry, tp, sl, 'Long', fibo_levels, bb_data)
                            
                            # R/R oranı kontrolü - Daha esnek kriterler
                            if optimized_rr >= 0.5:  # 0.5:1'den yüksek olanları kabul et
                                risk_analysis = calculate_optimal_risk(symbol, entry, optimized_tp, optimized_sl, 'Long')
                                
                                firsat = {
                                    'symbol': symbol,
                                    'yön': 'Long',
                                    'formasyon': 'FALLING_WEDGE',
                                    'price': format_price(current_price),
                                    'tp': format_price(optimized_tp),
                                    'sl': format_price(optimized_sl),
                                    'tpfark': (optimized_tp-entry)/entry,
                                    'risk_analysis': risk_analysis,
                                    'signal_strength': long_percentage,
                                    'rr_ratio': optimized_rr
                                }
                                return firsat
                
                # Cup and Handle formasyonu tespiti
                cup_handle = detect_cup_and_handle(df)
                
                # Falling Wedge formasyonu tespiti
                falling_wedge = detect_falling_wedge(df)
                
                # Yeni formasyonları tespit et ve analiz et
                rectangle = find_rectangle(df)
                ascending_triangle = find_ascending_triangle(df)
                descending_triangle = find_descending_triangle(df)
                symmetrical_triangle = find_symmetrical_triangle(df)
                broadening_formation = find_broadening_formation(df)
                
                # Yeni formasyonları da fırsat olarak değerlendir
                if rectangle and current_price:
                    entry = current_price
                    if rectangle['breakout_up']:
                        tp = entry * 1.05  # %5 yukarı
                        sl = entry * 0.98  # %2 aşağı
                        if (tp - entry) / entry >= 0.01:
                            risk_analysis = calculate_optimal_risk(symbol, entry, tp, sl, 'Long')
                            firsat = {
                                'symbol': symbol,
                                'yön': 'Long',
                                'formasyon': 'Rectangle',
                                'price': format_price(current_price),
                                'tp': format_price(tp),
                                'sl': format_price(sl),
                                'tpfark': (tp-entry)/entry,
                                'risk_analysis': risk_analysis,
                                'signal_strength': 60,
                                'rr_ratio': (tp-entry)/(entry-sl) if entry > sl else 0
                            }
                            return firsat
                    elif rectangle['breakout_down']:
                        tp = entry * 0.95  # %5 aşağı
                        sl = entry * 1.02  # %2 yukarı
                        if (entry - tp) / entry >= 0.01:
                            risk_analysis = calculate_optimal_risk(symbol, entry, tp, sl, 'Short')
                            firsat = {
                                'symbol': symbol,
                                'yön': 'Short',
                                'formasyon': 'Rectangle',
                                'price': format_price(current_price),
                                'tp': format_price(tp),
                                'sl': format_price(sl),
                                'tpfark': (entry-tp)/entry,
                                'risk_analysis': risk_analysis,
                                'signal_strength': 60,
                                'rr_ratio': (entry-tp)/(sl-entry) if sl > entry else 0
                            }
                            return firsat
                
                # --- YENİ İNDİKATÖR ANALİZLERİ (4H ve 1D) ---
                ind_results = {}
                for tf in ['4h', '1d']:
                    df_tf = fetch_ohlcv(symbol, tf)
                    if df_tf is not None and not df_tf.empty:
                        ind_results[tf] = {
                            'ichimoku': calculate_ichimoku(df_tf),
                            'supertrend': calculate_supertrend(df_tf),
                            'vwap': calculate_vwap(df_tf),
                            'obv': calculate_obv(df_tf),
                            'heikin_ashi': calculate_heikin_ashi(df_tf)
                        }
                # Konsol çıktısı örneği
                for tf in ind_results:
                    print(f"\n[{symbol} - {tf.upper()}] İndikatörler:")
                    ichi = ind_results[tf]['ichimoku']
                    if ichi:
                        print(f"  Ichimoku: {ichi['signal']} | Tenkan-Kijun: {ichi['tenkan_kijun_cross']} | Bulut: {ichi['cloud_bottom']:.2f}-{ichi['cloud_top']:.2f}")
                    st = ind_results[tf]['supertrend']
                    if st:
                        print(f"  Supertrend: {st['signal']} | Band: {st['lowerband']:.2f}-{st['upperband']:.2f}")
                    vwap = ind_results[tf]['vwap']
                    if vwap:
                        print(f"  VWAP: {vwap['signal']} | VWAP: {vwap['vwap']:.2f} | Fiyat: {vwap['price']:.2f}")
                    obv = ind_results[tf]['obv']
                    if obv:
                        print(f"  OBV: {obv['obv_trend']} | Fiyat trendi: {obv['price_trend']} | Diverjans: {obv['divergence']}")
                    ha = ind_results[tf]['heikin_ashi']
                    if ha:
                        print(f"  Heikin Ashi trend: {ha['trend']} | HA Close: {ha['ha_close']:.2f}")
                
                return None
            except Exception as e:
                return None
        
        # Tüm coinleri gerçekten analiz et - 80-90 saniye sürecek
        print(f"🔍 {len(symbols)} coin analiz ediliyor... (80-90 saniye sürecek)")
        
        # Thread sayısını azalt - daha detaylı analiz için
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(analyze_symbol, symbol, interval) for symbol in symbols]
            
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                completed += 1
                
                # İlerleme göster
                if completed % 20 == 0:
                    progress = (completed / len(symbols)) * 100
                    print(f"📊 İlerleme: %{progress:.1f} ({completed}/{len(symbols)})")
                
                if result:
                    firsatlar.append(result)
                    print(f"✅ Fırsat bulundu: {result['symbol']} - {result['yön']} ({result['formasyon']})")
        
        # En iyi 10 fırsatı sırala ve yazdır
        all_firsatlar = sorted(firsatlar, key=lambda x: x['tpfark'], reverse=True)[:10]
        
        # Tarama süresini hesapla
        scan_time = time.time() - scan_start_time
        
        # Tarama özeti
        print(f"\n📊 TARAMA ÖZETİ")
        print(f"="*60)
        print(f"🔍 Taranan Coin: {len(symbols)}+")
        print(f"🎯 Bulunan Fırsat: {len(all_firsatlar)}")
        print(f"⏱️ Tarama Süresi: {scan_time:.1f} saniye")
        
        if all_firsatlar:
            print(f"\n🎯 EN İYİ {len(all_firsatlar)} FIRSAT")
            print(f"="*80)
            
            # Telegram'da fırsat bildirimleri gönder
            for i, f in enumerate(all_firsatlar, 1):
                try:
                    send_opportunity_notification(f, i)
                except Exception as e:
                    print(f"❌ Fırsat bildirimi gönderilemedi: {e}")
            
            # Telegram'da tarama özeti gönder (sadece bir kez)
            try:
                send_scan_summary(len(symbols), len(all_firsatlar), scan_time)
            except Exception as e:
                print(f"❌ Tarama özeti gönderilemedi: {e}")
            
            for i, f in enumerate(all_firsatlar, 1):
                risk = f['risk_analysis']
                signal_strength = f.get('signal_strength', 0)
                
                print(f"\n{i}. {f['symbol']} - {f['yön']} ({f['formasyon']})")
                print(f"   💰 Fiyat: {f['price']} | TP: {f['tp']} | SL: {f['sl']}")
                print(f"   📊 Potansiyel: %{f['tpfark']*100:.2f} | R/R: {risk['risk_reward']} ✅")
                print(f"   ⚡ Kaldıraç: {risk['leverage']} | Pozisyon: {risk['position_size']}")
                print(f"   🎯 Hedef: {risk['potential_gain']} | Risk: {risk['risk_amount']}")
                print(f"   🔒 Margin: {risk['margin_type']} | Max Kayıp: {risk['max_loss']}")
                
                # 3 TP seviyesi gösterimi
                if 'tp_levels' in f and f['tp_levels']:
                    tp_levels = f['tp_levels']
                    print(f"   🎯 3 TP SEVİYESİ:")
                    print(f"      TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"      TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"      TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                else:
                    print("   🎯 3 TP SEVİYESİ: Hesaplanamadı.")
                
                # Sinyal gücü
                if signal_strength >= 75:
                    strength_emoji = "🔥"
                    strength_text = "ÇOK GÜÇLÜ"
                elif signal_strength >= 60:
                    strength_emoji = "⚡"
                    strength_text = "GÜÇLÜ"
                elif signal_strength >= 50:
                    strength_emoji = "💪"
                    strength_text = "ORTA"
                else:
                    strength_emoji = "💤"
                    strength_text = "ZAYIF"
                
                print(f"   {strength_emoji} Sinyal Gücü: {strength_text} (%{signal_strength:.0f})")
                print(f"   ✅ FUTURES İŞLEM AÇILABİLİR!")
        else:
            print('\n❌ R/R 1:1+ fırsat bulunamadı.')
            print('🔄 R/R 0.8:1+ fırsatlar aranıyor...')
            
            # Telegram'da tarama özeti gönder
            try:
                send_scan_summary(len(symbols), 0, scan_time)
            except Exception as e:
                print(f"❌ Tarama özeti gönderilemedi: {e}")
            
            # İkinci tarama - 0.8:1 R/R için
            firsatlar_08 = []
            
            def analyze_symbol_08(symbol, interval='4h'):
                try:
                    current_price = get_current_price(symbol)
                    df = fetch_ohlcv(symbol, interval)
                    if df is None or df.empty:
                        return None
                    
                    # MA hesaplamaları
                    df['MA7'] = df['close'].rolling(window=7).mean()
                    df['MA25'] = df['close'].rolling(window=25).mean()
                    df['MA50'] = df['close'].rolling(window=50).mean()
                    df['MA99'] = df['close'].rolling(window=99).mean()
                    
                    ma_trend = None
                    if df['MA7'].iloc[-1] > df['MA25'].iloc[-1] > df['MA50'].iloc[-1] > df['MA99'].iloc[-1]:
                        ma_trend = 'Güçlü Yükseliş (Tüm kısa MA\'lar uzun MA\'ların üstünde)'
                    elif df['MA7'].iloc[-1] < df['MA25'].iloc[-1] < df['MA50'].iloc[-1] < df['MA99'].iloc[-1]:
                        ma_trend = 'Güçlü Düşüş (Tüm kısa MA\'lar uzun MA\'ların altında)'
                    else:
                        ma_trend = 'Kararsız veya yatay trend (MA\'lar karışık)'
                    
                    fibo_levels, fibo_high, fibo_low = calculate_fibonacci_levels(df)
                    
                    # Formasyon analizi
                    all_tobo = find_all_tobo(df)
                    all_obo = find_all_obo(df)
                    falling_wedge = detect_falling_wedge(df)
                    tobo = all_tobo[-1] if all_tobo else None
                    obo = all_obo[-1] if all_obo else None
                    
                    # En güçlü formasyonu belirle
                    dominant_formation = None
                    formation_scores = {}
                    
                    if tobo:
                        tobo_strength = abs(tobo['bas'] - tobo['neckline']) / tobo['neckline']
                        formation_scores['TOBO'] = tobo_strength * 100
                    
                    if obo:
                        obo_strength = abs(obo['bas'] - obo['neckline']) / obo['neckline']
                        formation_scores['OBO'] = obo_strength * 100
                    
                    if falling_wedge:
                        formation_scores['FALLING_WEDGE'] = falling_wedge['score']
                    
                    if formation_scores:
                        dominant_formation = max(formation_scores, key=formation_scores.get)
                    else:
                        return None
                    
                    # 0.8:1 R/R kontrolü
                    if dominant_formation == 'TOBO' and current_price:
                        neckline = tobo['neckline']
                        tp = fibo_levels['0.382']
                        min_sl_distance = current_price * 0.97
                        
                        if '0.786' in fibo_levels and fibo_levels['0.786'] < min_sl_distance:
                            sl = fibo_levels['0.786']
                        elif '0.618' in fibo_levels and fibo_levels['0.618'] < min_sl_distance:
                            sl = fibo_levels['0.618']
                        elif '0.5' in fibo_levels and fibo_levels['0.5'] < min_sl_distance:
                            sl = fibo_levels['0.5']
                        else:
                            sl = current_price * 0.95
                        
                        entry = current_price
                        
                        if tp > entry > sl and (tp - entry) / entry >= 0.01 and sl < entry:
                            macd_data = calculate_macd(df)
                            bb_data = calculate_bollinger_bands(df)
                            stoch_data = calculate_stochastic(df)
                            adx_data = calculate_adx(df)
                            
                            bullish_signals = 0
                            bearish_signals = 0
                            
                            if 'Yükseliş' in ma_trend:
                                bullish_signals += 1
                            elif 'Düşüş' in ma_trend:
                                bearish_signals += 1
                            
                            if macd_data and macd_data['trend'] == 'Bullish':
                                bullish_signals += 1
                            elif macd_data and macd_data['trend'] == 'Bearish':
                                bearish_signals += 1
                            
                            if adx_data and adx_data['trend_direction'] == 'Bullish':
                                bullish_signals += 1
                            elif adx_data and adx_data['trend_direction'] == 'Bearish':
                                bearish_signals += 1
                            
                            if bb_data and bb_data['signal'] == 'Oversold':
                                bullish_signals += 1
                            elif bb_data and bb_data['signal'] == 'Overbought':
                                bearish_signals += 1
                            
                            if stoch_data and stoch_data['signal'] == 'Oversold':
                                bullish_signals += 1
                            elif stoch_data and stoch_data['signal'] == 'Overbought':
                                bearish_signals += 1
                            
                            bullish_signals += 1
                            
                            total_signals = 6
                            long_percentage = (bullish_signals / total_signals) * 100
                            
                            if long_percentage >= 40:
                                tp_levels = calculate_three_tp_levels(entry, tp, sl, 'Long', fibo_levels, bb_data, 'TOBO')
                                optimized_tp, optimized_sl, optimized_rr = optimize_tp_sl(entry, tp, sl, 'Long', fibo_levels, bb_data)
                                
                                # 0.8:1 R/R kontrolü
                                if 0.8 <= optimized_rr < 1.0:
                                    risk_analysis = calculate_optimal_risk(symbol, entry, optimized_tp, optimized_sl, 'Long')
                                    
                                    firsat = {
                                        'symbol': symbol,
                                        'yön': 'Long',
                                        'formasyon': 'TOBO',
                                        'price': format_price(current_price),
                                        'tp': format_price(optimized_tp),
                                        'sl': format_price(optimized_sl),
                                        'tpfark': (optimized_tp-entry)/entry,
                                        'risk_analysis': risk_analysis,
                                        'signal_strength': long_percentage,
                                        'rr_ratio': optimized_rr,
                                        'tp_levels': tp_levels,
                                        'rr_type': '0.8:1'
                                    }
                                    return firsat
                    
                    elif dominant_formation == 'OBO' and current_price:
                        neckline = obo['neckline']
                        tp = fibo_levels['0.618']
                        min_sl_distance = current_price * 1.03
                        
                        if '0.236' in fibo_levels and fibo_levels['0.236'] > min_sl_distance:
                            sl = fibo_levels['0.236']
                        elif '0.382' in fibo_levels and fibo_levels['0.382'] > min_sl_distance:
                            sl = fibo_levels['0.382']
                        elif '0.5' in fibo_levels and fibo_levels['0.5'] > min_sl_distance:
                            sl = fibo_levels['0.5']
                        else:
                            sl = current_price * 1.05
                        
                        entry = current_price
                        
                        if tp < entry < sl and (entry - tp) / entry >= 0.01 and sl > entry:
                            macd_data = calculate_macd(df)
                            bb_data = calculate_bollinger_bands(df)
                            stoch_data = calculate_stochastic(df)
                            adx_data = calculate_adx(df)
                            
                            bullish_signals = 0
                            bearish_signals = 0
                            
                            if 'Yükseliş' in ma_trend:
                                bullish_signals += 1
                            elif 'Düşüş' in ma_trend:
                                bearish_signals += 1
                            
                            if macd_data and macd_data['trend'] == 'Bullish':
                                bullish_signals += 1
                            elif macd_data and macd_data['trend'] == 'Bearish':
                                bearish_signals += 1
                            
                            if adx_data and adx_data['trend_direction'] == 'Bullish':
                                bullish_signals += 1
                            elif adx_data and adx_data['trend_direction'] == 'Bearish':
                                bearish_signals += 1
                            
                            if bb_data and bb_data['signal'] == 'Oversold':
                                bullish_signals += 1
                            elif bb_data and bb_data['signal'] == 'Overbought':
                                bearish_signals += 1
                            
                            if stoch_data and stoch_data['signal'] == 'Oversold':
                                bullish_signals += 1
                            elif stoch_data and stoch_data['signal'] == 'Overbought':
                                bearish_signals += 1
                            
                            bearish_signals += 1
                            
                            total_signals = 6
                            short_percentage = (bearish_signals / total_signals) * 100
                            
                            if short_percentage >= 40:
                                optimized_tp, optimized_sl, optimized_rr = optimize_tp_sl(entry, tp, sl, 'Short', fibo_levels, bb_data)
                                
                                # 0.8:1 R/R kontrolü
                                if 0.8 <= optimized_rr < 1.0:
                                    risk_analysis = calculate_optimal_risk(symbol, entry, optimized_tp, optimized_sl, 'Short')
                                    
                                    firsat = {
                                        'symbol': symbol,
                                        'yön': 'Short',
                                        'formasyon': 'OBO',
                                        'price': format_price(current_price),
                                        'tp': format_price(optimized_tp),
                                        'sl': format_price(optimized_sl),
                                        'tpfark': (entry-optimized_tp)/entry,
                                        'risk_analysis': risk_analysis,
                                        'signal_strength': short_percentage,
                                        'rr_ratio': optimized_rr,
                                        'rr_type': '0.8:1'
                                    }
                                    return firsat
                    
                    return None
                except Exception as e:
                    return None
            
            # İkinci tarama
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(analyze_symbol_08, symbol, interval) for symbol in symbols]
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        firsatlar_08.append(result)
            
            # 0.8:1 fırsatları göster
            all_firsatlar_08 = sorted(firsatlar_08, key=lambda x: x['tpfark'], reverse=True)[:5]
            
            if all_firsatlar_08:
                print(f"\n⚡ R/R 0.8:1+ FIRSATLAR ({len(all_firsatlar_08)} adet)")
                print(f"="*80)
                
                # Telegram'da 0.8:1 fırsat bildirimleri gönder
                for i, f in enumerate(all_firsatlar_08, 1):
                    try:
                        # 0.8:1 fırsatlar için özel mesaj
                        f['rr_type'] = '0.8:1'  # R/R tipini ekle
                        send_opportunity_notification(f, i)
                    except Exception as e:
                        print(f"❌ 0.8:1 fırsat bildirimi gönderilemedi: {e}")
                
                for i, f in enumerate(all_firsatlar_08, 1):
                    risk = f['risk_analysis']
                    signal_strength = f.get('signal_strength', 0)
                    
                    print(f"\n{i}. {f['symbol']} - {f['yön']} ({f['formasyon']}) - R/R: {f['rr_ratio']:.1f}:1")
                    print(f"   💰 Fiyat: {f['price']} | TP: {f['tp']} | SL: {f['sl']}")
                    print(f"   📊 Potansiyel: %{f['tpfark']*100:.2f} | R/R: {risk['risk_reward']} ⚡")
                    print(f"   ⚡ Kaldıraç: {risk['leverage']} | Pozisyon: {risk['position_size']}")
                    print(f"   🎯 Hedef: {risk['potential_gain']} | Risk: {risk['risk_amount']}")
                    print(f"   🔒 Margin: {risk['margin_type']} | Max Kayıp: {risk['max_loss']}")
                    
                    if 'tp_levels' in f:
                        tp_levels = f['tp_levels']
                        print(f"   🎯 3 TP SEVİYESİ:")
                        print(f"      TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                        print(f"      TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                        print(f"      TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                    
                    if signal_strength >= 75:
                        strength_emoji = "🔥"
                        strength_text = "ÇOK GÜÇLÜ"
                    elif signal_strength >= 60:
                        strength_emoji = "⚡"
                        strength_text = "GÜÇLÜ"
                    else:
                        strength_emoji = "💤"
                        strength_text = "ORTA"
                    
                    print(f"   {strength_emoji} Sinyal Gücü: {strength_text} (%{signal_strength:.0f})")
                    print(f"   ⚡ DÜŞÜK R/R - DİKKATLİ İŞLEM!")
                
                # Telegram'da 0.8:1 tarama özeti gönder
                try:
                    send_scan_summary(len(symbols), len(all_firsatlar_08), scan_time)
                except Exception as e:
                    print(f"❌ 0.8:1 tarama özeti gönderilemedi: {e}")
            else:
                print('\n❌ R/R 0.8:1+ fırsat da bulunamadı.')
                print('💡 Sebepler:')
                print('   - R/R oranı 0.8:1\'den düşük olan sinyaller')
                print('   - Yeterli teknik sinyal gücü olmayan coinler')
                print('   - Formasyon tamamlanmamış coinler')
                print('⏰ 3 saat sonra tekrar taranacak...')
                
                # Telegram'da tarama özeti gönder
                try:
                    send_scan_summary(len(symbols), 0, scan_time)
                except Exception as e:
                    print(f"❌ Tarama özeti gönderilemedi: {e}")
        
        # Tarama tarih ve saati
        from datetime import datetime
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        print(f"\n📅 Tarama Tarihi: {current_time}")
        
        print("\n⏰ ESC'ye basarak çıkın veya 3 saat bekleyin...")
        start_time = time.time()
        timeout = 10800  # 3 saat = 10800 saniye
        
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\x1b':  # ESC
                    print('👋 Çıkılıyor...')
                    return
            time.sleep(0.1)  # Daha hızlı tepki için
            
            # 3 saat kontrolü
            elapsed_time = time.time() - start_time
            if elapsed_time >= timeout:
                print("\n🔄 3 saat doldu, otomatik tarama yapılıyor...")
                break

def find_rectangle(df, min_touches=4, min_height_ratio=0.02, max_height_ratio=0.15):
    """
    Rectangle (Kutu Kanal) formasyonu tespit eder
    """
    try:
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        # En son 50 mumda formasyon ara
        lookback = min(50, len(df))
        
        # Tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, lookback-2):
            # Tepe noktası
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            # Dip noktası
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # En son tepe ve dip noktalarını al
        recent_peaks = peaks[-3:] if len(peaks) >= 3 else peaks
        recent_troughs = troughs[-3:] if len(troughs) >= 3 else troughs
        
        # Direnç ve destek seviyelerini hesapla
        resistance_level = np.mean([p[1] for p in recent_peaks])
        support_level = np.mean([t[1] for t in recent_troughs])
        
        # Yükseklik kontrolü
        height = resistance_level - support_level
        height_ratio = height / support_level
        
        if height_ratio < min_height_ratio or height_ratio > max_height_ratio:
            return None
        
        # Direnç ve destek toleransı
        resistance_tolerance = height * 0.05
        support_tolerance = height * 0.05
        
        # Tepe ve dip noktalarının direnç/destek seviyelerine yakınlığını kontrol et
        resistance_touches = sum(1 for p in recent_peaks if abs(p[1] - resistance_level) <= resistance_tolerance)
        support_touches = sum(1 for t in recent_troughs if abs(t[1] - support_level) <= support_tolerance)
        
        if resistance_touches < 2 or support_touches < 2:
            return None
        
        # Mevcut fiyat pozisyonu
        current_price = closes[-1]
        breakout_threshold = height * 0.02  # %2 kırılım eşiği
        
        # Kırılım durumu
        breakout_up = current_price > resistance_level + breakout_threshold
        breakout_down = current_price < support_level - breakout_threshold
        in_range = support_level - breakout_threshold <= current_price <= resistance_level + breakout_threshold
        
        # Formasyon skoru
        score = min(100, (resistance_touches + support_touches) * 15)
        
        return {
            'type': 'RECTANGLE',
            'resistance': resistance_level,
            'support': support_level,
            'height': height,
            'resistance_touches': resistance_touches,
            'support_touches': support_touches,
            'breakout_up': breakout_up,
            'breakout_down': breakout_down,
            'in_range': in_range,
            'score': score,
            'current_price': current_price
        }
    except Exception as e:
        return None

def find_ascending_triangle(df, min_touches=3, min_height_ratio=0.02, max_height_ratio=0.20):
    """
    Ascending Triangle (Yükselen Üçgen) formasyonu tespit eder
    """
    try:
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        lookback = min(60, len(df))
        
        # Tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, lookback-2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # En son noktaları al
        recent_peaks = peaks[-3:] if len(peaks) >= 3 else peaks
        recent_troughs = troughs[-3:] if len(troughs) >= 3 else troughs
        
        # Yatay direnç çizgisi
        resistance_level = np.mean([p[1] for p in recent_peaks])
        resistance_tolerance = resistance_level * 0.02
        
        # Yükselen destek çizgisi (linear regression)
        if len(recent_troughs) >= 2:
            x = np.array([t[0] for t in recent_troughs])
            y = np.array([t[1] for t in recent_troughs])
            
            # Linear regression
            slope, intercept = np.polyfit(x, y, 1)
            
            # Pozitif eğim kontrolü (yükselen destek)
            if slope <= 0:
                return None
            
            # Destek çizgisinin güncel değeri
            current_support = slope * (len(df) - 1) + intercept
            
            # Yükseklik kontrolü
            height = resistance_level - current_support
            height_ratio = height / current_support
            
            if height_ratio < min_height_ratio or height_ratio > max_height_ratio:
                return None
            
            # Direnç dokunuşları
            resistance_touches = sum(1 for p in recent_peaks if abs(p[1] - resistance_level) <= resistance_tolerance)
            
            # Destek dokunuşları (eğimli çizgiye yakınlık)
            support_touches = 0
            for t in recent_troughs:
                expected_support = slope * t[0] + intercept
                if abs(t[1] - expected_support) <= resistance_tolerance:
                    support_touches += 1
            
            if resistance_touches < 2 or support_touches < 2:
                return None
            
            # Kırılım kontrolü
            current_price = closes[-1]
            breakout_threshold = height * 0.02
            
            breakout_up = current_price > resistance_level + breakout_threshold
            breakout_down = current_price < current_support - breakout_threshold
            
            # Formasyon skoru
            score = min(100, (resistance_touches + support_touches) * 15)
            
            return {
                'type': 'ASCENDING_TRIANGLE',
                'resistance': resistance_level,
                'support_slope': slope,
                'support_intercept': intercept,
                'current_support': current_support,
                'height': height,
                'resistance_touches': resistance_touches,
                'support_touches': support_touches,
                'breakout_up': breakout_up,
                'breakout_down': breakout_down,
                'score': score,
                'current_price': current_price
            }
    except Exception as e:
        return None

def find_descending_triangle(df, min_touches=3, min_height_ratio=0.02, max_height_ratio=0.20):
    """
    Descending Triangle (Alçalan Üçgen) formasyonu tespit eder
    """
    try:
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        lookback = min(60, len(df))
        
        # Tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, lookback-2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # En son noktaları al
        recent_peaks = peaks[-3:] if len(peaks) >= 3 else peaks
        recent_troughs = troughs[-3:] if len(troughs) >= 3 else troughs
        
        # Yatay destek çizgisi
        support_level = np.mean([t[1] for t in recent_troughs])
        support_tolerance = support_level * 0.02
        
        # Alçalan direnç çizgisi (linear regression)
        if len(recent_peaks) >= 2:
            x = np.array([p[0] for p in recent_peaks])
            y = np.array([p[1] for p in recent_peaks])
            
            # Linear regression
            slope, intercept = np.polyfit(x, y, 1)
            
            # Negatif eğim kontrolü (alçalan direnç)
            if slope >= 0:
                return None
            
            # Direnç çizgisinin güncel değeri
            current_resistance = slope * (len(df) - 1) + intercept
            
            # Yükseklik kontrolü
            height = current_resistance - support_level
            height_ratio = height / support_level
            
            if height_ratio < min_height_ratio or height_ratio > max_height_ratio:
                return None
            
            # Destek dokunuşları
            support_touches = sum(1 for t in recent_troughs if abs(t[1] - support_level) <= support_tolerance)
            
            # Direnç dokunuşları (eğimli çizgiye yakınlık)
            resistance_touches = 0
            for p in recent_peaks:
                expected_resistance = slope * p[0] + intercept
                if abs(p[1] - expected_resistance) <= support_tolerance:
                    resistance_touches += 1
            
            if resistance_touches < 2 or support_touches < 2:
                return None
            
            # Kırılım kontrolü
            current_price = closes[-1]
            breakout_threshold = height * 0.02
            
            breakout_up = current_price > current_resistance + breakout_threshold
            breakout_down = current_price < support_level - breakout_threshold
            
            # Formasyon skoru
            score = min(100, (resistance_touches + support_touches) * 15)
            
            return {
                'type': 'DESCENDING_TRIANGLE',
                'support': support_level,
                'resistance_slope': slope,
                'resistance_intercept': intercept,
                'current_resistance': current_resistance,
                'height': height,
                'resistance_touches': resistance_touches,
                'support_touches': support_touches,
                'breakout_up': breakout_up,
                'breakout_down': breakout_down,
                'score': score,
                'current_price': current_price
            }
    except Exception as e:
        return None

def find_symmetrical_triangle(df, min_touches=3, min_height_ratio=0.02, max_height_ratio=0.20):
    """
    Symmetrical Triangle (Simetrik Üçgen) formasyonu tespit eder
    """
    try:
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        lookback = min(60, len(df))
        
        # Tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, lookback-2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # En son noktaları al
        recent_peaks = peaks[-3:] if len(peaks) >= 3 else peaks
        recent_troughs = troughs[-3:] if len(troughs) >= 3 else troughs
        
        # Direnç çizgisi (linear regression)
        if len(recent_peaks) >= 2:
            x_resistance = np.array([p[0] for p in recent_peaks])
            y_resistance = np.array([p[1] for p in recent_peaks])
            slope_resistance, intercept_resistance = np.polyfit(x_resistance, y_resistance, 1)
            
            # Destek çizgisi (linear regression)
            if len(recent_troughs) >= 2:
                x_support = np.array([t[0] for t in recent_troughs])
                y_support = np.array([t[1] for t in recent_troughs])
                slope_support, intercept_support = np.polyfit(x_support, y_support, 1)
                
                # Eğimlerin zıt yönlü olması kontrolü
                if slope_resistance >= 0 or slope_support <= 0:
                    return None
                
                # Çizgilerin yakınsaması kontrolü
                convergence_ratio = abs(slope_resistance - slope_support) / abs(slope_resistance)
                if convergence_ratio < 0.3:  # Çok yavaş yakınsama
                    return None
                
                # Güncel değerler
                current_resistance = slope_resistance * (len(df) - 1) + intercept_resistance
                current_support = slope_support * (len(df) - 1) + intercept_support
                
                # Yükseklik kontrolü
                height = current_resistance - current_support
                height_ratio = height / current_support
                
                if height_ratio < min_height_ratio or height_ratio > max_height_ratio:
                    return None
                
                # Dokunuş sayıları
                tolerance = height * 0.05
                
                resistance_touches = 0
                for p in recent_peaks:
                    expected_resistance = slope_resistance * p[0] + intercept_resistance
                    if abs(p[1] - expected_resistance) <= tolerance:
                        resistance_touches += 1
                
                support_touches = 0
                for t in recent_troughs:
                    expected_support = slope_support * t[0] + intercept_support
                    if abs(t[1] - expected_support) <= tolerance:
                        support_touches += 1
                
                if resistance_touches < 2 or support_touches < 2:
                    return None
                
                # Kırılım kontrolü
                current_price = closes[-1]
                breakout_threshold = height * 0.02
                
                breakout_up = current_price > current_resistance + breakout_threshold
                breakout_down = current_price < current_support - breakout_threshold
                
                # Formasyon skoru
                score = min(100, (resistance_touches + support_touches) * 15)
                
                return {
                    'type': 'SYMMETRICAL_TRIANGLE',
                    'resistance_slope': slope_resistance,
                    'resistance_intercept': intercept_resistance,
                    'support_slope': slope_support,
                    'support_intercept': intercept_support,
                    'current_resistance': current_resistance,
                    'current_support': current_support,
                    'height': height,
                    'resistance_touches': resistance_touches,
                    'support_touches': support_touches,
                    'breakout_up': breakout_up,
                    'breakout_down': breakout_down,
                    'score': score,
                    'current_price': current_price
                }
    except Exception as e:
        return None

def find_broadening_formation(df, min_touches=3, min_height_ratio=0.02, max_height_ratio=0.25):
    """
    Broadening Formation (Genleşen Üçgen / Megafoon) formasyonu tespit eder
    """
    try:
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        lookback = min(60, len(df))
        
        # Tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, lookback-2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # En son noktaları al
        recent_peaks = peaks[-3:] if len(peaks) >= 3 else peaks
        recent_troughs = troughs[-3:] if len(troughs) >= 3 else troughs
        
        # Direnç çizgisi (linear regression)
        if len(recent_peaks) >= 2:
            x_resistance = np.array([p[0] for p in recent_peaks])
            y_resistance = np.array([p[1] for p in recent_peaks])
            slope_resistance, intercept_resistance = np.polyfit(x_resistance, y_resistance, 1)
            
            # Destek çizgisi (linear regression)
            if len(recent_troughs) >= 2:
                x_support = np.array([t[0] for t in recent_troughs])
                y_support = np.array([t[1] for t in recent_troughs])
                slope_support, intercept_support = np.polyfit(x_support, y_support, 1)
                
                # Eğimlerin aynı yönlü olması kontrolü (genleşme)
                if slope_resistance <= 0 or slope_support >= 0:
                    return None
                
                # Çizgilerin ıraksaması kontrolü
                divergence_ratio = abs(slope_resistance + slope_support) / abs(slope_resistance)
                if divergence_ratio < 0.3:  # Çok yavaş ıraksama
                    return None
                
                # Güncel değerler
                current_resistance = slope_resistance * (len(df) - 1) + intercept_resistance
                current_support = slope_support * (len(df) - 1) + intercept_support
                
                # Yükseklik kontrolü
                height = current_resistance - current_support
                height_ratio = height / current_support
                
                if height_ratio < min_height_ratio or height_ratio > max_height_ratio:
                    return None
                
                # Dokunuş sayıları
                tolerance = height * 0.05
                
                resistance_touches = 0
                for p in recent_peaks:
                    expected_resistance = slope_resistance * p[0] + intercept_resistance
                    if abs(p[1] - expected_resistance) <= tolerance:
                        resistance_touches += 1
                
                support_touches = 0
                for t in recent_troughs:
                    expected_support = slope_support * t[0] + intercept_support
                    if abs(t[1] - expected_support) <= tolerance:
                        support_touches += 1
                
                if resistance_touches < 2 or support_touches < 2:
                    return None
                
                # Kırılım kontrolü
                current_price = closes[-1]
                breakout_threshold = height * 0.02
                
                breakout_up = current_price > current_resistance + breakout_threshold
                breakout_down = current_price < current_support - breakout_threshold
                
                # Formasyon skoru
                score = min(100, (resistance_touches + support_touches) * 15)
                
                return {
                    'type': 'BROADENING_FORMATION',
                    'resistance_slope': slope_resistance,
                    'resistance_intercept': intercept_resistance,
                    'support_slope': slope_support,
                    'support_intercept': intercept_support,
                    'current_resistance': current_resistance,
                    'current_support': current_support,
                    'height': height,
                    'resistance_touches': resistance_touches,
                    'support_touches': support_touches,
                    'breakout_up': breakout_up,
                    'breakout_down': breakout_down,
                    'score': score,
                    'current_price': current_price
                }
    except Exception as e:
        return None

def format_price(price):
    if price == 0:
        return '0'
    elif price < 0.0001:
        return f"{price:.8f}"
    elif price < 1:
        return f"{price:.6f}"
    elif price < 10:
        return f"{price:.4f}"
    elif price < 100:
        return f"{price:.3f}"
    else:
        return f"{price:.2f}"

def send_opportunity_notification(firsat, index):
    """
    Fırsat bulunduğunda Telegram'da bildirim gönderir
    """
    try:
        risk = firsat['risk_analysis']
        signal_strength = firsat.get('signal_strength', 0)
        
        # Sinyal gücü emoji ve metni
        if signal_strength >= 75:
            strength_emoji = "🔥"
            strength_text = "ÇOK GÜÇLÜ"
        elif signal_strength >= 60:
            strength_emoji = "⚡"
            strength_text = "GÜÇLÜ"
        elif signal_strength >= 50:
            strength_emoji = "💪"
            strength_text = "ORTA"
        else:
            strength_emoji = "💤"
            strength_text = "ZAYIF"
        
        # Ana mesaj
        message = f"""
🚨 **FUTURES TRADING FIRSATI #{index}**

📈 **{firsat['symbol']}** - {firsat['yön']} ({firsat['formasyon']})

💰 **Fiyat:** {firsat['price']}
🎯 **TP:** {firsat['tp']}
🛑 **SL:** {firsat['sl']}

📊 **Potansiyel:** %{firsat['tpfark']*100:.2f}
⚖️ **R/R:** {risk['risk_reward']} ✅
⚡ **Kaldıraç:** {risk['leverage']}
📦 **Pozisyon:** {risk['position_size']}
🎯 **Hedef:** {risk['potential_gain']}
⚠️ **Risk:** {risk['risk_amount']}
🔒 **Margin:** {risk['margin_type']}
💸 **Max Kayıp:** {risk['max_loss']}

{strength_emoji} **Sinyal Gücü:** {strength_text} (%{signal_strength:.0f})

✅ **FUTURES İŞLEM AÇILABİLİR!**
"""
        
        # 3 TP seviyesi varsa ekle
        if 'tp_levels' in firsat and firsat['tp_levels']:
            tp_levels = firsat['tp_levels']
            message += f"""
🎯 **3 TP SEVİYESİ:**
• TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}
• TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}
• TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}
"""
        
        # Tarih ve saat ekle
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        message += f"\n📅 **Tarih:** {current_time}"
        
        # Telegram'a gönder
        send_telegram_message(message)
        print(f"📱 Telegram bildirimi gönderildi: {firsat['symbol']}")
        
    except Exception as e:
        print(f"❌ Telegram bildirimi gönderilemedi: {e}")

def send_scan_summary(total_symbols, found_opportunities, scan_time):
    """
    Tarama özetini Telegram'da gönderir
    """
    try:
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        
        message = f"""
📊 **TARAMA ÖZETİ**

🔍 **Taranan Coin:** {total_symbols}
🎯 **Bulunan Fırsat:** {found_opportunities}
⏱️ **Tarama Süresi:** {scan_time:.1f} saniye
📅 **Tarih:** {current_time}

"""
        
        if found_opportunities == 0:
            message += "❌ **R/R 1:1+ fırsat bulunamadı.**\n"
            message += "🔄 **3 saat sonra tekrar taranacak...**"
        else:
            message += f"✅ **{found_opportunities} fırsat bulundu!**\n"
            message += "📱 **Detaylı bildirimler gönderildi.**"
        
        send_telegram_message(message)
        print(f"📱 Tarama özeti Telegram'da gönderildi")
        
    except Exception as e:
        print(f"❌ Tarama özeti gönderilemedi: {e}")

def send_startup_notification(license_info=None):
    """
    Bot başladığında Telegram'da bildirim gönderir
    """
    try:
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        
        message = f"""
🤖 **BOT BAŞLATILDI**

📊 **Bot her fırsat için en uygun risk seviyesini otomatik önerecek**
💰 **Risk seviyesi:** Kaldıraç, pozisyon büyüklüğü ve potansiyel kazanç
🎯 **R/R Filtresi:** Sadece 1:1'den yüksek risk/ödül oranına sahip sinyaller
📱 **Telegram Bildirimleri:** Aktif

"""
        
        # Lisans bilgilerini ekle
        if license_info:
            message += f"""
🔑 **LİSANS BİLGİLERİ:**
📦 **Paket:** {license_info['type'].upper()}
💰 **Fiyat:** ${license_info['price']}
📅 **Aktifleştirme:** {license_info['activated_date'][:10]}
"""
            
            if license_info['expiry_date']:
                message += f"⏰ **Bitiş:** {license_info['expiry_date'][:10]}\n"
            else:
                message += "⏰ **Bitiş:** Sınırsız\n"
        
        message += f"""
📅 **Başlangıç:** {current_time}
⏰ **Tarama Sıklığı:** Her 10 dakika
🔄 **ESC'ye basarak çıkabilirsiniz**

**Bot çalışmaya başladı! 🚀**
"""
        
        send_telegram_message(message)
        print("📱 Bot başlangıç bildirimi Telegram'da gönderildi")
        
    except Exception as e:
        print(f"❌ Başlangıç bildirimi gönderilemedi: {e}")

def send_error_notification(error_message):
    """
    Hata durumunda Telegram'da bildirim gönderir
    """
    try:
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        
        message = f"""
⚠️ **BOT HATASI**

❌ **Hata:** {error_message}
📅 **Tarih:** {current_time}

🔄 **Bot yeniden başlatılacak...**
"""
        
        send_telegram_message(message)
        print(f"📱 Hata bildirimi Telegram'da gönderildi")
        
    except Exception as e:
        print(f"❌ Hata bildirimi gönderilemedi: {e}")

def get_scan_results():
    """Tarama sonuçlarını döndür (Telegram bot için)"""
    try:
        # Lisans yöneticisini başlat
        license_manager = LicenseManager()
        
        # Lisans kontrolü - Telegram bot için her zaman True döndür
        # Çünkü Telegram bot kendi lisans kontrolünü yapıyor
        pass
        
        # Tarama yap
        scan_start_time = time.time()
        symbols = get_usdt_symbols()
        firsatlar = []
        
        # Tüm coinleri gerçekten analiz et - 80-90 saniye sürecek
        print(f"🔍 {len(symbols)} coin analiz ediliyor... (80-90 saniye sürecek)")
        
        # analyze_symbol fonksiyonunu main() fonksiyonundan al
        def analyze_symbol(symbol, interval='4h'):
            try:
                current_price = get_current_price(symbol)
                if not current_price:
                    return None
                
                df = fetch_ohlcv(symbol, interval)
                if df is None or df.empty or len(df) < 100:
                    return None
                
                # MA hesaplamaları
                df['MA7'] = df['close'].rolling(window=7).mean()
                df['MA25'] = df['close'].rolling(window=25).mean()
                df['MA50'] = df['close'].rolling(window=50).mean()
                df['MA99'] = df['close'].rolling(window=99).mean()
                
                ma_trend = None
                if df['MA7'].iloc[-1] > df['MA25'].iloc[-1] > df['MA50'].iloc[-1] > df['MA99'].iloc[-1]:
                    ma_trend = 'Güçlü Yükseliş'
                elif df['MA7'].iloc[-1] < df['MA25'].iloc[-1] < df['MA50'].iloc[-1] < df['MA99'].iloc[-1]:
                    ma_trend = 'Güçlü Düşüş'
                else:
                    ma_trend = 'Kararsız'
                
                fibo_levels, fibo_high, fibo_low = calculate_fibonacci_levels(df)
                
                # Tüm formasyonları analiz et
                all_tobo = find_all_tobo(df)
                all_obo = find_all_obo(df)
                falling_wedge = detect_falling_wedge(df)
                
                # En güçlü formasyonu belirle
                formations = []
                
                if all_tobo:
                    tobo = all_tobo[-1]
                    entry = current_price
                    tp = fibo_levels.get('0.382', current_price * 1.05)
                    sl = tobo['neckline']
                    
                    # TP/SL optimizasyonu
                    optimized_tp, optimized_sl, optimized_rr = optimize_tp_sl(entry, tp, sl, 'Long', fibo_levels, None)
                    
                    # R/R oranı kontrolü - Daha esnek kriterler
                    if optimized_rr >= 0.5:  # 0.5:1'den yüksek olanları kabul et
                        risk_analysis = calculate_optimal_risk(symbol, entry, optimized_tp, optimized_sl, 'Long')
                        
                        formations.append({
                            'type': 'TOBO',
                            'data': tobo,
                            'direction': 'Long',
                            'tp': optimized_tp,
                            'sl': optimized_sl,
                            'rr_ratio': optimized_rr,
                            'risk_analysis': risk_analysis
                        })
                
                if all_obo:
                    obo = all_obo[-1]
                    entry = current_price
                    tp = fibo_levels.get('0.618', current_price * 0.95)
                    sl = obo['neckline']
                    
                    # TP/SL optimizasyonu
                    optimized_tp, optimized_sl, optimized_rr = optimize_tp_sl(entry, tp, sl, 'Short', fibo_levels, None)
                    
                    # R/R oranı kontrolü
                    if optimized_rr >= 0.5:
                        risk_analysis = calculate_optimal_risk(symbol, entry, optimized_tp, optimized_sl, 'Short')
                        
                        formations.append({
                            'type': 'OBO',
                            'data': obo,
                            'direction': 'Short',
                            'tp': optimized_tp,
                            'sl': optimized_sl,
                            'rr_ratio': optimized_rr,
                            'risk_analysis': risk_analysis
                        })
                
                if falling_wedge:
                    entry = current_price
                    tp = falling_wedge.get('tp', current_price * 1.05)
                    sl = falling_wedge.get('sl', current_price * 0.95)
                    
                    # TP/SL optimizasyonu
                    optimized_tp, optimized_sl, optimized_rr = optimize_tp_sl(entry, tp, sl, 'Long', fibo_levels, None)
                    
                    # R/R oranı kontrolü
                    if optimized_rr >= 0.5:
                        risk_analysis = calculate_optimal_risk(symbol, entry, optimized_tp, optimized_sl, 'Long')
                        
                        formations.append({
                            'type': 'Falling Wedge',
                            'data': falling_wedge,
                            'direction': 'Long',
                            'tp': optimized_tp,
                            'sl': optimized_sl,
                            'rr_ratio': optimized_rr,
                            'risk_analysis': risk_analysis
                        })
                
                # En iyi formasyonu seç
                if not formations:
                    return None
                
                # R/R oranına göre sırala
                best_formation = max(formations, key=lambda x: x['rr_ratio'])
                
                # Sinyal gücü hesapla
                signal_strength = 70  # Varsayılan
                if 'Güçlü Yükseliş' in ma_trend and best_formation['direction'] == 'Long':
                    signal_strength += 10
                
                return {
                    'symbol': symbol,
                    'yön': best_formation['direction'],
                    'formasyon': best_formation['type'],
                    'price': current_price,
                    'tp': best_formation['tp'],
                    'sl': best_formation['sl'],
                    'tpfark': abs(best_formation['tp'] - current_price) / current_price,
                    'risk_analysis': best_formation['risk_analysis'],
                    'signal_strength': min(95, signal_strength),
                    'rr_ratio': best_formation['rr_ratio']
                }
                
            except Exception as e:
                print(f"Hata {symbol}: {e}")
                return None
        
        # Sıralı analiz - daha sağlıklı ve gerçekçi
        print("🔍 Sıralı analiz başlatılıyor... (80-90 saniye sürecek)")
        
        completed = 0
        for symbol in symbols:
            try:
                result = analyze_symbol(symbol, '4h')
                completed += 1
                
                # İlerleme göster
                if completed % 20 == 0:
                    progress = (completed / len(symbols)) * 100
                    print(f"📊 İlerleme: %{progress:.1f} ({completed}/{len(symbols)})")
                
                if result:
                    firsatlar.append(result)
                    print(f"✅ {symbol}: {result['formasyon']} - R/R: {result['rr_ratio']:.2f}")
                
                # Her 10 coin'de bir kısa bekleme (API limitlerini aşmamak için)
                if completed % 10 == 0:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"❌ {symbol} analiz hatası: {e}")
                completed += 1
                continue
        
        # En iyi 10 fırsatı sırala
        all_firsatlar = sorted(firsatlar, key=lambda x: x['tpfark'], reverse=True)[:10]
        
        # Tarama süresini hesapla
        scan_time = time.time() - scan_start_time
        
        return {
            'total_scanned': len(symbols),
            'opportunities': all_firsatlar,
            'scan_time': scan_time
        }
    except Exception as e:
        print(f"Tarama hatası: {e}")
        return None

if __name__ == "__main__":
    main()